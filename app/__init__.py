"""Application Launcher.

Build an application and launch it.  This is the entry point that creates the
flaks application.  This should be passed to FLASK_APP::

    export FLASK_APP=app
    flask run

"""
import logging
import atexit
import config
import signal
import sys
from webapp import create_app, requestManager, db
from webapp.models import Monitor


config_class = config.configuration()


def configure_logging(config):
    """Configure application logging for `app`"""
    from logging.config import dictConfig
    default_format = \
        '[%(asctime)s] %(levelname)s ' \
        'in %(module)s (%(threadName)s): %(message)s'
    logging_config = {
        'version': 1,
        'formatters': {
            'default': {
                'format': default_format,
            }
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default',
            }
        },
        'root': {
            'level': config.LOG_LEVEL,
            'handlers': ['wsgi']
        },
    }
    dictConfig(logging_config)
    logging.getLogger(__name__).info("Logging configured")


def signal_handler(signal, frame):
    logging.getLogger(__name__).info("Cleaning up application stack")
    teardown()
    sys.exit(0)


def teardown():
    requestManager.clear()
    requestManager.stop(join=True)


configure_logging(config_class)
signal.signal(signal.SIGINT, signal_handler)
atexit.register(teardown)

app = create_app(config_class)
app.logger.info("EPMonitor has started")


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Monitor': Monitor
    }
