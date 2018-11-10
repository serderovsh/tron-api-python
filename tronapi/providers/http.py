# --------------------------------------------------------------------
# Copyright (c) iEXBase. All rights reserved.
# Licensed under the MIT License.
# See License.txt in the project root for license information.
# --------------------------------------------------------------------

from collections import namedtuple

from eth_utils import to_dict
from requests import Session
from requests.exceptions import ConnectionError

from tronapi.providers.base import BaseProvider
from ..exceptions import HTTP_EXCEPTIONS, TransportError, HttpError

HttpResponse = namedtuple('HttpResponse', ('status_code', 'headers', 'data'))


class HttpProvider(BaseProvider):
    """A Connection object to make HTTP requests to a particular node."""

    def __init__(self, node_url, request_kwargs=None):
        """Initializes a :class:`~tronapi.providers.http.HttpProvider`
        instance.

         Args:
            node_url (str):  Url of the node to connect to.
            request_kwargs (dict): Optional params to send with each request.

        """

        self.node_url = node_url.rstrip('/')
        self._request_kwargs = request_kwargs or {}
        self.session = Session()

    @to_dict
    def get_request_kwargs(self):
        """Header settings"""
        if 'headers' not in self._request_kwargs:
            yield 'headers', self._http_default_headers()
        for key, value in self._request_kwargs.items():
            yield key, value

    def request(self, path, json=None, params=None, method=None):
        """Performs an HTTP request with the given parameters.

           Args:
               path (str): API endpoint path (e.g.: ``'/transactions'``).
               json (dict): JSON data to send along with the request.
               params (dict): Dictionary of URL (query) parameters.
               method (str): HTTP method (e.g.: ``'GET'``).

        """
        try:
            response = self._request(
                method=method,
                url=self.node_url + path if path else self.node_url,
                json=json,
                params=params,
                **self.get_request_kwargs(),
            )
        except ConnectionError as err:
            raise err

        return response.data

    def is_connected(self) -> bool:
        """Checking the connection from the connected node

        Returns:
            bool: True if successful, False otherwise.

        """
        response = self.request(path=self.status_page, method='get')
        if 'blockID' in response or response == 'OK':
            return True

        return False

    def _request(self, **kwargs):

        kwargs.setdefault('timeout', 60)
        response = self.session.request(**kwargs)
        text = response.text
        try:
            json = response.json()
        except ValueError:
            json = None

        if not (200 <= response.status_code < 300):
            exc_cls = HTTP_EXCEPTIONS.get(response.status_code, TransportError)
            raise exc_cls(response.status_code, text, json, kwargs.get('url'))

        data = json if json is not None else text
        return HttpResponse(response.status_code, response.headers, data)
