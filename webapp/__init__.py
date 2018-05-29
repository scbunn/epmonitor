"""Monitor Web application.

This is the frontend web application that sits in front of the endpoint
monitor.

"""
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_moment import Moment
from checks.manager import RequestsManager
from webapp.utils.jinja import percentile, failRate, availability, stddev

# Application Globals; Required for Flask application factories
db = SQLAlchemy()
migrate = Migrate()
moment = Moment()
requestManager = RequestsManager(10)


def create_app(config_class=Config):
    """Flask application factory.

    This function is responsible for constructing an instance of the flask
    application with the desired configuration state.

    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)

    # Register the main blueprint.  This is the home/landing page
    from webapp.main import bp as main_blueprint
    app.register_blueprint(main_blueprint)

    # Register the monitors blueprint.
    from webapp.monitors import bp as monitors_blueprint
    app.register_blueprint(monitors_blueprint, url_prefix='/monitors')

    # Register some custom jinja filters
    app.jinja_env.filters['percentile'] = percentile
    app.jinja_env.filters['failRate'] = failRate
    app.jinja_env.filters['availability'] = availability
    app.jinja_env.filters['stddev'] = stddev

    requestManager.start()

    return app

from webapp import models
