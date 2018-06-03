#!/usr/bin/env python
"""Endpoint Monitor Jinja Utilities.

This module contains custom jinja filters and utilities.

"""
import numpy as np
from collections import Counter


def megabytes(_bytes):
    """Convert _bytes into Megabytes."""
    return _bytes / (1024 ** 2)


def gigabytes(_bytes):
    """Convert _bytes into Gigabytes."""
    return _bytes / (1024 ** 3)


def availability(window):
    """Return the availability percentage of `window`.

    A window data point is considered 'available' if the status was success

    """
    success = Counter([r for r in window if r.status])
    return (len(success) / len(window)) * 100


def failRate(window):
    """Return the percentage of results in `window` that failed.

    A window data point is considered to have failed if the request failed

    """
    failures = Counter([r for r in window if not r.status])
    if failures:
        return (len(failures)/len(window)) * 100
    return 0  # no failures have occurred


def percentile(window, p):
    """Return the `percentile` for the `window` of data passed.

    Args:
        p(int): The percentile to calculate
        window(list): A list of data points to calculate the percentile on

    """
    if not isinstance(window, list):
        raise ValueError("percentile window expects a list")

    if isinstance(window[0], tuple):  # we have a list of Monitor Results
        arry = np.array(epresult_to_list(window))
    else:  # assume we have a list of numeric data
        arry = np.array(window)
    return np.percentile(arry, p)


def stddev(window):
    """Return the standard deviation of `monitor_result`."""
    if not isinstance(window, list):
        raise ValueError('stddev window expected to be a list')
    if isinstance(window[0], tuple):
        data = epresult_to_list(window)
    else:
        data = window
    return np.std(data, ddof=1)


def epresult_to_list(result):
    """Convert a list of endpoint results to a list of numerics.

    Convert of list of endpoint results into a list of floats based on the
    endpoint's elapsed time window.

    """
    return [r.elapsed for r in result]
