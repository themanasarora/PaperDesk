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
