"""Settings package

The settings package contains the routes and forms necessary to display and
configure the runtime settings of the application.

"""
from flask import Blueprint

bp = Blueprint('settings', __name__)
from webapp.settings import routes
