"""Endpoint Object.

This module defines what an endpoint looks like.  The endpoint object defines
all the components necessary .

"""
import enum


@enum.unique
class HTTPVerb(enum.Enum):
    """HTTP request verb."""
    GET = 1
    POST = 2
    PUT = 3
    DELETE = 4


class Endpoint(object):
    """The Endpoint.

    The `Endpoint` is an object representing a Uniform Resource Identifier
    (URI)::

        scheme://host:port/path?query

    Combined with the `HTTPVerb`, `Headers`, and `Payload` necessary to make a
    valid and meaningful request.

    """

    def __init__(self, slug):
        """ the endpoint object.

        An endpoint object is instantiated empty and built through a series of
        properties.  This constructor should set sane defaults.

        Args:
            slug(str): A unique identifier for this endpoint.

        Properties:
            frequency(int): The maximum frequency to make requests in seconds
            scheme(str): The scheme of the URI
            server(str): The server to make requests to
            port(int): The port the server is listening on
            path(str): The path of the resource being requested
            verb(`HTTPVerb`): The HTTP verb to use when making the request
            headers(dict): A map of headers to include in the request
            payload(str): The payload to include as part of the request

        The endpoint needs a unique identifier to associate it with a monitor.
        A endpoint is associated with a monitor if their slugs are equal.
        """
        self.slug = slug
        self._frequency = 10
        self._scheme = 'https'
        self._server = 'localhost'
        self._port = 443
        self._path = '/'
        self._verb = HTTPVerb.GET
        self._headers = []
        self._payload = None

    @property
    def payload(self):
        """Return the payload of the endpoint."""
        return self._payload

    @payload.setter
    def payload(self, value):
        """Sets the payload of the endpoint.

        The payload is represented as a string.  It the callers responsibility
        to parse this value into something meaningful.

        """
        if not isinstance(value, str):
            raise ValueError("The payload should be passed as a string.")
        self._payload = value

    @property
    def headers(self):
        """Return all of the headers of the endpoint."""
        return self._headers

    @headers.setter
    def headers(self, value):
        """Headers should be set via headers()"""
        raise ValueError("Use header() to set headers")

    def header(self, key=None, value=None, **kwargs):
        """Set the endpoints headers.

        Headers can be defined through the key and value arguments or as a list
        of keyword arguments.  If the header key contains special characters
        then you must use the key and value arguments.

        Args:
            key(str): Header key
            value(str): Header value

        Example using keyword arguments::

            >>> e = Endpoint()
            >>> e.header(Allow="GET, HEAD")
            >>> e.headers
            [{'Allow': 'GET, HEAD'}]
            >>>

        Example using key/value arguments::

            >>> e = Endpoint()
            >>> e.header(key='Content-Type', value='text/html')
            >>> e.headers
            [{'Content-Type': 'text/html'}]
            >>>

        """
        if key:
            self._headers.append({key: value})
            return
        for key, value in kwargs.items():
            self._headers.append({key: value})

    @property
    def path(self):
        """Return the path of the endpoint."""
        if self._path.startswith('/'):
            return self._path.lstrip('/')
        return self._path

    @path.setter
    def path(self, value):
        """Set the path of the endpoint."""
        if not isinstance(value, str):
            raise ValueError("The path should be passed as a string.")
        self._path = value

    @property
    def verb(self):
        """Return the `name` of the HTTP verb."""
        return self._verb.name

    @verb.setter
    def verb(self, value):
        """Set the HTTP Verb of the endpoint.

        The verb can be passed as a `string`, `HTTPVerb`, or `Integer`.

        """
        if isinstance(value, str):
            try:
                self._verb = HTTPVerb[value]
                return
            except KeyError:
                raise ValueError(f"{value} is not a valid HTTPVerb")

        if isinstance(value, HTTPVerb):
            self._verb = value
            return

        if isinstance(value, int):
            try:
                self._verb = HTTPVerb(value)
                return
            except ValueError:
                raise ValueError(f"{value} is not a valid HTTPVerb")

        raise ValueError(f"{value} is not a valid HTTPb")

    @property
    def scheme(self):
        """Return the scheme of the URI."""
        if self._scheme.endswith('://'):
            return self._scheme
        return f"{self._scheme}://"

    @scheme.setter
    def scheme(self, value):
        """Set the scheme."""
        if not isinstance(value, str):
            raise ValueError("The scheme should be passed as a string.")
        self._scheme = value

    @property
    def server(self):
        """Return the server of this endpoint."""
        return self._server

    @server.setter
    def server(self, value):
        """Set the server.

        The server can be represented as a domain or as an IP.

        """
        if not isinstance(value, str):
            raise ValueError("The server should be passed as a string.")
        self._server = value

    @property
    def port(self):
        """Return the port of the server for this endpoint."""
        return self._port

    @port.setter
    def port(self, value):
        """Set the port of the server for this endpoint."""
        try:
            self._port = int(value)
        except ValueError:
            raise ValueError("The port should be an integer.")

    @property
    def frequency(self):
        """Return the maximum frequency of requests for this endpoint.

        This is the *maximum* frequency.  A request will take `frequency` plus
        the endpoint response time.  If the endpoint responds in 1 second and
        frequency is set to 10 seconds, the endpoint can be checked a maximum
        of once every `11` seconds.

        """
        return self._frequency

    @frequency.setter
    def frequency(self, value):
        """Set the frequency of this endpoint.  `value` should be seconds."""
        try:
            self._frequency = int(value)
        except ValueError:
            raise ValueError(
                "Endpoint frequencies are measured in seconds as an integer.")

    @property
    def url(self):
        """Return a URL.

        Return a requests compatible URL.

        """
        return f"{self.scheme}{self.server}:{self.port}/{self.path}"

    @url.setter
    def url(self, value):
        """This property should be read-only."""
        raise ValueError("The url property is read only.")
