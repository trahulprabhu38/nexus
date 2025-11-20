# backend/utils.py
def sanitize_text(s: str) -> str:
    if s is None:
        return ''
    return s.strip()