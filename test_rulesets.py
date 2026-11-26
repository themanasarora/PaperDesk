import datetime

import pytest

from rules import DEFAULT, RULESETS, get_ruleset, rules_notice, with_defaults

TODAY = datetime.date(2026, 11, 27)


def test_default_key_is_registered():
    assert DEFAULT in RULESETS


def test_with_defaults_fills_missing_keys():
    out = with_defaults({"name": "x"})
    assert out["table_numbering"] == "roman"
    assert out["verified"] is False


def test_with_defaults_does_not_mutate_input():
    src = {"name": "x"}
    with_defaults(src)
    assert set(src) == {"name"}


def test_get_ruleset_unknown_key_raises():
    with pytest.raises(KeyError):
        get_ruleset("nope")


def test_notice_unverified():
    assert "Unverified draft rules" in rules_notice(get_ruleset("ieee_conference"), TODAY)


def test_notice_stale():
    rules = with_defaults({"verified": True, "last_verified": "2026-01-01"})
    assert "2026-01-01" in rules_notice(rules, TODAY)


def test_notice_fresh_is_none():
    rules = with_defaults({"verified": True, "last_verified": "2026-11-01"})
    assert rules_notice(rules, TODAY) is None


def test_notice_verified_without_date():
    rules = with_defaults({"verified": True, "last_verified": None})
    assert "not recorded" in rules_notice(rules, TODAY)
