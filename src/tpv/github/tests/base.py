from __future__ import absolute_import

import unittest
import json
from contextlib import contextmanager

from .. import github_base
from .. import github


class MockRequest(object):
    def __init__(self, status, body, extra_headers=dict()):
        self.status = status
        self.extra_headers = extra_headers
        self.body = json.loads(body)

    @property
    def headers(self):
        return dict(status=self.status, **self.extra_headers)

    def json(self):
        return self.body


class TestCase(unittest.TestCase):
    @contextmanager
    def request_override(self, requests):
        '''A context manager, which monkey patches github_request to mock
    github.
        '''
        def intercept(method, urlpath, data=None, params=None):
            if params == dict():
                params = None

            request = requests.pop(0)
            if request.get("times", 1) > 1:
                request["times"] -= 1
                requests.insert(0, request)

            self.assertEqual(method, request.get("method", "GET"))
            self.assertEqual(urlpath, request["urlpath"])
            self.assertEqual(data, request.get("data"))
            self.assertEqual(params, request.get("params"))

            return MockRequest(request.get("response_status", "200 OK"),
                               request["response_body"],
                               request.get("response_extra_headers", dict()))

        prev_request = github_base.github_request
        prev_authenticated_user = github.authenticated_user

        github_base.github_request = intercept
        github.authenticated_user = lambda: "octocat"

        yield intercept

        github_base.github_request = prev_request
        github.authenticated_user = prev_authenticated_user

        self.assertEqual(len(requests), 0)

    def setUp(self):
        github.Github().clear_cache()

    # def setUp(self):
    #     self.answers = dict()

    #     def intercept(method, urlpath, data=None, params=None):
    #         self.assertTrue((method, urlpath, data, params) in self.answers)
    #         return self.answers[(method, urlpath)]

    #     github.github_request = intercept
