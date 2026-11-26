"""Optional wording suggestions (language only).

Safeguards:
  * Off unless ANTHROPIC_API_KEY is set.
  * The model is told to fix grammar, clarity and style only. It must not change
    meaning, numbers, citations, names or technical terms.
  * Programmatic check: a suggestion is dropped if it changes any number,
    citation marker like [3], or capitalised technical token from the original.
  * Suggestions are only shown to the author. Nothing is applied automatically.
"""
import json
import os
import re

MAX_PARAGRAPHS = 12
MAX_CHARS_PER_PARAGRAPH = 1500

SYSTEM = (
    "You are a careful language editor for academic manuscripts. For each paragraph "
    "you receive, suggest at most one improved version that fixes grammar, spelling, "
    "clarity and style ONLY. Never change meaning, claims, numbers, citation markers "
    "such as [3], names, abbreviations or technical terms. Never add new content or "
    "new facts. If a paragraph needs no change, omit it. Reply with ONLY a JSON array "
    'of objects: {"index": <int>, "suggestion": <string>, "reason": <short string>}.'
)

_TOKEN_RE = re.compile(r"\[[\d,\s–\-]+\]|\d+(?:\.\d+)?|\b[A-Z][A-Za-z0-9\-]{2,}\b")


def _tokens(text: str):
    return sorted(_TOKEN_RE.findall(text))


def preserves_content(original: str, suggestion: str) -> bool:
    """True if numbers, citation markers and capitalised tokens are unchanged."""
    return _tokens(original) == _tokens(suggestion)


def available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def suggest(paragraphs):
    """paragraphs: list of (paragraph_number, text). Returns list of dicts."""
    if not available() or not paragraphs:
        return []
    import anthropic  # imported lazily so the app runs without the key

    items = [(n, t[:MAX_CHARS_PER_PARAGRAPH]) for n, t in paragraphs[:MAX_PARAGRAPHS]]
    payload = [{"index": n, "text": t} for n, t in items]
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=os.environ.get("PAPERDESK_MODEL", "claude-sonnet-5-5"),
        max_tokens=2000,
        system=SYSTEM,
        messages=[{"role": "user", "content": json.dumps(payload)}],
    )
    raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    originals = dict(items)
    out = []
    for d in data if isinstance(data, list) else []:
        n = d.get("index")
        s = d.get("suggestion")
        if n in originals and isinstance(s, str) and s.strip() and s.strip() != originals[n].strip():
            if preserves_content(originals[n], s):
                out.append({"paragraph": n, "original": originals[n], "suggestion": s.strip(),
                            "reason": str(d.get("reason", ""))[:200]})
    return out
