from unittest.mock import patch

import pytest


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_parse_persists_report(client, album_html):
    with patch("app.api.fetch_html", return_value=album_html):
        r = client.post("/api/parse", json={"url": "https://radiohead.bandcamp.com/album/in-rainbows"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["title"] == "In Rainbows"
    assert data["errors"] == []

    r2 = client.get("/api/reports")
    assert r2.status_code == 200
    reports = r2.get_json()["reports"]
    assert len(reports) == 1
    assert reports[0]["title"] == "In Rainbows"


def test_parse_invalid_url(client):
    r = client.post("/api/parse", json={"url": "https://example.com/x"})
    assert r.status_code == 400


def test_parse_missing_url(client):
    r = client.post("/api/parse", json={})
    assert r.status_code in (400, 422)


def test_delete_report(client, album_html):
    with patch("app.api.fetch_html", return_value=album_html):
        client.post("/api/parse", json={"url": "https://radiohead.bandcamp.com/album/in-rainbows"})
    reports = client.get("/api/reports").get_json()["reports"]
    rid = reports[0]["id"]
    r = client.delete(f"/api/reports/{rid}")
    assert r.status_code == 200
    assert client.get("/api/reports").get_json()["reports"] == []


def test_delete_missing_report(client):
    r = client.delete("/api/reports/9999")
    assert r.status_code == 404


def test_get_report(client, album_html):
    with patch("app.api.fetch_html", return_value=album_html):
        client.post("/api/parse", json={"url": "https://radiohead.bandcamp.com/album/in-rainbows"})
    reports = client.get("/api/reports").get_json()["reports"]
    rid = reports[0]["id"]
    r = client.get(f"/api/reports/{rid}")
    assert r.status_code == 200
    assert r.get_json()["id"] == rid
    assert r.get_json()["data"]["title"] == "In Rainbows"


def test_get_missing_report(client):
    r = client.get("/api/reports/9999")
    assert r.status_code == 404


def test_swagger(client):
    r = client.get("/swagger-ui")
    assert r.status_code == 200
