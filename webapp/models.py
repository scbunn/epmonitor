"""EP Monitor Data Model.

This module contains the database models used by all blueprints and packages
in the application.

"""
from datetime import datetime
from checks.endpoint import HTTPVerb
from sqlalchemy import CheckConstraint
from sqlalchemy_json import MutableJson
from webapp import db
from wtforms import BooleanField


class Monitor(db.Model):
    """Endpoint Monitor.

    Data model of an Endpoint.  This model is not normalized.

    """
    __tablename__ = 'monitors'
    __table_args__ = (
        CheckConstraint('port > 0 AND port < 65536', name='valid_port_range'),
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    slug = db.Column(db.String(), index=True, unique=True, nullable=False)
    created = db.Column(db.TIMESTAMP(timezone=True),
                        default=datetime.utcnow, nullable=False)
    updated = db.Column(db.TIMESTAMP(timezone=True),
                        default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
    frequency = db.Column(db.Integer, nullable=False)
    scheme = db.Column(db.String(16), nullable=False)
    server = db.Column(db.String(256), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    path = db.Column(db.String)
    verb = db.Column(db.Enum(HTTPVerb))
    payload = db.Column(db.Text)
    headers = db.Column(MutableJson)
    enabled = db.Column(db.Boolean(name='monitor_enabled'), nullable=False)

    def __repr__(self):
        return "<Monitor {}: >".format(self.slug, self.name)
