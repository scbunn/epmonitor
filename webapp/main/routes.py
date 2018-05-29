"""Landing page routes.

This module contains the main routes of the web application.

"""
from flask import render_template, flash, redirect, url_for
from webapp.main import bp
from webapp.models import Monitor
from webapp import requestManager
from checks.endpoint import Endpoint


@bp.route('/stop')
def stop():
    """Stop threads"""
    requestManager.stop()
    return "stopped"


@bp.route('/stats')
def stats():
    # TODO: Testing purposes only; move to an API
    return f"{requestManager.window}"


@bp.route('/load')
def load():
    """Convert Monitors to Endpoints and queue them for requests."""
    # TODO: find a place for this to live; ideally this should be able to
    #       occur outside of route.  Maybe this belongs in a utility function
    #       that is called with an application_context on start.  Also, this
    #       will need to be called from the UI

    # first we need to kill any running threads
    requestManager.stop()

    # Now we need to clear the queue
    requestManager.clear()

    count = 0
    for monitor in Monitor.query.all():
        if monitor.enabled:
            count += 1
            ep = Endpoint(monitor.slug)
            ep.name = monitor.name
            ep.frequency = monitor.frequency
            ep.scheme = monitor.scheme
            ep.server = monitor.server
            ep.port = monitor.port
            ep.path = monitor.path
            ep.verb = monitor.verb
            ep.payload = monitor.payload
            ep.header(**monitor.headers)
            requestManager.request_queue.put(ep)
    requestManager.start()
    flash(f"Loaded {count} monitors")
    return redirect(url_for('monitors.index'))


@bp.route('/')
def index():
    """The main index page.

    This page shows some basic stats and index cards for other components of
    the applicaiton.

    """
    return render_template('index.html.j2')
