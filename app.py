"""Application Launcher.

Build an application and launch it.  This is the entry point that creates the
flaks application.  This should be passed to FLASK_APP::

    export FLASK_APP=app.py
    flask run

"""
import atexit
from webapp import create_app, requestManager


def teardown():
    print("tearing down...")
    requestManager.stop()


atexit.register(teardown)

app = create_app()
