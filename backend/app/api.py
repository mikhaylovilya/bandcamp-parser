"""API blueprint (flask-smorest)."""

from __future__ import annotations

import os

from flask import request
from flask_smorest import Blueprint, abort
from sqlalchemy.orm import Session

from .db import make_session_factory
from .models import Report, create_all
from .parser import fetch_html, is_bandcamp_url, parse_release
from .schemas import (
    MessageSchema,
    ParseRequestSchema,
    ReleaseSchema,
    ReportListSchema,
    ReportSchema,
)

blp = Blueprint(
    "bandcamp",
    "bandcamp",
    url_prefix="/api",
    description="Bandcamp parser API",
)

# engine/session factory are configured by create_app
_session_factory = None
_engine = None


def configure(engine):
    global _engine, _session_factory
    _engine = engine
    _session_factory = make_session_factory(engine)
    create_all(engine)


def _session() -> Session:
    if _session_factory is None:
        raise RuntimeError("database not configured")
    return _session_factory()


@blp.route("/parse", methods=["POST"])
@blp.arguments(ParseRequestSchema)
@blp.response(200, ReleaseSchema)
@blp.alt_response(400, description="Invalid request")
def parse_release_endpoint(args):
    url = (args.get("url") or "").strip()
    if not url:
        abort(400, message="url is required")
    if not is_bandcamp_url(url):
        abort(400, message="url must be a bandcamp.com release URL")

    # allow injecting html via env? no. fetch.
    # For tests, support an optional header to pass raw html? no.
    try:
        html_text = fetch_html(url)
    except Exception as exc:  # network errors
        abort(400, message=f"failed to fetch url: {exc}")

    data = parse_release(html_text, url=url)

    # persist report
    session = _session()
    try:
        report = Report(
            url=data["url"],
            title=data.get("title"),
            artist=data.get("artist"),
            release_type=data.get("type"),
            data=data,
        )
        session.add(report)
        session.commit()
        session.refresh(report)
    finally:
        session.close()

    return data


@blp.route("/reports", methods=["GET"])
@blp.response(200, ReportListSchema)
def list_reports():
    session = _session()
    try:
        reports = session.query(Report).order_by(Report.id.desc()).all()
        return {"reports": [r.to_dict() for r in reports]}
    finally:
        session.close()


@blp.route("/reports/<int:report_id>", methods=["DELETE"])
@blp.response(200, MessageSchema)
def delete_report(report_id):
    session = _session()
    try:
        report = session.get(Report, report_id)
        if report is None:
            abort(404, message="report not found")
        session.delete(report)
        session.commit()
        return {"message": "deleted"}
    finally:
        session.close()


@blp.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}
