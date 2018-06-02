"""Application Launcher.

Build an application and launch it.  This is the entry point that creates the
flaks application.  This should be passed to FLASK_APP::

    export FLASK_APP=app.py
    flask run

"""
import atexit
import config
import signal
import sys
from webapp import create_app, requestManager


config_class = config.configuration()


def signal_handler(signal, frame):
    print("Cleaning up application stack...")
    teardown()
    sys.exit(0)


def teardown():
    requestManager.clear()
    requestManager.stop()


signal.signal(signal.SIGINT, signal_handler)
atexit.register(teardown)

app = create_app(config_class)
