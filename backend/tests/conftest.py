import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app(tmp_path):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path}/test.db"
    from app import create_app
    application = create_app({"DATABASE_URL": os.environ["DATABASE_URL"], "TESTING": True})
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def album_html():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "fixtures", "album.html"), encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def track_html():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "fixtures", "track.html"), encoding="utf-8") as f:
        return f.read()
