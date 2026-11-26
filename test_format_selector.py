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


def test_template_choice_kept_after_rejected_upload(client):
    r = client.post("/check", data={"ruleset": "springer_lncs", "paper": (io.BytesIO(b"hi"), "notes.txt")},
                    content_type="multipart/form-data")
    assert r.status_code == 400
    assert b'<option value="springer_lncs" selected' in r.data


def a4_template_bytes():
    from docx import Document
    from docx.shared import Inches
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
    doc.add_paragraph("Template")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def post_custom(client, template, **extra):
    data = {"paper": (io.BytesIO(CLEAN), "p.docx"), "ruleset": "custom", **extra}
    if template is not None:
        data["template"] = (io.BytesIO(template), "journal.docx")
    return client.post("/check", data=data, content_type="multipart/form-data")


def test_form_offers_custom_and_template_upload(client):
    html = client.get("/").data.decode()
    assert '<option value="custom"' in html and 'name="template"' in html


def test_custom_uses_uploaded_template_rules(client):
    r = post_custom(client, a4_template_bytes())
    assert r.status_code == 200
    assert b"Custom template" in r.data and b"Page size" in r.data  # clean sample is Letter, template is A4


def test_custom_without_template_is_rejected_and_stays_selected(client):
    r = post_custom(client, None)
    assert r.status_code == 400
    assert b"Custom needs a template .docx." in r.data and b'<option value="custom" selected' in r.data


def test_custom_with_invalid_template_is_rejected(client):
    r = post_custom(client, b"not a docx")
    assert r.status_code == 400 and b"The template file does not look like a valid .docx." in r.data


def test_custom_leaves_no_temp_files(client):
    import glob, os, tempfile
    before = set(glob.glob(os.path.join(tempfile.gettempdir(), "*.docx")))
    post_custom(client, a4_template_bytes())
    post_custom(client, b"not a docx")
    assert set(glob.glob(os.path.join(tempfile.gettempdir(), "*.docx"))) == before
