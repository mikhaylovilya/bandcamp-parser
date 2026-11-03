"""Flask app factory."""

from __future__ import annotations

import os

from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from .api import blp, configure
from .db import create_db_engine


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    CORS(app)

    app.config.setdefault("API_TITLE", "Bandcamp Parser API")
    app.config.setdefault("API_VERSION", "v1")
    app.config.setdefault("OPENAPI_VERSION", "3.0.3")
    app.config.setdefault("OPENAPI_URL_PREFIX", "/")
    app.config.setdefault("OPENAPI_SWAGGER_UI_PATH", "/swagger-ui")
    app.config.setdefault("OPENAPI_SWAGGER_UI_URL", "https://cdn.jsdelivr.net/npm/swagger-ui-dist/")
    app.config.setdefault("TESTING", False)

    if config:
        app.config.update(config)

    engine = create_db_engine(app.config.get("DATABASE_URL") or os.environ.get("DATABASE_URL"))
    configure(engine)

    api = Api(app)
    api.register_blueprint(blp)

    # serve frontend static? no, separate container.

    @app.route("/")
    def index():
        return {"service": "bandcamp-parser", "docs": "/swagger-ui"}

    return app


# convenience for gunicorn/flask run
app = create_app()
