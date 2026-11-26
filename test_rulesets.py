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


REQUIRED_KEYS = {"name", "page_width_in", "page_height_in", "margins_in", "margin_tolerance_in",
                 "body_font", "body_size_pt", "abstract_words", "require_index_terms",
                 "heading_style", "table_numbering", "keywords_label", "flag_double_spaces",
                 "require_figure_table_references"}


def test_all_three_rulesets_registered():
    assert {"ieee_conference", "ieee_journal", "springer_lncs"} <= set(RULESETS)


def test_new_rulesets_are_unverified():
    assert get_ruleset("ieee_journal")["verified"] is False
    assert get_ruleset("springer_lncs")["verified"] is False


def test_springer_structure():
    r = get_ruleset("springer_lncs")
    assert (r["heading_style"], r["table_numbering"], r["page_name"], r["keywords_label"]) == \
        ("numeric", "arabic", "A4", "Keywords")


def test_ieee_journal_structure():
    assert get_ruleset("ieee_journal")["heading_style"] == "roman"


def test_every_ruleset_has_required_keys():
    for key in RULESETS:
        assert REQUIRED_KEYS <= set(get_ruleset(key)), key


@pytest.mark.parametrize("bad", ["01/12/2026", "2026-13-01", "2026-1-1", 20261201])
def test_notice_malformed_date_does_not_crash(bad):
    notice = rules_notice(with_defaults({"verified": True, "last_verified": bad}), TODAY)
    assert "unreadable" in notice


def test_registered_last_verified_values_are_iso_dates():
    for key in RULESETS:
        v = get_ruleset(key)["last_verified"]
        assert v is None or datetime.date.fromisoformat(v)
