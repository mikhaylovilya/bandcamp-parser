from pathlib import Path

import pytest

from app.parser import parse_release

CORPUS = sorted((Path(__file__).parent / "fixtures" / "corpus").glob("*.html"))


@pytest.mark.parametrize("path", CORPUS, ids=lambda p: p.name)
def test_corpus_page_parses(path):
    html = path.read_text(encoding="utf-8")
    kind = "track" if "-track-" in path.name else "album"
    data = parse_release(html, url=f"https://example.bandcamp.com/{kind}/x")

    assert data["title"]
    assert data["artist"]
    assert data["type"] == kind
    assert isinstance(data["errors"], list)
    assert isinstance(data["tracks"], list)
    assert isinstance(data["comments"], list)
    if kind == "album":
        assert data["tracks"]
