import pytest

import app as appmod


@pytest.fixture
def client():
    appmod.app.config["TESTING"] = True
    return appmod.app.test_client()


def test_default_template_card_is_checked(client):  # DEFAULT is ieee_conference
    html = client.get("/").data.decode()
    assert 'name="ruleset" value="ieee_conference" checked' in html


def test_stylesheet_is_served(client):
    r = client.get("/static/style.css")
    assert r.status_code == 200 and b"#3B3F9E" in r.data and b"@media" in r.data


def test_rail_lists_three_steps(client):
    html = client.get("/").data.decode()
    for step in ("template", "upload", "report"):
        assert f'data-step="{step}"' in html


def test_privacy_line_present(client):
    assert "Your file is deleted right after the check." in client.get("/").data.decode()


def test_wording_checkbox_discloses_ai_when_available(client, monkeypatch):
    monkeypatch.setattr("suggest.available", lambda: True)
    html = client.get("/").data.decode()
    assert 'name="wording"' in html and "sent to an AI service" in html


def test_wording_checkbox_hidden_when_unavailable(client, monkeypatch):
    monkeypatch.setattr("suggest.available", lambda: False)
    assert 'name="wording"' not in client.get("/").data.decode()


def test_form_works_without_script(client):  # all steps in the markup, file input required
    html = client.get("/").data.decode()
    assert 'name="paper"' in html and "required" in html and 'action="/check"' in html


def test_script_is_served(client):
    assert client.get("/static/app.js").status_code == 200


import io

CLEAN = open("samples/test_paper_clean.docx", "rb").read()
FLAWED = open("samples/test_paper_flawed.docx", "rb").read()


def post_paper(client, data, **form):
    body = {"paper": (io.BytesIO(data), "p.docx"), **form}
    return client.post("/check", data=body, content_type="multipart/form-data")


def test_report_shows_count_cards(client):  # flawed sample under IEEE conference: 9 errors, 3 warnings
    html = post_paper(client, FLAWED).data.decode()
    assert 'data-count="errors">9<' in html and 'data-count="warnings">3<' in html
    assert 'class="finding finding-error"' in html and 'data-step="report"' in html
    assert 'class="rail-item is-active" data-step="report"' in html


def test_clean_paper_shows_zero_and_no_problems(client):
    html = post_paper(client, CLEAN).data.decode()
    assert 'data-count="errors">0<' in html and 'data-count="warnings">0<' in html
    assert "No problems found against this rule set." in html


def test_oversize_upload_is_friendly(client):
    big = (io.BytesIO(b"PK\x03\x04" + b"0" * (10 * 1024 * 1024 + 1)), "big.docx")
    r = client.post("/check", data={"ruleset": "ieee_conference", "paper": big},
                    content_type="multipart/form-data")
    assert r.status_code == 413 and b"File is larger than 10 MB." in r.data
    assert b"Check your paper before you submit" in r.data


def test_template_filename_is_escaped(client):
    from docx import Document
    buf = io.BytesIO()
    Document().save(buf)
    data = {"paper": (io.BytesIO(CLEAN), "p.docx"), "ruleset": "custom",
            "template": (io.BytesIO(buf.getvalue()), "<img src=x onerror=1>.docx")}
    r = client.post("/check", data=data, content_type="multipart/form-data")
    assert r.status_code == 200
    assert b"<img src=x" not in r.data and b"&lt;img src=x" in r.data


def test_error_keeps_template_and_message(client):
    r = client.post("/check", data={"ruleset": "springer_lncs"}, content_type="multipart/form-data")
    assert r.status_code == 400 and b"Please choose a .docx file." in r.data
    assert b'name="ruleset" value="springer_lncs" checked' in r.data


def test_findings_are_in_a_scroll_box(client):
    html = post_paper(client, FLAWED).data.decode()
    box = html.index('class="findings"')
    assert box < html.index('class="finding finding-error"') < html.index("Check another paper")
    assert html.index('data-count="errors"') < box          # count cards stay above the box
    assert html.index("</div>\n", html.rindex('class="finding finding-warn"')) < html.index("Check another paper")


def test_clean_report_has_no_scroll_box(client):
    assert 'class="findings"' not in post_paper(client, CLEAN).data.decode()


def test_scroll_box_has_fixed_height_css(client):
    css = client.get("/static/style.css").data.decode()
    assert ".findings{" in css and "max-height" in css and "overflow-y:auto" in css
