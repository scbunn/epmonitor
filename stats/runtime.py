"""Runtime Statistics collector.

This package collects runtime statistics about the operating system and
application.


"""
import collections
import psutil
import os
import threading
import time
from datetime import datetime, timezone


class RuntimeStats(object):
    """Runtime statistics object.

    The RuntimeStats object collects system and application runtime
    statistics with a running window.  A window of stats are collected so that
    it can be graphed.

    The stats data structure::

        {
          'stats': {
            'cpu': {
              'utilization': int,
              'user': deque[30],
              'system': deque[30],
              'idle': deque[30]
            },
            'memory': {
              'free': int,
              'consumed_by_stack': int,
              'total': deque[30],
              'available': deque[30]
            },
            'network': {
              'connections_total': int,
              'bytes_sent': deque[30],
              'bytes_recv': deque[30],
              'connections': list(dict(connections))
            },
            'stack': {
              'pid': int,
              'app_thread_count': int,
              'rm_max_threads': int,
              'rm_running_threads': int,
              'queue_size': int,
              'stack_threads': list(dict(app_threads)),
              'rm_threads': list(dict(requestManager_threads))
            }
          }
        }

    """

    def __init__(self, request_manager=None):
        self._stats = {
            'cpu': {
                'utilization': 0,
                'user': collections.deque(maxlen=30),
                'system': collections.deque(maxlen=30),
                'idle': collections.deque(maxlen=30),
            },
            'memory': {
                'free': 0,
                'consumed_by_stack': 0,
                'total': collections.deque(maxlen=30),
                'available': collections.deque(maxlen=30),
            },
            'network': {
                'connections_total': 0,
                'bytes_sent': collections.deque(maxlen=30),
                'bytes_recv': collections.deque(maxlen=30),
                'bytes_sent_s': collections.deque(maxlen=30),
                'bytes_recv_s': collections.deque(maxlen=30),
                'connections': []
            },
            'stack': {
                'pid': 0,
                'max_threads': 0,
                'running_threads': 0,
                'queue_size': 0,
                'stack_threads': [],
                'rm_threads': []
            }
        }

        self.rm = request_manager
        self.lock = threading.Lock()
        collect_thread = threading.Thread(target=self.collect, args=())
        collect_thread.daemon = True
        collect_thread.start()

    def _update_cpu(self, snapshot, ts):
        """Update CPU runtime statistics"""
        _c = snapshot['system']
        with self.lock:
            self._stats['cpu']['utilization'] = _c.get('cpu_percent', 0)
            self._stats['cpu']['user'].append(
                (_c['cpu_times'].user, ts)
            )
            self._stats['cpu']['system'].append(
                (_c['cpu_times'].system, ts)
            )
            self._stats['cpu']['idle'].append(
                (_c['cpu_times'].idle, ts)
            )

    def _update_memory(self, snapshot, ts):
        """Update Memory runtime statistics"""
        _m = snapshot['system']['memory']
        with self.lock:
            self._stats['memory']['free'] = _m.free
            self._stats['memory']['consumed_by_stack'] = \
                snapshot['proc']['memory'].uss
            self._stats['memory']['total'].append(
                (_m.total, ts)
            )
            self._stats['memory']['available'].append(
                (_m.available, ts)
            )
            self._stats['memory']['used_pct'] = _m.percent

    def _update_network(self, snapshot, ts):
        """Update Network runtime statistics"""
        _n = snapshot['system']['netio']
        with self.lock:
            self._stats['network']['connections_total'] = \
                len(snapshot['proc']['connections'])
            self._stats['network']['bytes_sent'].append(
                (_n.bytes_sent, ts)
            )
            self._stats['network']['bytes_recv'].append(
                (_n.bytes_recv, ts)
            )
            self._stats['network']['bytes_sent_s'].append(
                (snapshot['system']['netstats']['sent_s'], ts)
            )
            self._stats['network']['bytes_recv_s'].append(
                (snapshot['system']['netstats']['recv_s'], ts)
            )
            self._stats['network']['connections'] = \
                snapshot['proc']['connections']

    def _update_stack(self, snapshot, ts):
        """Update the Flask Stack runtime statistics"""
        _s = snapshot['proc']
        _r = snapshot['requestManager']
        with self.lock:
            self._stats['stack']['pid'] = _s['pid']
            self._stats['stack']['app_thread_count'] = _s['thread_count']
            self._stats['stack']['running_threads'] = len(_s['threads'])
            self._stats['stack']['stack_threads'] = _s['threads']
            if self.rm:
                self._stats['stack']['rm_max_threads'] = _r['thread_count']
                self._stats['stack']['rm_running_threads'] = \
                    _r['threads']['running']
                self._stats['stack']['queue_size'] = _r['queue_size']
                self._stats['stack']['rm_threads'] = _r['threads']['active']

    def update(self):
        """Update the current stats window."""

        ts = datetime.now(timezone.utc).timestamp()
        snapshot = self.snapshot
        self._update_cpu(snapshot, ts)
        self._update_memory(snapshot, ts)
        self._update_network(snapshot, ts)
        self._update_stack(snapshot, ts)

    @property
    def stats(self):
        """Return our window of stats"""
        return self._stats

    def collect(self):
        """Thread to collect runtime stats and populate internal stats"""
        while True:  # terminates at application exit
            self.update()
            time.sleep(10)  # collect every 10 seconds

    @property
    def request_manager(self):
        if not self.rm:
            return {'requestManager': {}}

        threads = self.rm.threads
        # TODO: Fix Me
        #       only return monitors with enabled = True for monitor count
        return {
            'requestManager': {
                'thread_count': self.rm.thread_count,
                'queue_size': self.rm.request_queue.qsize(),
                'threads': {
                    'running': len(threads),
                    'active': [
                        (t.name, t.status, t.is_alive()) for t in threads]
                }
            }
        }

    @property
    def system(self):
        """Return a dictionary of system stats."""
        p = psutil.Process(os.getpid())
        net_before = psutil.net_io_counters()
        time.sleep(1)
        net_after = psutil.net_io_counters()
        return {
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=None),
                'cpu_times': psutil.cpu_times_percent(interval=None),
                'memory': psutil.virtual_memory(),
                'netio': net_after,
                'netstats': {
                    'sent_s': net_after.bytes_sent - net_before.bytes_sent,
                    'recv_s': net_after.bytes_recv - net_before.bytes_recv
                }
            },
            'proc': {
                'pid': p.pid,
                'parent': p.parent(),
                'thread_count': p.num_threads(),
                'threads': p.threads(),
                'connections': p.connections(),
                'memory': p.memory_full_info(),
                'created': datetime.fromtimestamp(
                    p.create_time(), timezone.utc)
            }
        }

    @property
    def snapshot(self):
        """Return a snapshot of current runtime stats."""
        return {**self.system, **self.request_manager}
