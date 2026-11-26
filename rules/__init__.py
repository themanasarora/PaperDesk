"""Rule-set registry. One module per template, each exposing a RULES dict.

Rules are static data. Each one carries `verified`, `source` (official URL)
and `last_verified` (ISO date) so reports can warn when they are unchecked
or stale. Add a template by creating rules/<key>.py and registering it below.
"""
import datetime

from . import ieee_conference, ieee_journal, springer_lncs

DEFAULT = "ieee_conference"
STALE_AFTER_DAYS = 180

RULESETS = {
    "ieee_conference": ieee_conference.RULES,
    "ieee_journal": ieee_journal.RULES,
    "springer_lncs": springer_lncs.RULES,
}

DEFAULTS = {
    "page_name": "US Letter",
    "heading_style": "roman",  # "roman" or "numeric"
    "keywords_label": "Index Terms",
    "table_numbering": "roman",  # "roman" or "arabic"
    "reference_style": "bracket",  # "bracket" = [1] ...; "dotted" = "1. Author..." after the References heading
    "verified": False,
    "source": "",
    "last_verified": None,
}


def with_defaults(rules: dict) -> dict:
    return {**DEFAULTS, **rules}


def get_ruleset(key: str) -> dict:
    return with_defaults(RULESETS[key])


def rules_notice(rules: dict, today: datetime.date | None = None) -> str | None:
    """A warning for the report, or None when the rules are verified and fresh."""
    if not rules.get("verified"):
        return ("Unverified draft rules: confirm every requirement against the "
                "official template before relying on this report.")
    last = rules.get("last_verified")
    if not last:
        return "Rules were verified but the date is not recorded; confirm they are current."
    today = today or datetime.date.today()
    try:
        age = (today - datetime.date.fromisoformat(last)).days
    except (ValueError, TypeError):
        return "Rules verification date is unreadable (use YYYY-MM-DD); confirm the rules are current."
    if age > STALE_AFTER_DAYS:
        return f"Rules last verified on {last} ({age} days ago) and may be out of date."
    return None
