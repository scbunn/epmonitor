"""Landing Package.

This package contains the routes and functions necessary to build the landing
page.  The main package is responsible for any routes that are not part of
content specific sections or authentication.

"""
from flask import Blueprint

bp = Blueprint('main', __name__)
from webapp.main import routes
