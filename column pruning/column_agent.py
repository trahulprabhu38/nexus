from typing import List, Dict, Tuple
import ast
import os
import argparse
from pathlib import Path
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

class ColumnPruningAgent:
    def __init__(self, model: str | None = None):
        # Prefer env override, then fallback to a broadly available, supported model name
        effective_model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
        self.llm = ChatGoogleGenerativeAI(model=effective_model)
        self.prompt = PromptTemplate(
            input_variables=["query", "columns"],
            template=(
                "You are a Column Pruning Agent. Your job is to choose only the necessary "
                "columns required to answer the user's query.\n\n"
                "User Query:\n{query}\n\n"
                "Available Columns:\n{columns}\n\n"
                "Rules:\n"
                "- Select only columns needed to answer the query.\n"
                "- Do not add imaginary fields.\n"
                "- Do not include irrelevant or sensitive columns unless the query requires them.\n"
                "- Choose ONLY from the Available Columns using their exact names.\n"
                "- Final output must be ONLY a Python list of column names, with no explanation.\n"
            ),
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def prune_with_reason(self, query: str, columns: List[str]) -> Tuple[List[str], Dict[str, str], List[str]]:
        """Return pruned columns, reasons per column, and pruned-out columns.

        LLM is asked to produce strict JSON: {"keep": [..], "prune": [..], "reasons": {col: reason}}
        """
        reason_prompt = PromptTemplate(
            input_variables=["query", "columns"],
            template=(
                "You are a Column Pruning Agent. Choose only necessary columns to answer the query.\n\n"
                "User Query:\n{query}\n\n"
                "Available Columns (use exact names):\n{columns}\n\n"
                "Rules:\n"
                "- Only choose from Available Columns.\n"
                "- No imaginary fields.\n"
                "- Be minimal but sufficient.\n\n"
                "Output STRICT JSON with keys: keep (list of columns to keep), prune (list to drop), reasons (object mapping each column to a short reason).\n"
                "Example: {\"keep\":[\"G3\",\"sex\"],\"prune\":[\"age\"],\"reasons\":{\"G3\":\"target metric\",\"sex\":\"grouping\",\"age\":\"not needed\"}}\n"
            ),
        )
        chain = reason_prompt | self.llm | StrOutputParser()
        response_text = chain.invoke({
            "query": query,
            "columns": ", ".join(columns),
        })

        # Clean up the response - remove markdown code blocks if present
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            # Remove markdown code fence
            lines = cleaned_text.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        data = None
        try:
            data = json.loads(cleaned_text)
        except Exception:
            try:
                data = ast.literal_eval(cleaned_text)
            except Exception as e:
                raise ValueError(f"Model did not return valid JSON for reasoning. Got: {cleaned_text[:200]}") from e

        keep = data.get("keep", []) if isinstance(data, dict) else []
        prune_out = data.get("prune", []) if isinstance(data, dict) else []
        reasons = data.get("reasons", {}) if isinstance(data, dict) else {}

        # Validate against available columns (case-insensitive mapping)
        name_map = {c.lower(): c for c in columns}
        seen = set()
        pruned: List[str] = []
        for item in keep:
            if isinstance(item, str):
                key = item.strip().lower()
                if key in name_map and name_map[key] not in seen:
                    seen.add(name_map[key])
                    pruned.append(name_map[key])

        # Normalize reasons to actual column names
        norm_reasons: Dict[str, str] = {}
        if isinstance(reasons, dict):
            for k, v in reasons.items():
                if not isinstance(k, str):
                    continue
                key = k.strip().lower()
                if key in name_map:
                    norm_reasons[name_map[key]] = str(v)

        # Compute pruned-out list intersecting available columns
        norm_prune_out: List[str] = []
        for item in prune_out:
            if isinstance(item, str):
                key = item.strip().lower()
                if key in name_map:
                    norm_prune_out.append(name_map[key])

        if not pruned:
            raise ValueError("No valid columns selected. Ensure output uses exact available names.")

        return pruned, norm_reasons, norm_prune_out

    def prune_offline_simple(self, query: str, columns: List[str]) -> List[str]:
        """Heuristic, LLM-free pruning by keyword matching.
        - Matches column names/tokens appearing in the query (case-insensitive)
        - Adds common target/metric/group-by terms
        """
        q = query.lower()
        tokens = set(q.replace("(", " ").replace(")", " ").replace(",", " ").split())
        # Seed keywords
        keywords = {
            "sum", "avg", "average", "mean", "total", "count", "by", "group", "trend" ,
            "year", "month", "day", "date",
        }
        tokens |= keywords
        selected: List[str] = []
        for c in columns:
            cl = c.lower()
            name_parts = set(cl.replace("_", " ").split())
            if cl in q or name_parts & tokens:
                selected.append(c)
        # Minimal safeguard: if nothing matched, return columns most mentioned in datasets like grades
        if not selected:
            for c in ["G3", "G2", "G1", "sex", "school", "internet", "absences"]:
                if c in columns:
                    selected.append(c)
        # Deduplicate preserving order
        seen = set(); dedup = []
        for c in selected:
            if c not in seen:
                seen.add(c); dedup.append(c)
        return dedup

    def prune(self, query: str, columns: List[str]) -> List[str]:
        response_text = self.chain.invoke({
            "query": query,
            "columns": ", ".join(columns),
        })

        # Clean up the response - remove markdown code blocks if present
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            # Remove markdown code fence
            lines = cleaned_text.split("\n")
            # Remove first line (```python or ``` or ```json)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        # Parse model output strictly
        try:
            parsed = ast.literal_eval(cleaned_text)
        except Exception as e:
            raise ValueError(f"Model did not return a valid Python list of strings. Got: {cleaned_text[:200]}") from e

        if not (isinstance(parsed, list) and all(isinstance(x, str) for x in parsed)):
            raise ValueError("Model did not return a valid Python list of strings.")

        # Build case-insensitive map to actual column names
        name_map = {c.lower(): c for c in columns}
        seen = set()
        pruned: List[str] = []
        for item in parsed:
            key = item.strip().lower()
            if key in name_map:
                actual = name_map[key]
                if actual not in seen:
                    seen.add(actual)
                    pruned.append(actual)

        if not pruned:
            raise ValueError("No valid columns selected. Ensure you choose only from the available columns.")

        return pruned


if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        raise SystemExit("Please set GOOGLE_API_KEY in your environment (or .env) to run this program.")

    parser = argparse.ArgumentParser(description="Column Pruning Agent CLI")
    default_file = (Path(__file__).parent / "student_data.csv").resolve()
    parser.add_argument("--file", type=str, default=str(default_file), help=f"Path to dataset (csv/parquet/xlsx). Defaults to {default_file}")
    parser.add_argument("--query", type=str, help="Natural language query to answer")
    parser.add_argument("--show", action="store_true", help="Show the table (head) of the dataset")
    parser.add_argument("--limit", type=int, default=10, help="Number of rows to show when using --show")
    parser.add_argument("--category", type=str, help="Category column name to inspect or filter")
    parser.add_argument("--value", type=str, help="Value of the category to filter rows by")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode: prompt for actions and inputs")
    parser.add_argument("--show-pruned", action="store_true", help="After pruning, display the pruned columns' table")
    parser.add_argument("--pruned-limit", type=int, default=10, help="Rows to show when displaying pruned columns")
    parser.add_argument("--reason", action="store_true", help="Also output keep/prune reasoning per column")
    parser.add_argument("--metrics", action="store_true", help="Also output efficiency metrics of pruning")
    parser.add_argument("--offline-simple", action="store_true", help="Use a heuristic, offline pruning (no LLM)")
    args = parser.parse_args()

    # If no action flags were provided, default to interactive mode
    no_action = not any([
        args.show,
        bool(args.query),
        bool(args.category),
        args.interactive,
    ])
    if no_action:
        args.interactive = True

    agent = ColumnPruningAgent()

    if args.file:
        path = Path(args.file)
        if not path.exists():
            raise SystemExit(f"File not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(path)
        elif suffix in {".parquet", ".pq"}:
            df = pd.read_parquet(path)
        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(path)
        else:
            raise SystemExit("Unsupported file type. Use csv, parquet, or xlsx/xls.")

        pd.set_option("display.max_columns", 200)
        pd.set_option("display.width", 200)

        if args.show:
            print(df.head(args.limit))

        if args.category and not args.value:
            if args.category not in df.columns:
                raise SystemExit(f"Column not found: {args.category}")
            vals = df[args.category].value_counts(dropna=False).reset_index()
            vals.columns = [args.category, "count"]
            print(vals)

        if args.category and args.value is not None:
            if args.category not in df.columns:
                raise SystemExit(f"Column not found: {args.category}")
            filtered = df[df[args.category].astype(str) == str(args.value)]
            print(filtered.head(args.limit))

        if args.query:
            columns = list(df.columns)
            if args.offline_simple:
                pruned_columns = agent.prune_offline_simple(args.query, columns)
                reasons = {c: "Selected by heuristic keyword match." for c in pruned_columns}
                pruned_out = [c for c in columns if c not in pruned_columns]
            elif args.reason or args.metrics:
                pruned_columns, reasons, pruned_out = agent.prune_with_reason(args.query, columns)
            else:
                pruned_columns = agent.prune(args.query, columns)
                reasons = {}
                pruned_out = [c for c in columns if c not in pruned_columns]
            print("\n[Pruned Columns]")
            print(pruned_columns)
            if args.reason:
                # Display reasoning in a compact form
                print("\n[Column Decisions]")
                for c in columns:
                    status = "KEEP" if c in pruned_columns else "PRUNE"
                    r = reasons.get(c, "")
                    print(f"- {c}: {status} {('- ' + r) if r else ''}")
            if args.metrics:
                kept = len(pruned_columns); total = len(columns); removed = total - kept
                pct = (removed / total * 100.0) if total else 0.0
                print(f"\n[Efficiency] kept={kept}, removed={removed} of {total} columns ({pct:.1f}% reduction)")
            if args.show_pruned:
                try:
                    print(df[pruned_columns].head(args.pruned_limit))
                except Exception as e:
                    print(f"Error displaying pruned columns: {e}")

        if args.interactive:
            while True:
                print("\nSelect an action: \n 1) Show table head \n 2) List category values \n 3) Filter by category=value \n 4) Prune columns for a query \n 5) Exit")
                choice = input("Enter choice [1-5]: ").strip()
                if choice == "1":
                    try:
                        n = int(input(f"Rows to show [default {args.limit}]: ") or args.limit)
                    except Exception:
                        n = args.limit
                    print(df.head(n))
                elif choice == "2":
                    cat = input("Category column name: ").strip()
                    if cat not in df.columns:
                        print(f"Column not found: {cat}")
                        continue
                    vals = df[cat].value_counts(dropna=False).reset_index()
                    vals.columns = [cat, "count"]
                    print(vals)
                elif choice == "3":
                    cat = input("Category column name: ").strip()
                    if cat not in df.columns:
                        print(f"Column not found: {cat}")
                        continue
                    val = input("Value to filter by: ").strip()
                    try:
                        n = int(input(f"Rows to show [default {args.limit}]: ") or args.limit)
                    except Exception:
                        n = args.limit
                    filtered = df[df[cat].astype(str) == str(val)]
                    print(filtered.head(n))
                elif choice == "4":
                    q = input("Enter your query (natural language): ").strip()
                    columns = list(df.columns)
                    try:
                        mode = input("Use offline heuristic? [y/N]: ").strip().lower()
                        if mode == "y":
                            pruned = agent.prune_offline_simple(q, columns)
                            reasons = {c: "Selected by heuristic keyword match." for c in pruned}
                            pruned_out = [c for c in columns if c not in pruned]
                        else:
                            explain = input("Show reasoning and metrics? [y/N]: ").strip().lower()
                            if explain == "y":
                                pruned, reasons, pruned_out = agent.prune_with_reason(q, columns)
                            else:
                                pruned = agent.prune(q, columns)
                                reasons = {}
                                pruned_out = [c for c in columns if c not in pruned]
                        print("\n[Pruned Columns]")
                        print(pruned)
                        show = input("Show these columns' content? [y/N]: ").strip().lower()
                        if show == "y":
                            try:
                                n = int(input(f"Rows to show [default {args.limit}]: ") or args.limit)
                            except Exception:
                                n = args.limit
                            try:
                                print(df[pruned].head(n))
                            except Exception as e:
                                print(f"Error displaying pruned columns: {e}")
                        if reasons:
                            print("\n[Column Decisions]")
                            for c in columns:
                                status = "KEEP" if c in pruned else "PRUNE"
                                r = reasons.get(c, "")
                                print(f"- {c}: {status} {('- ' + r) if r else ''}")
                            kept = len(pruned); total = len(columns); removed = total - kept
                            pct = (removed / total * 100.0) if total else 0.0
                            print(f"\n[Efficiency] kept={kept}, removed={removed} of {total} columns ({pct:.1f}% reduction)")
                    except Exception as e:
                        print(f"Error: {e}")
                elif choice == "5":
                    break
                else:
                    print("Invalid choice. Please enter 1-5.")
    else:
        query = "What is the total revenue per year?"
        columns = ["product", "region", "month", "year", "revenue", "price", "units"]
        print(f"\n[Demo Mode - Query: {query}]")
        pruned_columns = agent.prune(query, columns)
        print("\n[Pruned Columns]")
        print(pruned_columns)
