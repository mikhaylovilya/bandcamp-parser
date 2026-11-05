import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

from app.parser import fetch_html
from app.ratelimit import RateLimiter


def test_limiter_waits_between_calls(tmp_path, monkeypatch):
    sleeps = []
    monkeypatch.setattr("app.ratelimit.time.sleep", lambda seconds: sleeps.append(seconds))
    clock = {"now": 1_000.0}
    monkeypatch.setattr("app.ratelimit.time.time", lambda: clock["now"])

    limiter = RateLimiter(path=str(tmp_path / "rate"), min_interval=2.0)
    assert limiter.wait() == 0.0
    waited = limiter.wait()

    assert sleeps == [2.0]
    assert waited == 2.0


def test_limiter_disabled_when_interval_is_zero(tmp_path, monkeypatch):
    monkeypatch.setattr("app.ratelimit.time.sleep", lambda seconds: (_ for _ in ()).throw(AssertionError("slept")))
    limiter = RateLimiter(path=str(tmp_path / "rate"), min_interval=0)
    assert limiter.wait() == 0.0
    assert limiter.wait() == 0.0


def test_fetch_html_waits_before_request(monkeypatch):
    waited = MagicMock()
    monkeypatch.setattr("app.ratelimit.limiter.wait", waited)
    response = MagicMock(status_code=200, text="<html></html>")
    response.raise_for_status = MagicMock()
    with patch("requests.get", return_value=response) as get:
        html = fetch_html("https://radiohead.bandcamp.com/album/in-rainbows")
    assert html == "<html></html>"
    waited.assert_called_once()
    get.assert_called_once()


def test_ten_users_parse_without_bursting(tmp_path, monkeypatch):
    """10 concurrent parses must be spaced by the shared limiter, not fired at once."""
    interval = 0.05
    users = 10
    monkeypatch.setattr(
        "app.ratelimit.limiter",
        RateLimiter(path=str(tmp_path / "rate"), min_interval=interval),
    )

    call_times = []
    call_lock = threading.Lock()

    def fake_get(url, headers=None, timeout=None):
        with call_lock:
            call_times.append(time.time())
        response = MagicMock(status_code=200, text=f"<html>{url}</html>", headers={})
        response.raise_for_status = MagicMock()
        return response

    monkeypatch.setattr("requests.get", fake_get)
    barrier = threading.Barrier(users)
    urls = [f"https://artist{i}.bandcamp.com/album/release" for i in range(users)]

    def parse_as_user(url):
        barrier.wait(timeout=5)
        return fetch_html(url)

    started = time.time()
    with ThreadPoolExecutor(max_workers=users) as pool:
        pages = list(pool.map(parse_as_user, urls))
    elapsed = time.time() - started

    assert len(pages) == users
    assert len(call_times) == users
    call_times.sort()
    gaps = [later - earlier for earlier, later in zip(call_times, call_times[1:])]
    assert gaps, "expected more than one fetch"
    assert min(gaps) >= interval - 0.02, gaps
    assert elapsed >= interval * (users - 1) - 0.05


def test_fetch_html_retries_once_on_429(monkeypatch):
    monkeypatch.setattr("app.ratelimit.limiter.wait", MagicMock())
    monkeypatch.setattr("app.ratelimit.limiter.interval", lambda: 2.0)
    sleeps = []
    monkeypatch.setattr("app.parser.time.sleep", lambda seconds: sleeps.append(seconds))

    limited = MagicMock(status_code=429, headers={"Retry-After": "3"})
    ok = MagicMock(status_code=200, text="ok", headers={})
    ok.raise_for_status = MagicMock()
    with patch("requests.get", side_effect=[limited, ok]):
        assert fetch_html("https://radiohead.bandcamp.com/track/nude") == "ok"
    assert sleeps == [3.0]
