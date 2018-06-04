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


class DebugConfig(Config):
    DEBUG = True
    REQUEST_THREADS = 10
    LOG_LEVEL = "DEBUG"


def configuration():
    """Return the correct configuration object.

    Based on the current environment settings, return the correct configuration
    object.

    """
    configs = {
        'DEBUG': DebugConfig,
    }
    return configs.get(os.environ.get('FLASK_ENV'), DebugConfig)
