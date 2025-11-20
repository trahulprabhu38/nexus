# backend/agent.py
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    import openai
    _HAS_OPENAI = True
except Exception:
    openai = None
    _HAS_OPENAI = False

try:
    from transformers import pipeline
    _HAS_TRANSFORMERS = True
except Exception:
    pipeline = None
    _HAS_TRANSFORMERS = False

from database import save_turn
from utils import sanitize_text

class AIMLAgent:
    """
    Modular agent:
      - If OPENAI_API_KEY is present and openai installed -> uses OpenAI ChatCompletion.
      - Else if transformers installed -> uses local HF text-generation pipeline.
      - Else -> fallback deterministic replies.
    """

    def __init__(self, hf_model: str = "gpt2"):
        self.openai_key = os.getenv("OPENAI_API_KEY") or None
        self.hf_model = os.getenv("HF_MODEL", hf_model)
        self.backend = "fallback"
        self.generator = None

        if self.openai_key and _HAS_OPENAI:
            try:
                openai.api_key = self.openai_key
                self.backend = "openai"
                logger.info("AIMLAgent: Using OpenAI backend.")
            except Exception as e:
                logger.exception("Failed to configure OpenAI: %s", e)
                self.backend = "fallback"
        elif _HAS_TRANSFORMERS:
            try:
                # create pipeline lazily
                self.backend = "hf"
                logger.info("AIMLAgent: Using local HuggingFace pipeline when needed.")
            except Exception as e:
                logger.exception("HF init failed: %s", e)
                self.backend = "fallback"

    def respond(self, message: str, user_id: Optional[str] = "anonymous") -> str:
        message = sanitize_text(message)
        if not message:
            return "I didn't catch that — please type a message."

        if self.backend == "openai":
            return self._respond_openai(message, user_id)
        elif self.backend == "hf":
            return self._respond_hf(message, user_id)
        else:
            return self._respond_fallback(message, user_id)

    def _respond_openai(self, message: str, user_id: Optional[str]) -> str:
        try:
            system_prompt = "You are AIML Nexus, an expert assistant for AIML research and development. Keep answers concise and actionable."
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=300,
                temperature=0.7,
            )
            text = resp.choices[0].message.content.strip()
            try:
                save_turn(user_id, message, text)
            except Exception:
                logger.debug("Could not save turn.")
            return text
        except Exception as e:
            logger.exception("OpenAI call failed: %s", e)
            return self._respond_fallback(message, user_id)

    def _respond_hf(self, message: str, user_id: Optional[str]) -> str:
        try:
            if self.generator is None:
                # Lazy load to avoid heavy startup cost unless used
                self.generator = pipeline("text-generation", model=self.hf_model, device=-1)
            prompt = f"You are AIML Nexus. User: {message}\nAIML Nexus:"
            out = self.generator(prompt, max_length=256, do_sample=True, top_p=0.95, top_k=50, num_return_sequences=1)
            text = out[0].get("generated_text", "")
            # remove prompt prefix if present
            if prompt in text:
                reply = text.split(prompt, 1)[1].strip()
            else:
                # fallback to full text
                reply = text.strip()
            try:
                save_turn(user_id, message, reply)
            except Exception:
                logger.debug("Could not save turn.")
            return reply
        except Exception as e:
            logger.exception("HF generation failed: %s", e)
            return self._respond_fallback(message, user_id)

    def _respond_fallback(self, message: str, user_id: Optional[str]) -> str:
        m = message.lower()
        if any(g in m for g in ["hello", "hi", "hey"]):
            reply = "Hello! I'm AIML Nexus — how can I help you with your AIML project?"
        elif "help" in m or "how do i" in m or "how to" in m:
            reply = "Tell me what you want to build (model type, dataset, or problem) and I'll suggest steps."
        elif "bye" in m or "thanks" in m or "thank you" in m:
            reply = "You're welcome! If you need more help, ask anytime."
        else:
            reply = f"I received: {message}. (Tip: set OPENAI_API_KEY to enable richer replies.)"
        try:
            save_turn(user_id, message, reply)
        except Exception:
            logger.debug("Could not save turn.")
        return reply