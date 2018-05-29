"""Flask Web Application Configuration.

Configure the flask app.  Provides the base configuration object.

"""
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.runtime-environment'))


class Config(object):
    """Base Flask Configuration class.

    Use this object directly or inherit for environment customizations.

    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'develop-so-secret'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'postgresql+psycopg2://postgres:development@localhost/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = "debug"
