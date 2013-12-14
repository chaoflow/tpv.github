from __future__ import absolute_import

from .base import TestCase
from ..github import github_request_paginated


class TestGithub(TestCase):
    def test_github_request_paginated(self):
        with self.request_override([
                dict(urlpath="/user/repos?per_page=2",
                     response_extra_headers=dict(
                         Link='<https://api.github.com/user/repos?page=2&per_page=2>; rel="next", '
                              '<https://api.github.com/user/repos?page=2&per_page=2>; rel="last"'),
                     response_body='[ {"name": "Hello-World"},'
                                   '  {"name": "Hello-Earth"} ]'),
                dict(urlpath="/user/repos?page=2&per_page=2",
                     response_extra_headers=dict(
                         Link='<https://api.github.com/user/repos?page=1&per_page=2>; rel="prev", '
                              '<https://api.github.com/user/repos?page=2&per_page=2>; rel="last"'),
                     response_body='[ {"name": "Hello-Moon"} ]')]):
            repos = github_request_paginated("GET",
                                             "/user/repos?per_page=2")
            self.assertTrue(len(list(repos)) == 3)
