"""Runtime settings routes.

The runtime settings package is designed to display and allow runtime
configuration changes of the application.

"""
import psutil
import os
from datetime import datetime, timezone
from flask import render_template
from webapp.settings import bp
from webapp import requestManager
from webapp.models import Monitor


@bp.route('/')
def display_runtime_settings():
    """Display current runtime settings.

    Display's the current runtime configuration of the application.

    """
    system = system_stats()
    rm = requestManager_stats()
    return render_template(
        'settings/index.html.j2',
        title="Runtime Settings",
        stats={**system, **rm},
    )


def system_stats():
    """Return a snapshot of the running system.

    Return a dictionary of runtime system settings.

    """
    p = psutil.Process(os.getpid())
    return {
        'system': {
            'cpu_percent': psutil.cpu_percent(interval=None),
            'cpu_times': psutil.cpu_times(percpu=False),
            'cpu_stats': psutil.cpu_stats(),
            'memory': psutil.virtual_memory(),
            'netio': psutil.net_io_counters(),
        },
        'proc': {
            'pid': p.pid,
            'parent': p.parent(),
            'thread_count': p.num_threads(),
            'threads': p.threads(),
            'connections': p.connections(),
            'memory': p.memory_full_info(),
            'created': datetime.fromtimestamp(p.create_time(), timezone.utc)
        }
    }


def requestManager_stats():
    """Return a snapshot of the requestManager settings."""
    threads = requestManager.threads

    # TODO: Fix Me; only return monitors with enabled = True for monitor count
    return {
        'requestManager': {
            'thread_count': requestManager.thread_count,
            'queue_size': requestManager.request_queue.qsize(),
            'endpoint_count': len(Monitor.query.all()),
            'threads': {
                'running': len(threads),
                'active': [(t.name, t.status, t.is_alive()) for t in threads]
            }
        }
    }
