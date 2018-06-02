"""Synthetic Checks Manger.

The manager module is responsible for managing the threads and queues
responsible for issuing check requests.

"""
import collections
import datetime
import logging
import requests
import threading
import time
import queue


class RequestsManager(object):

    def __init__(self, thread_count=1, logger=None):
        """Initialize a new Request Manager.

        Args:
            thread_count(int): Number of threads to spawn for requests.

        """
        self.logger = logger or logging.getLogger(__name__)
        self.thread_count = thread_count
        self.request_queue = queue.Queue()
        self.threads = []
        self.results = {}
        self.lock = threading.Lock()
        self.logger.debug("Created a new RequestManager")

    @property
    def window(self):
        """Return a copy of the current result window.

        Result windows are returned as a dictionary with endpoint slugs as keys

        """
        _w = {}
        with self.lock:
            for endpoint, data in self.results.items():
                _w[endpoint.slug] = []
                for window in data:
                    _w[endpoint.slug].append(window)
        return _w

    def start(self):
        """Start a new thread pool.

        Start a new thread pool of `thread_count`.

        """
        self.logger.info(
            f"Starting a new thread pool with {self.thread_count} threads")
        if len(self.threads) > 0:
            print(f"thread pool already been started? {len(self.threads)}")
            return
        for i in range(self.thread_count):
            t = EndpointRequestThread(lock=self.lock,
                                      request_queue=self.request_queue,
                                      request_results=self.results)
            self.threads.append(t)
            t.start()

    def clear(self):
        """Remove all items from the queue."""
        while not self.request_queue.empty():
            item = self.request_queue.get()
            self.request_queue.task_done()
            print(f'popped a queue item: {item}')

    def stop(self):
        """Enumerate all threads and tell them to die.

        """
        for t in self.threads:
            print(f"stopping {t.name}")
            t.should_die = True
        self.threads = []


class EndpointRequestThread(threading.Thread):
    """Endpoint Request Thread.

    The endpoint request thread is responsible for making a request to an
    endpoint and storing the results.

    Each thread pops an Endpoint object off the request queue to process.  When
    the request is completed, the thread adds the Endpoint back to the queue.


    Endpoint Results:
        Endpoint results are stored in a shared dictionary that maps endpoint
        objects to a deque of dimensions::

            {
              EndPointObject: [{
                'timestamp': timestamp of request,
                'TTFB': Time to first byte (ms),
                'elapsed': Time to last byte (ms),
                'status_code': status code returned
              }],
              'System': {
                'count': number of requests
              }
            }

        The deque is configurable at thread creation time with the purpose of
        operating as a moving time window of results.

        The `timestamp` is stored as a timezone aware datetime object.  The
        timezone is `UTC`.

        The `System` key contains information about the runtime of the manager.
        `count` contains the number of requests that have been made since the
        system was started.

    """

    def __init__(self,
                 group=None,
                 target=None,
                 name=None,
                 lock=None,
                 request_queue=queue.Queue(),
                 request_results={},
                 window_size=20,
                 verbose=None,
                 args=(),
                 kwargs=None):
        """Initialize the request thread.

        Initialize an endpoint request thread.

        Args:
            lock(`threading.Lock`): primitive lock for `request_results`
            request_queue(`queue.Queue`): queue for storing endpoints
            request_results(`dict`):  results of endpoint requests.

        The lifetime of a thread is controlled by the member variable
        `should_die`.  The thread will continue to wait for requests from the
        queue unless this is true.
        """
        super(EndpointRequestThread, self).__init__(group=group, target=target,
                                                    name=name)
        self.args = args
        self.kwargs = kwargs
        self.lock = lock
        self.request_queue = request_queue
        self.request_results = request_results
        self.window_size = window_size
        self.should_die = False  # flag to terminate thread

    def update(self, endpoint, dimensions):
        """Update the results.

        Update `request_results` with the latest data from a request.

        """
        with self.lock:
            if endpoint not in self.request_results:
                self.request_results[endpoint] = collections.deque(
                    maxlen=self.window_size)
            self.request_results[endpoint].append(dimensions)

    def request(self, endpoint):
        """Make a request to the `endpoint`.

        Make the request to the passed `endpoint` and record the results.

        """
        # TODO: This is starting to get messy, clean this up
        dimensions = {}
        dimensions['datetime'] = datetime.datetime.now(datetime.timezone.utc)
        dimensions['timestamp'] = dimensions['datetime'].timestamp()
        try:
            url, payload = endpoint.request
            response = requests.request(endpoint.verb, url, **payload)
            dimensions['content'] = response.content
            dimensions['status_code'] = response.status_code
            dimensions['TTFB'] = sum((r.elapsed for r in response.history),
                                     response.elapsed).total_seconds() * 1000.0
        except requests.exceptions.ConnectionError as ex:
            dimensions['status_code'] = 500
            dimensions['failure_reason'] = f"Connection Error: {ex}"
        request_end = datetime.datetime.now(datetime.timezone.utc)
        dimensions['elapsed'] = \
            (request_end - dimensions['datetime']).total_seconds() * 1000.0
        self.update(
            endpoint=endpoint,
            dimensions=dimensions
        )

    def wait_for_frequency(self, frequency):
        """wait for this run's frequency to expire"""
        while frequency > 0:
            # check if the thread wants to die
            if self.should_die:
                return
            time.sleep(1)
            frequency -= 1

    def run(self):
        """Thread execution point.

        The run method is the thread entrypoint.  This method will continue
        to run until `should_die` is true.

        """
        while True:
            if self.should_die:
                break
            try:
                # Get the next endpoint; get blocks by default
                # throw Empty exception after timeout to prevent deadlock
                # TODO: make sure this is actually an `Endpoint`
                endpoint = self.request_queue.get(timeout=10)
                self.request(endpoint)
                self.wait_for_frequency(endpoint.frequency)
                self.request_queue.task_done()
                self.request_queue.put(endpoint)
            except queue.Empty:
                continue  # give the thread a chance
