"""
An HTTP server that listens on localhost and returns a variety of responses for
mocking remote servers.
"""
from contextlib import contextmanager
from threading import Thread
from time import sleep
from wsgiref.simple_server import make_server
import six
from six.moves import reduce
from six.moves.http_client import responses
from six.moves.urllib.request import urlopen
import socket


def _get_str_params(request):
    """ Get parameters from the request. If 'str_params' is available,
    use that, otherwise just use 'params'.
    """
    return request.values


class MockHTTPServer(object):
    """
    Mock HTTP server that can take the place of a remote server for testing
    fetching of remote resources.

    Uses contextmanager to allow easy setup and teardown of the WSGI server in
    a separate thread, eg::

        >>> with MockTestServer().serve() as server_address:
        ...     urlopen(server_address)
        ...

    Subclass this and override __call__ to provide your own WSGI handler function.
    """

    def __call__(self, environ, start_response):
        raise NotImplementedError()

    @contextmanager
    def serve(self, host='localhost', port_range=(8000, 9000)):
        """
        Start an instance of wsgiref.simple_server set up to handle requests in
        a separate daemon thread.
        Return the address of the server eg ('http://localhost:8000').
        This uses context manager to make sure the server is stopped::

            >>> with MockTestServer().serve() as addr:
            ...     print(urlopen('%s/?content=hello+world').read())
            ...
            'hello world'
        """
        for port in range(*port_range):
            try:
                server = make_server(host, port, self)
            except socket.error:
                continue
            break
        else:
            raise Exception("Could not bind to a port in range %r" % (port_range,))

        serving = True

        def _serve_until_stopped():
            while serving:
                server.handle_request()

        thread = Thread(target=_serve_until_stopped)
        thread.daemon = True
        thread.start()
        try:
            yield 'http://%s:%d' % (host, port)
        finally:
            serving = False

            # Call the server to make sure the waiting handle_request()
            # call completes. Set a very small timeout as we don't actually need to
            # wait for a response. We don't care about exceptions here either.
            try:
                urlopen("http://%s:%s/" % (host, port), timeout=0.01)
            except Exception:
                pass

    @classmethod
    def get_content(cls, varspec):
        """
        Return the value of the variable at varspec, which must be in the
        format 'package.module:variable'. If variable is callable, it will be
        called and its return value used.
        """
        modpath, var = varspec.split(':')
        mod = reduce(getattr, modpath.split('.')[1:], __import__(modpath))
        var = reduce(getattr, var.split('.'), mod)
        try:
            return six.ensure_binary(var())
        except TypeError:
            return six.ensure_binary(var)


class MockEchoTestServer(MockHTTPServer):
    """
    WSGI application that echos back the status, headers and
    content passed via the URL, eg:

        a 500 error response: 'http://localhost/?status=500'

        a 200 OK response, returning the function's docstring:
        'http://localhost/?status=200&content-type=text/plain&content_var
        =ckan.tests.lib.test_package_search:test_wsgi_app.__doc__'

    To specify content, use:

        content=string
        content_var=package.module:variable
    """

    def __call__(self, environ, start_response):

        from flask import Request
        request = Request(environ)
        status = int(_get_str_params(request).get('status', '200'))
        if 'content_var' in _get_str_params(request):
            content = _get_str_params(request).get('content_var')
            content = self.get_content(content)
        elif 'content_long' in _get_str_params(request):
            content = '*' * 1000001
        else:
            content = _get_str_params(request).get('content', '')
        if 'method' in _get_str_params(request) \
                and request.method.lower() != _get_str_params(request)['method'].lower():
            content = ''
            status = 405

        headers = [
            (str(item[0]), str(item[1]))
            for item in _get_str_params(request).items()
            if item[0] not in ('content', 'status')
        ]
        if 'length' in _get_str_params(request):
            cl = str(_get_str_params(request).get('length'))
            headers += [('Content-Length', cl)]
        elif content and 'no-content-length' not in _get_str_params(request):
            # Python 2 with old WebOb wants bytes,
            # Python 3 with new WebOb wants text,
            # so both want 'str'
            headers += [('Content-Length', str(len(content)))]
        start_response(
            '%d %s' % (status, responses[status]),
            headers
        )
        return [six.ensure_binary(content)]


class MockTimeoutTestServer(MockHTTPServer):
    """
    Sleeps ``timeout`` seconds before responding. Make sure that your timeout value is
    less than this to check handling timeout conditions.
    """
    def __init__(self, timeout):
        super(MockTimeoutTestServer, self).__init__()
        self.timeout = timeout

    def __call__(self, environ, start_response):
        # Sleep until self.timeout or the parent thread finishes
        sleep(self.timeout)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return ['xyz']
