import os

import pytest

from app.parser import parse_release, ParseError


def test_parse_album(album_html):
    data = parse_release(album_html, url="https://radiohead.bandcamp.com/album/in-rainbows")
    assert data["title"] == "In Rainbows"
    assert data["artist"] == "Radiohead"
    assert data["type"] == "album"
    assert data["cover_image_url"].startswith("https://")
    assert data["release_date"] is not None
    assert data["price"] is not None
    assert len(data["tracks"]) == 10
    assert data["tracks"][0]["title"] == "15 Step"
    assert data["errors"] == []


def test_parse_track(track_html):
    data = parse_release(track_html, url="https://radiohead.bandcamp.com/track/nude")
    assert data["title"] == "Nude"
    assert data["artist"] == "Radiohead"
    assert data["type"] == "track"
    assert len(data["tracks"]) == 1
    assert data["tracks"][0]["title"] == "Nude"
    assert data["errors"] == []


def test_parse_empty_raises():
    with pytest.raises(ParseError):
        parse_release("", url="x")


def test_parse_missing_tralbum_reports_errors():
    html = "<html><head><title>x</title></head><body></body></html>"
    data = parse_release(html, url="x")
    assert "data-tralbum attribute not found" in data["errors"]
    assert data["title"] is None or data["errors"]


def test_is_bandcamp_url():
    from app.parser import is_bandcamp_url

    assert is_bandcamp_url("https://radiohead.bandcamp.com/album/x")
    assert not is_bandcamp_url("https://example.com/x")
