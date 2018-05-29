"""Monitors Package

This package contains the routes and forms for viewing and manipulating
endpoint monitors.

"""
from flask import Blueprint

bp = Blueprint('monitors', __name__)
from webapp.monitors import routes
