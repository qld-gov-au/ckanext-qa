# encoding: utf-8
""" Some useful functions for interacting with the current request.

Handles both WebOb and Flask request objects.
"""


class RequestHelper():

    def __init__(self, request=None):
        if request:
            self.request = request
        else:
            import ckan.common
            self.request = ckan.common.request

    def get_path(self):
        """ Get the request path, without query string.
        """
        return self.request.path

    def get_method(self):
        """ Get the request method, eg HEAD, GET, POST.
        """
        return self.request.method

    def get_environ(self):
        """ Get the WebOb environment dict.
        """
        return self.request.environ

    def get_cookie(self, field_name, default=None):
        """ Get the value of a cookie, or the default value if not present.
        """
        return self.request.cookies.get(field_name, default)

    def _get_params(self, pylons_attr, flask_attr, field_name=None):
        """ Retrieve a list of all parameters with the specified name
        for the current request.

        If no field name is specified, retrieve the whole parameter object.

        The Flask param attribute will be used if present;
        if not, then the Pylons param attribute will be used.
        """
        if hasattr(self.request, flask_attr):
            param_object = getattr(self.request, flask_attr)
            if field_name:
                return param_object.getlist(field_name)
        else:
            param_object = getattr(self.request, pylons_attr)
            if field_name:
                return param_object.getall(field_name)
        return param_object

    def get_post_params(self, field_name=None):
        """ Retrieve a list of all POST parameters with the specified name
        for the current request.

        If no field name is specified, retrieve the whole parameter object.

        This uses 'request.POST' for Pylons and 'request.form' for Flask.
        """
        return self._get_params('POST', 'form', field_name)

    def get_query_params(self, field_name):
        """ Retrieve a list of all GET parameters with the specified name
        for the current request.

        This uses 'request.GET' for Pylons and 'request.args' for Flask.
        """
        return self._get_params('GET', 'args', field_name)

    def delete_param(self, field_name):
        """ Remove the parameter with the specified name from the current
        request. This requires the request parameters to be mutable.
        """
        for collection_name in ['args', 'form', 'GET', 'POST']:
            collection = getattr(self.request, collection_name, {})
            if field_name in collection:
                del collection[field_name]

    def scoped_attrs(self):
        """ Returns a mutable dictionary of attributes that exist in the
        scope of the current request, and will vanish afterward.
        """
        if 'webob.adhoc_attrs' not in self.request.environ:
            self.request.environ['webob.adhoc_attrs'] = {}
        return self.request.environ['webob.adhoc_attrs']

    def get_first_post_param(self, field_name, default=None):
        """ Retrieve the first POST parameter with the specified name
        for the current request.

        This uses 'request.POST' for Pylons and 'request.form' for Flask.
        """
        return self.get_post_params().get(field_name, default)

    def get_first_query_param(self, field_name, default=None):
        """ Retrieve the first GET parameter with the specified name
        for the current request.

        This uses 'request.GET' for Pylons and 'request.args' for Flask.
        """
        return self.get_query_params().get(field_name, default)
