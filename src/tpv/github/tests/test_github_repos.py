from __future__ import absolute_import

import itertools

from .base import TestCase
from ..github import Github, GhUserRepos, GhRepo


class TestGithubRepos(TestCase):

    def test_repos_getitem(self):
        github = Github()

        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name":"Hello-World",'
                                   '  "full_name":"octocat/Hello-World" }'),
                dict(urlpath="/repos/octocat/Not-Existant",
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }')]):
            repos = github["repos"]["octocat"]

            self.assertTrue(isinstance(repos, GhUserRepos))

            repo = repos["Hello-World"]
            self.assertTrue(isinstance(repo, GhRepo))
            self.assertEqual(repo["full_name"], "octocat/Hello-World")

            self.assertRaises(KeyError, lambda: repos["Not-Existant"])

    def test_repos_add(self):
        github = Github()

        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(method="POST", urlpath="/user/repos",
                     data=dict(name="Hello-World",
                               description="This is your first repo"),
                     response_status="201 Created",
                     response_body='{ "name": "Hello-World" }')]):
            repos = github["repos"]["octocat"]

            self.assertTrue(isinstance(repos, GhUserRepos))

            repo = repos.add(name="Hello-World",
                             description="This is your first repo")
            self.assertTrue(isinstance(repo, GhRepo))
            self.assertEqual(repo["name"], "Hello-World")

        with self.request_override([
                dict(times=2,
                     urlpath="/users/ninocat",
                     response_body='{ "login": "ninocat",'
                                   '  "type": "User" }'),
                dict(times=2,
                     urlpath="/users/foreignorg",
                     response_body='{ "login": "foreignorg",'
                                   '  "type": "Organization" }'),
                dict(method="POST", urlpath="/orgs/foreignorg/repos",
                     data=dict(name="Hello"),
                     response_status="403 Forbidden",
                     response_body='{ "message": "Must be an owner or admin of Organization." }')]):

            otheruser_repos = github["repos"]["ninocat"]
            self.assertRaises(ValueError,
                              lambda: otheruser_repos.add(name="Hello-Earth"))

            foreignorg_repos = github["repos"]["foreignorg"]
            self.assertRaises(ValueError,
                              lambda: foreignorg_repos.add(name="Hello"))

    def test_repos_delitem(self):
        github = Github()

        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(method="DELETE", urlpath="/repos/octocat/Hello-World",
                     response_status="204 No Content",
                     response_body='null')]):
            repos = github["repos"]["octocat"]

            self.assertTrue(isinstance(repos, GhUserRepos))
            del repos["Hello-World"]

    def test_user_repos_iter(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(times=2,
                     urlpath="/users/octocat/repos",
                     response_body='''
[
  {
    "name": "Hello-World",
    "full_name": "octocat/Hello-World"
  },
  {
    "name": "Hello-Earth",
    "full_name": "octocat/Hello-Earth"
  }
]
                     ''')]):
            repos = Github()["repos"]["octocat"]

            self.assertTrue(isinstance(repos, GhUserRepos))
            self.assertEqual(set(repos), set(("Hello-World", "Hello-Earth")))

            values = list(repos.itervalues())
            self.assertTrue(isinstance(values[0], GhRepo))
            self.assertEqual(set(v["full_name"] for v in values),
                             set(("octocat/Hello-World",
                                  "octocat/Hello-Earth")))

            helloearth = next(
                itertools.dropwhile(lambda x: x[0] != "Hello-Earth",
                                    repos.iteritems()))
            self.assertTrue(isinstance(helloearth[1], GhRepo))
            self.assertEqual(helloearth[1]["full_name"], "octocat/Hello-Earth")


class TestGithubRepo(TestCase):

    def test_repo_setitem(self):
        github = Github()

        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name":"Hello-World",'
                                   '  "full_name":"octocat/Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     method="PATCH",
                     data=dict(name="Hello-World",
                               description="foo"),
                     response_body='{ "name":"Hello-World" }'),
                dict(urlpath="/users/ninocat",
                     response_body='{ "login": "ninocat" }'),
                dict(urlpath="/repos/ninocat/Hello-Earth",
                     response_body='{ "name":"Hello-Earth" }'),
                dict(urlpath="/repos/ninocat/Hello-Earth",
                     method="PATCH",
                     data=dict(name="Hello-Earth",
                               description="foo"),
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }')]):
            repos = github["repos"]["octocat"]

            self.assertTrue(isinstance(repos, GhUserRepos))

            repo = repos["Hello-World"]
            repo['description'] = "foo"

            foreign_repo = github["repos"]["ninocat"]["Hello-Earth"]
            self.assertRaises(ValueError,
                              lambda: foreign_repo.__setitem__("description",
                                                          "foo"))
