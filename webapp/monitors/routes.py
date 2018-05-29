"""Monitors routes

This module contains the routes used by the monitors package.

"""
import slugify
from checks.endpoint import Endpoint
from webapp import requestManager, db
from webapp.monitors import bp
from webapp.models import Monitor
from webapp.monitors.forms import EndpointForm, HeaderForm
from flask import render_template, flash, url_for, redirect, request


@bp.route('/')
def index():
    """monitors index page

    The index page shows all currently configured monitors.

    """
    monitors = Monitor.query.all()
    results = requestManager.window
    return render_template('monitors/index.html.j2',
                           monitors=monitors,
                           results=results)


@bp.route('/<slug>')
def details(slug):
    """Load a monitor for viewing.

    This loads the details page for a monitor.

    """
    monitor = Monitor.query.filter_by(slug=slug).first_or_404()
    # TODO: clean this up, it seems messy; not sure why we keep converting a
    #       monitor to endpoint and back.
    #       maybe merge Endpoint and the Monitor data class?
    endpoint = Endpoint(monitor.slug)
    endpoint.frequency = monitor.frequency
    endpoint.scheme = monitor.scheme
    endpoint.server = monitor.server
    endpoint.port = monitor.port
    if monitor.path:
        endpoint.path = monitor.path
    endpoint.verb = monitor.verb
    if monitor.payload:
        endpoint.payload = monitor.payload
    if monitor.headers:
        endpoint.header(**monitor.headers)
    title = f"Monitor {monitor.name}"

    if monitor.slug in requestManager.window:
        results = requestManager.window[monitor.slug]
    else:
        results = {}

    return render_template('monitors/details.html.j2',
                           title=title,
                           monitor=monitor,
                           endpoint=endpoint,
                           results=results)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    """Add a new endpoint monitor.

    This methods loads a new form to create a new endpoint monitor.

    """
    form = EndpointForm()
    monitor = Monitor()
    if form.validate_on_submit():   # form is being POSTed
        monitor = process_form_data(form, monitor)
        flash("New monitor created")
        return redirect(url_for('monitors.details', slug=monitor.slug))

    # GET request; Show a new blank form
    return render_template('monitors/edit.html.j2', title='New',
                           form=form, monitor=monitor)


@bp.route('/<slug>/edit', methods=['GET', 'POST'])
def edit(slug):
    """Edit a monitor

    Edit the details of a particular monitor.

    """
    monitor = Monitor.query.filter_by(slug=slug).first_or_404()
    form = EndpointForm()
    if form.validate_on_submit():  # changes were submitted
        process_form_data(form, monitor)
        flash(f"{monitor.name} updated")
        return redirect(url_for('monitors.details', slug=monitor.slug))
    elif request.method == 'GET':  # Loading the form for display
        form.name.data = monitor.name
        form.frequency.data = monitor.frequency
        form.scheme.data = monitor.scheme
        form.server.data = monitor.server
        form.port.data = monitor.port
        form.path.data = monitor.path
        form.verb.data = monitor.verb
        form.payload.data = monitor.payload
        for key, value in monitor.headers.items():
            hf = HeaderForm()
            hf.key = key
            hf.value = value
            form.headers.append_entry(hf)

    return render_template('monitors/edit.html.j2', title='Edit',
                           form=form, monitor=monitor)


def parse_headers(headers):
    """Parse form headers.

    Convert data returned from the form into the correct JSON format for the
    database.

    """
    _h = {}
    for header in headers:
        key, value = list(header.values())
        _h[key] = value
    return _h


def process_form_data(form, monitor):
    """Process data from the EndpointForm.

    Process data from the EndpointForm and convert it to a Monitor while
    serializing the result to the database.

    """
    monitor.name = form.name.data
    monitor.slug = slugify.slugify(form.name.data)
    monitor.frequency = form.frequency.data
    monitor.scheme = form.scheme.data
    monitor.server = form.server.data
    monitor.port = form.port.data
    monitor.path = form.path.data
    monitor.verb = form.verb.data
    monitor.payload = form.payload.data
    monitor.headers = parse_headers(form.headers.data)
    db.session.add(monitor)
    db.session.commit()
    return monitor
