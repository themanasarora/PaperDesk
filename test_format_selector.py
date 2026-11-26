import io

import pytest

import app as appmod
import checker
import rules
from rules import RULESETS, get_ruleset

CLEAN = open("samples/test_paper_clean.docx", "rb").read()


@pytest.fixture
def client():
    return appmod.app.test_client()


def post(client, **form):
    data = {"paper": (io.BytesIO(CLEAN), "p.docx"), **form}
    return client.post("/check", data=data, content_type="multipart/form-data")


def test_form_lists_every_ruleset(client):
    html = client.get("/").data.decode()
    assert '<select name="ruleset"' in html
    for key in RULESETS:
        assert f'<option value="{key}"' in html


def test_missing_ruleset_defaults_to_ieee_conference(client):
    r = post(client)
    assert r.status_code == 200 and b"IEEE conference" in r.data


def test_springer_selected_shows_name_and_unverified_notice(client):
    r = post(client, ruleset="springer_lncs")
    assert r.status_code == 200
    assert b"Springer LNCS" in r.data and b"Unverified draft rules" in r.data


def test_unknown_ruleset_rejected_and_not_echoed(client):
    r = post(client, ruleset="<script>alert(1)</script>")
    assert r.status_code == 400
    assert b"Unknown template" in r.data and b"<script>alert" not in r.data


def test_stale_notice_in_report(client, monkeypatch):
    monkeypatch.setitem(rules.RULESETS, "ieee_conference",
                        {**rules.RULESETS["ieee_conference"], "verified": True, "last_verified": "2020-01-01"})
    assert b"2020-01-01" in post(client, ruleset="ieee_conference").data


def test_markdown_report_contains_notice():
    r = get_ruleset("springer_lncs")
    md = checker.to_markdown("x.docx", checker.check("samples/test_paper_clean.docx", r), r)
    assert "Unverified draft rules" in md
