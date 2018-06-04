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


RequestDimension = collections.namedtuple('RequestDimension', [
    'date',           # datetime.datetime
    'timestamp',      # timestamp()
    'status',         # Boolean (did the request fail or not)
    'status_code',    # HTTP status code
    'TTFB',           # Time to first Byte
    'elapsed',        # Total elapsed time
    'content',        # Content of the Request
    'message',        # Any passed message (usually failure reason)
])


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

        Start a new thread pool of `thread_count`.  `start` will stop all
        currently running threads and create a new thread pool.

        """
        if len(self.threads) > 0:  # if there is a pool already, kill it
            self.stop()
        for i in range(self.thread_count):
            t = EndpointRequestThread(lock=self.lock,
                                      request_queue=self.request_queue,
                                      request_results=self.results)
            t.logger = self.logger
            self.threads.append(t)
            t.start()
        self.logger.info(
            f"Started a new thread pool with {self.thread_count} threads")

    def clear(self):
        """Remove all items from the queue."""
        while not self.request_queue.empty():
            item = self.request_queue.get()
            self.request_queue.task_done()
            print(f'popped a queue item: {item}')

    def stop(self, join=False):
        """Enumerate all threads and tell them to die.

        """
        for t in self.threads:
            self.logger.debug(f"Stopping {t.name}")
            t.should_die = True

       # NOTE: We don't join() by default here; there is a risk that we
       #       leave behind orphaned threads.
        if join:
            for t in self.threads:
                self.logger.debug(f"joining {t.name}")
                t.join()

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
    COUNT = 0

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
        EndpointRequestThread.COUNT += 1
        if not name:
            name = f"EndpointRequest-{EndpointRequestThread.COUNT}"
        super(EndpointRequestThread, self).__init__(group=group, target=target,
                                                    name=name)
        self.args = args
        self.kwargs = kwargs
        self.lock = lock
        self.request_queue = request_queue
        self.request_results = request_results
        self.window_size = window_size
        self.should_die = False  # flag to terminate thread
        self.status = "Waiting for an endpoint request"
        self.logger = logging.getLogger(__name__)

    def update(self, endpoint, request_dimension):
        """Update the results.

        Update `request_results` with the latest data from a request.

        """
        self.status = "Updating result window"
        with self.lock:
            if endpoint not in self.request_results:
                self.request_results[endpoint] = collections.deque(
                    maxlen=self.window_size)
            self.request_results[endpoint].append(request_dimension)

    def _build_dimensions(self, result, message, start, end, response=None):
        """Build a `RequestDimension`

        Build a new `RequestDimension` for the current request.

        """
        if result:  # the request was successful
            status_code = response.status_code
            content = response.content
            TTFB = sum((r.elapsed for r in response.history),
                       response.elapsed).total_seconds() * 1000.0
        else:
            status_code = 0
            content = None
            TTFB = 0
        return RequestDimension(
            start,
            start.timestamp(),
            result,
            status_code,
            TTFB,
            (end - start).total_seconds() * 1000.0,
            content,
            message
        )

    def request(self, endpoint):
        """Make a request to the `endpoint`.

        Make the request to the passed `endpoint` and record the results.

        """
        self.status = f"Sending a request to an endpoint, {endpoint.name}"
        start = datetime.datetime.now(datetime.timezone.utc)
        result = True
        message = ''
        response = None
        try:
            url, payload = endpoint.request
            response = requests.request(endpoint.verb, url, **payload)
        except requests.exceptions.RequestException as ex:
            result = False
            message = f"{getattr(ex, 'message', repr(ex))}"

        end = datetime.datetime.now(datetime.timezone.utc)
        rd = self._build_dimensions(result, message, start, end, response)
        self.update(endpoint, rd)

    def wait_for_frequency(self, frequency, name):
        """wait for this run's frequency to expire"""
        self.status = \
            f"waiting for endpoint frequency to expire, {name}, {frequency}"
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
        self.logger.debug("Starting a new RequestManager Thread")
        while True:
            if self.should_die:
                break
            try:
                self.status = "Checking queue for an endpoint"
                # Get the next endpoint; get blocks by default
                # throw Empty exception after timeout to prevent deadlock
                # TODO: make sure this is actually an `Endpoint`
                endpoint = self.request_queue.get(timeout=3)
                self.logger.debug(f"{self.name} is checking {endpoint.name}")
                self.request(endpoint)
                self.wait_for_frequency(endpoint.frequency, endpoint.name)
                self.request_queue.task_done()
                self.request_queue.put(endpoint)
            except queue.Empty:
                self.status = "Queue is empty"
                continue  # give the thread a chance
            self.status = "Waiting for an endpoint request"
