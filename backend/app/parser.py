"""Bandcamp HTML parser.

Parses a bandcamp release page (album or track) into a structured dict.
No audio is downloaded; the :class:`AudioDownloader` protocol is provided
so that downloading can be added later without touching the parser.
"""

from __future__ import annotations

import html as html_lib
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup


class ParseError(Exception):
    """Raised when input is not usable at all (e.g. empty HTML)."""


def _extract_tralbum(html_text: str) -> tuple[Optional[dict], list[str]]:
    errors: list[str] = []
    m = re.search(r'data-tralbum="([^"]*)"', html_text)
    if not m:
        errors.append("data-tralbum attribute not found")
        return None, errors
    try:
        raw = html_lib.unescape(m.group(1))
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        errors.append(f"failed to parse data-tralbum JSON: {exc}")
        return None, errors
    if not isinstance(data, dict):
        errors.append("data-tralbum is not an object")
        return None, errors
    return data, errors


def _extract_cart(html_text: str) -> dict:
    m = re.search(r'data-cart="([^"]*)"', html_text)
    if not m:
        return {}
    try:
        return json.loads(html_lib.unescape(m.group(1)))
    except (json.JSONDecodeError, ValueError):
        return {}


def _og(soup: BeautifulSoup, prop: str) -> Optional[str]:
    tag = soup.find("meta", attrs={"property": prop})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


def _meta_name(soup: BeautifulSoup, name: str) -> Optional[str]:
    tag = soup.find("meta", attrs={"name": name})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None




def _parse_comments(soup: BeautifulSoup) -> list[dict]:
    comments: list[dict] = []
    for el in soup.select(".comment"):
        contents = el.select_one(".comment-contents")
        author = el.select_one(".comment-author")
        text = (contents.get_text(strip=True) if contents else el.get_text(strip=True))
        if not text:
            continue
        comments.append({
            "author": author.get_text(strip=True) if author else None,
            "text": text,
        })
    # de-duplicate identical entries
    seen = set()
    unique = []
    for c in comments:
        key = (c.get("author"), c.get("text"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)
    return unique[:20]


def _html_lyrics(soup: BeautifulSoup) -> str | None:
    for sel in (".lyrics", "#lyrics", ".track-lyrics", "[data-lyrics]"):
        el = soup.select_one(sel)
        if el:
            txt = el.get_text("\n", strip=True)
            if txt:
                return txt
    return None

def _image_url_from_art_id(art_id: Any) -> Optional[str]:
    if not art_id:
        return None
    try:
        return f"https://f4.bcbits.com/img/a{int(art_id)}_5.jpg"
    except (TypeError, ValueError):
        return None


def parse_release(html_text: str, url: str = "") -> dict:
    """Parse a bandcamp release page.

    Returns a dict with fields plus an ``errors`` list. ``errors`` contains
    human readable descriptions of markup that could not be interpreted.
    """
    errors: list[str] = []
    if not html_text or not html_text.strip():
        raise ParseError("empty html")

    soup = BeautifulSoup(html_text, "html.parser")
    tralbum, terrs = _extract_tralbum(html_text)
    errors.extend(terrs)

    current: dict = {}
    tralbum_obj = tralbum if isinstance(tralbum, dict) else {}
    if isinstance(tralbum, dict):
        cur = tralbum.get("current")
        if isinstance(cur, dict):
            current = cur
        else:
            errors.append("tralbum.current is missing or not an object")

    # --- title ---
    title = current.get("title")
    if not title:
        title = _og(soup, "og:title")
        if title and ", by " in title:
            title = title.split(", by ")[0].strip()
        if not title:
            errors.append("title could not be parsed")
    # --- artist ---
    artist = current.get("artist") or tralbum_obj.get("artist")
    if not artist:
        og_title = _og(soup, "og:title")
        if og_title and ", by " in og_title:
            artist = og_title.rsplit(", by ", 1)[-1].strip()
        if not artist:
            errors.append("artist could not be parsed")
    # --- type ---
    rtype = current.get("type") or current.get("short_type")
    type_map = {"album": "album", "a": "album", "track": "track", "t": "track"}
    normalized_type = type_map.get(str(rtype).lower()) if rtype is not None else None
    if normalized_type is None:
        # fallback from og:type
        og_type = _og(soup, "og:type")
        if og_type in ("album", "music.album"):
            normalized_type = "album"
        elif og_type in ("song", "music.song", "track"):
            normalized_type = "track"
    if normalized_type is None:
        errors.append("release type could not be parsed")
        normalized_type = "unknown"

    # --- cover image ---
    cover = _og(soup, "og:image")
    if not cover:
        cover = _image_url_from_art_id(current.get("art_id"))
    if not cover:
        errors.append("cover image could not be parsed")

    # --- release date ---
    release_date = current.get("release_date") or current.get("album_release_date")
    if not release_date and isinstance(current.get("album"), dict):
        release_date = current["album"].get("release_date") or current["album"].get("album_release_date")
    if not release_date:
        release_date = current.get("publish_date")
    if not release_date:
        # top-level fallbacks
        release_date = tralbum_obj.get("album_release_date") or tralbum_obj.get("release_date")
    if not release_date:
        errors.append("release date could not be parsed")

    # --- price ---
    price = current.get("minimum_price")
    if price is None:
        price = current.get("set_price")
    if price is None and isinstance(current.get("album"), dict):
        price = current["album"].get("minimum_price")
    # currency
    cart = _extract_cart(html_text)
    currency = cart.get("currency")
    if price is None:
        errors.append("price could not be parsed")

    # --- about / credits ---
    about = current.get("about")
    if about is None and isinstance(current.get("album"), dict):
        about = current["album"].get("about")
    credits = current.get("credits")
    if credits is None and isinstance(current.get("album"), dict):
        credits = current["album"].get("credits")

    # --- tracks ---
    tracks: list[dict] = []
    trackinfo = current.get("trackinfo")
    if not isinstance(trackinfo, list):
        trackinfo = tralbum_obj.get("trackinfo")
    if isinstance(trackinfo, list) and trackinfo:
        for t in trackinfo:
            if not isinstance(t, dict):
                continue
            tracks.append({
                "track_num": t.get("track_num"),
                "title": t.get("title"),
                "duration": t.get("duration"),
                "lyrics": t.get("lyrics"),
            })
    elif normalized_type == "track":
        tracks.append({
            "track_num": current.get("track_number"),
            "title": current.get("title"),
            "duration": None,
            "lyrics": current.get("lyrics"),
        })
    # validate track titles
    for tr in tracks:
        if not tr.get("title"):
            errors.append("a track title could not be parsed")

    if normalized_type == "album" and not tracks:
        errors.append("track list could not be parsed")

    # --- description ---
    description = about
    if not description:
        description = _og(soup, "og:description")
    if description and description.startswith(" from the album "):
        description = None
    if description and about and description.strip() == about.strip():
        description = None

    # --- lyrics ---
    lyrics = current.get("lyrics")
    if lyrics is None and isinstance(current.get("album"), dict):
        lyrics = current["album"].get("lyrics")
    if not lyrics:
        # trackinfo lyrics (first track with lyrics)
        if isinstance(trackinfo, list):
            for t in trackinfo:
                if isinstance(t, dict) and t.get("lyrics"):
                    lyrics = t.get("lyrics")
                    break
    if not lyrics:
        lyrics = _html_lyrics(soup)

    # --- comments ---
    comments = _parse_comments(soup)

    # --- url canonical ---
    canonical_url = url
    og_url = _og(soup, "og:url")
    if og_url:
        canonical_url = og_url

    result = {
        "url": canonical_url or url,
        "title": title,
        "artist": artist,
        "type": normalized_type,
        "cover_image_url": cover,
        "release_date": release_date,
        "price": price,
        "currency": currency,
        "about": about,
        "description": description,
        "credits": credits,
        "lyrics": lyrics,
        "comments": comments,
        "tracks": tracks,
        "errors": errors,
    }
    return result


def fetch_html(url: str, timeout: int = 20) -> str:
    """Fetch a bandcamp page. Separated for testability/mocking.

    Waits on the shared rate limiter before each request so repeated parses
    do not hit Bandcamp faster than ``BANDCAMP_MIN_INTERVAL`` seconds.
    """
    import requests

    from .ratelimit import limiter

    headers = {"User-Agent": "Mozilla/5.0"}
    limiter.wait()
    resp = requests.get(url, headers=headers, timeout=timeout)
    if resp.status_code == 429:
        retry_after = resp.headers.get("Retry-After")
        try:
            delay = float(retry_after) if retry_after else limiter.interval()
        except ValueError:
            delay = limiter.interval()
        delay = min(max(delay, 1.0), 30.0)
        time.sleep(delay)
        limiter.wait()
        resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


@dataclass
class DownloadResult:
    url: str
    path: Optional[str] = None
    ok: bool = False
    error: Optional[str] = None


class AudioDownloader:
    """Extension point for audio downloading (not implemented yet)."""

    def download(self, release: dict, destination: str) -> DownloadResult:  # pragma: no cover - extension point
        return DownloadResult(url=release.get("url", ""), ok=False, error="audio download not implemented")


def is_bandcamp_url(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    return "bandcamp.com" in host


__all__ = ["parse_release", "fetch_html", "ParseError", "AudioDownloader", "DownloadResult", "is_bandcamp_url"]
