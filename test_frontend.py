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
