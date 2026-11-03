"""Marshmallow schemas for the API."""

from __future__ import annotations

from marshmallow import Schema, fields


class TrackSchema(Schema):
    track_num = fields.Integer(allow_none=True)
    title = fields.String(allow_none=True)
    duration = fields.Float(allow_none=True)
    lyrics = fields.String(allow_none=True)


class ReleaseSchema(Schema):
    url = fields.String()
    title = fields.String(allow_none=True)
    artist = fields.String(allow_none=True)
    type = fields.String(allow_none=True)
    cover_image_url = fields.String(allow_none=True)
    release_date = fields.String(allow_none=True)
    price = fields.Float(allow_none=True)
    currency = fields.String(allow_none=True)
    about = fields.String(allow_none=True)
    description = fields.String(allow_none=True)
    credits = fields.String(allow_none=True)
    lyrics = fields.String(allow_none=True)
    comments = fields.List(fields.Dict())
    tracks = fields.List(fields.Nested(TrackSchema))
    errors = fields.List(fields.String())


class ParseRequestSchema(Schema):
    url = fields.String(required=True)


class ReportSchema(Schema):
    id = fields.Integer()
    url = fields.String()
    title = fields.String(allow_none=True)
    artist = fields.String(allow_none=True)
    release_type = fields.String(allow_none=True)
    data = fields.Nested(ReleaseSchema)
    created_at = fields.String(allow_none=True)


class ReportListSchema(Schema):
    reports = fields.List(fields.Nested(ReportSchema))


class MessageSchema(Schema):
    message = fields.String()
