# model_runner.py (replace existing)
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import json
import re
from datetime import datetime

MODEL_NAME = "google/flan-t5-small"
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_tokenizer = None
_model = None

def load_model():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(_device)
    return _tokenizer, _model

# --- Deterministic (fast) heuristics first ---
_YEAR_RE = re.compile(r'\b([1-9][0-9]?)\s*(?:st|nd|rd|th)?\s*(?:year|yr)\b', re.IGNORECASE)
_SEM_RE = re.compile(r'\b(?:sem(?:ester)?\s*(?:no\.)?:?\s*)?([1-9][0-9]?)\b', re.IGNORECASE)
# common subject tokens, simple heuristic; you can expand this list
_COMMON_SUBJECTS = [
    "data structures", "operating systems", "mathematics", "physics",
    "computer networks", "database", "algorithms", "discrete math"
]

def heuristic_extract(text: str):
    text_l = text.lower()
    year = None
    sem = None
    subject = None

    y = _YEAR_RE.search(text_l)
    if y:
        try:
            year = int(y.group(1))
        except:
            year = None

    # semester extraction heuristic: search for 'sem' or numeric after subject keywords
    s = re.search(r'\bsem(?:ester)?\s*([1-9][0-9]?)\b', text_l, re.IGNORECASE)
    if s:
        try:
            sem = int(s.group(1))
        except:
            sem = None
    else:
        # try to infer sem from words like '7th sem'
        m = re.search(r'\b([1-9][0-9]?)\s*(?:th|st|nd|rd)\s*sem\b', text_l)
        if m:
            sem = int(m.group(1))

    for subj in _COMMON_SUBJECTS:
        if subj in text_l:
            subject = subj.title()
            break

    # fallback: look for capitalized 2-word sequence as potential subject
    if not subject:
        caps = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
        if caps:
            subject = caps[0]

    # keywords: simple tokenization of nouns / important words
    keywords = []
    # pick numbers and words that look like subject tokens
    keywords.extend(re.findall(r'\b\w{3,}\b', text_l))
    # dedupe and keep short list
    keywords = list(dict.fromkeys(keywords))[:8]

    return {
        "intent": None,
        "confidence": 0.0,
        "keywords": keywords,
        "entities": {"year": year, "semester": sem, "subject": subject, "student_id": None}
    }

# --- Model parsing & robust extraction helpers ---
def _extract_json_between_markers(text, start_marker="### BEGIN JSON", end_marker="### END JSON"):
    # prefer markers if present
    si = text.find(start_marker)
    ei = text.find(end_marker)
    if si != -1 and ei != -1 and ei > si:
        return text[si+len(start_marker):ei].strip()
    # fallback to first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return None

def _attempt_parse_json(text):
    try:
        jtext = _extract_json_between_markers(text)
        if jtext:
            return json.loads(jtext)
    except Exception:
        pass
    return None

def _sanitize_model_output(decoded):
    # log raw decoded output to console for debugging
    print("=== MODEL RAW OUTPUT ===")
    print(decoded)
    print("=== END MODEL RAW OUTPUT ===")

    parsed = _attempt_parse_json(decoded)
    if parsed is not None:
        return parsed

    # try line-key: value fallback parsing
    data = {}
    lines = [l.strip() for l in decoded.splitlines() if l.strip()]
    for line in lines:
        if ":" in line:
            k, v = line.split(":", 1)
            key = k.strip().lower()
            val = v.strip()
            if key == "keywords":
                items = re.split(r"[,\;]+", val)
                data["keywords"] = [it.strip() for it in items if it.strip()]
            elif key == "entities":
                try:
                    data["entities"] = json.loads(val)
                except:
                    data["entities"] = {}
            elif key == "confidence":
                try:
                    data["confidence"] = float(val)
                except:
                    data["confidence"] = 0.0
            else:
                data[key] = val
    if data:
        return data

    # final fallback: return raw text as explanation
    return {"explanation": decoded.strip()}

def call_model_for_json(user_text: str):
    tokenizer, model = load_model()

    prompt = (
        "You are an assistant that extracts an intent label, confidence (0-1), keywords, and entities "
        "from a user's message. **Return ONLY valid JSON**. Surround the JSON with EXACT markers:\n\n"
        "### BEGIN JSON\n"
        "{\n"
        '  "intent": "intent_name",\n'
        '  "confidence": 0.0,\n'
        '  "keywords": ["k1","k2"],\n'
        '  "entities": {"year": null, "semester": null, "subject": null, "student_id": null},\n'
        '  "explanation": "short explanation",\n'
        '  "query_descriptor": { "type": "table_lookup", "table": "marks", "filters": {"year": null}, "limit": 100 },\n'
        '  "next_action": "call_table_agent"\n'
        "}\n"
        "### END JSON\n\n"
        "User message:\n"
        f"\"{user_text}\"\n\nReturn the JSON only between the markers."
    )

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(_device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=180,
        num_beams=4,
        do_sample=False,
        early_stopping=True
    )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    parsed = _sanitize_model_output(decoded)
    return parsed

def extract_intent_payload(user_text: str) -> dict:
    # 1) Try fast heuristic extraction first
    heur = heuristic_extract(user_text)
    # if heuristics found a likely year or subject, set an initial payload
    if heur["entities"]["year"] or heur["entities"]["subject"] or heur["entities"]["semester"]:
        payload = {
            "intent": "result",  # heuristically assume result for queries like this dataset
            "confidence": 0.8,
            "keywords": heur["keywords"],
            "entities": heur["entities"],
            "explanation": "Heuristic extraction (regex + lookup).",
            "query_descriptor": {
                "type": "table_lookup",
                "table": "marks",
                "filters": {k: v for k, v in heur["entities"].items() if v is not None},
                "limit": 200
            },
            "next_action": "call_table_agent"
        }
        payload["timestamp"] = datetime.utcnow().isoformat() + "Z"
        return payload

    # 2) If heuristics didn't find anything reliable, call the model
    parsed = call_model_for_json(user_text)

    # parsed may be dict-like or fallback; normalize into final payload
    payload = {}
    if isinstance(parsed, dict) and parsed.get("intent"):
        payload["intent"] = parsed.get("intent") or "unknown"
        try:
            payload["confidence"] = float(parsed.get("confidence", 0.0))
        except:
            payload["confidence"] = 0.0
        payload["keywords"] = parsed.get("keywords") if isinstance(parsed.get("keywords"), list) else parsed.get("keywords", []) or []
        payload["entities"] = parsed.get("entities") if isinstance(parsed.get("entities"), dict) else parsed.get("entities", {}) or {}
        payload["explanation"] = parsed.get("explanation") or ""
        payload["query_descriptor"] = parsed.get("query_descriptor") or {"type":"table_lookup","table":"marks","filters":{},"limit":100}
        payload["next_action"] = parsed.get("next_action") or "ask_clarification"
    else:
        # robust fallback
        payload = {
            "intent": "unknown",
            "confidence": 0.0,
            "keywords": [],
            "entities": {},
            "explanation": parsed.get("explanation") if isinstance(parsed, dict) else str(parsed),
            "query_descriptor": {"type":"table_lookup","table":"marks","filters":{},"limit":100},
            "next_action": "ask_clarification"
        }

    payload["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return payload
