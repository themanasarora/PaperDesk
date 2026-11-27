"""Regression tests on real papers kept only on the developer's machine.

The papers live in real_papers/ (git-ignored: they are other people's unpublished
work). On any machine without the file these tests are skipped.
"""
import collections
import os

import pytest

import checker
from rules import get_ruleset

FRIEND = "real_papers/friend.docx"
needs_friend = pytest.mark.skipif(not os.path.exists(FRIEND), reason="real paper not on this machine")


@needs_friend
def test_two_column_ieee_style_paper_gives_only_real_findings():
    issues = checker.check(FRIEND, get_ruleset("ieee_conference"))
    assert dict(collections.Counter(i.rule for i in issues)) == {
        "Margin": 4,                       # 0.64/0.19/0.5/0.5 in against 0.75/1.0/0.625/0.625
        "Abstract length": 1,              # 104 words
        "Heading numbering": 3,            # two headings with no number; Arabic instead of Roman
        "Citation without reference": 9,   # cites [1]-[22], the list has 13 entries
        "Body text style": 1,              # stray 8 pt fragment "r [21]."
    }
    missing = sorted(i.detail for i in issues if i.rule == "Citation without reference")
    assert [d.split("]")[0] for d in missing] == sorted(f"Citation [{n}" for n in range(14, 23))


@needs_friend
def test_no_false_alarms_from_word_numbering_captions_or_small_text():
    issues = checker.check(FRIEND, get_ruleset("ieee_conference"))
    rules = {i.rule for i in issues}
    assert not rules & {"Table referenced but missing", "Table not referenced", "Reference never cited"}
    for i in issues:
        if i.rule == "Body text style":
            assert "Introduction" not in i.where and "References" not in i.where and "TABLE" not in i.where
