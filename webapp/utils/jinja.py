#!/usr/bin/env python
"""Endpoint Monitor Jinja Utilities.

This module contains custom jinja filters and utilities.

"""
import numpy as np


def availability(window):
    """Return the availability percentage of `window`.

    A window data point is considered 'available' if the status code is 200.

    """
    success = [r['status_code'] for r in window if r['status_code'] == 200]
    return (len(success) / len(window)) * 100


def failRate(window):
    """Return the percentage of results in `window` that failed.

    A window data point is considered to have failed if the status code is not
    200.

    """
    failures = [r['status_code'] for r in window if r['status_code'] != 200]
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

    if isinstance(window[0], dict):  # we have a list of Monitor Results
        arry = np.array(epresult_to_list(window))
    else:  # assume we have a list of numeric data
        arry = np.array(window)
    return np.percentile(arry, p)


def stddev(window):
    """Return the standard deviation of `monitor_result`."""
    if not isinstance(window, list):
        raise ValueError('stddev window expected to be a list')
    if isinstance(window[0], dict):
        data = epresult_to_list(window)
    else:
        data = window
    return np.std(data, ddof=1)


def epresult_to_list(result):
    """Convert a list of endpoint results to a list of numerics.

    Convert of list of endpoint results into a list of floats based on the
    endpoint's elapsed time window.

    """
    return [r['elapsed'] for r in result]