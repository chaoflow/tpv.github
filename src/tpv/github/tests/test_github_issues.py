from __future__ import absolute_import

import itertools

from .base import TestCase
from ..github import Github, GhRepoIssues, GhIssue, GhIssueComments, GhComment


class TestGithubIssues(TestCase):

    def test_repo_issues(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/issues",
                     response_body='[ { "number": 1, "state": "open"} ]'),
                dict(urlpath="/repos/octocat/Hello-World/issues",
                     params=dict(state="closed"),
                     response_body='[ { "number": 2, "state": "closed" } ]'),
                dict(urlpath="/repos/octocat/Hello-World/issues",
                     response_body='[ { "number": 1, "state": "open"} ]'),
                dict(urlpath="/repos/octocat/Hello-World/issues",
                     params=dict(state="closed"),
                     response_body='[ { "number": 2, "state": "closed" } ]')]):
            repo = Github()["repos"]["octocat"]["Hello-World"]
            issues = repo["issues"]
            self.assertTrue(isinstance(issues, GhRepoIssues))
            self.assertEqual(issues._user, "octocat")
            self.assertEqual(issues._repo, "Hello-World")

            self.assertTrue(len(issues) == 2)
            self.assertEqual(issues.keys(), [1, 2])

        with self.request_override([
                dict(urlpath="/repos/octocat/Hello-World/issues",
                     response_body='[ { "number": 1, "state": "open"} ]'),
                dict(urlpath="/repos/octocat/Hello-World/issues",
                     params=dict(state="closed"),
                     response_body='[ { "number": 2, "state": "closed" } ]'),
                dict(urlpath="/repos/octocat/Hello-World/issues",
                     params=dict(state="closed"),
                     response_body='[ { "number": 2, "state": "closed" } ]')]):
            self.assertEqual(
                list(x
                     for x, y in issues.iteritems()
                     if y["state"] == "closed"),
                list(x for x, y in issues.search(state="closed"))
            )

    def test_issues_getitem(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/issues/1",
                     response_body='{ "number": 1 }'),
                dict(urlpath="/repos/octocat/Hello-World/issues/12",
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }')]):
            issues = Github()["repos"]["octocat"]["Hello-World"]["issues"]

            self.assertEquals(issues[1]["number"], 1)
            self.assertRaises(KeyError, lambda: issues[12])

    def test_issues_add(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(method="POST",
                     urlpath="/repos/octocat/Hello-World/issues",
                     data=dict(title="New issue"),
                     response_status="201 Created",
                     response_body='{ "number": 2 }'),
                dict(method="POST",
                     urlpath="/repos/octocat/Hello-World/issues",
                     data=dict(body="Missing title"),
                     response_status="422 Unprocessable Entity",
                     response_body='{ "message": "Validation Failed" }')]):
            issues = Github()["repos"]["octocat"]["Hello-World"]["issues"]

            newissue = issues.add(title="New issue")
            self.assertTrue(isinstance(newissue, GhIssue))
            self.assertEqual(newissue["number"], 2)

            self.assertRaises(ValueError,
                              lambda: issues.add(body="Missing title"))

    def test_issue_setitem(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/issues/1",
                     response_body='{ "number": 1,'
                                   '  "body": "Old body" }'),
                dict(method="PATCH",
                     urlpath="/repos/octocat/Hello-World/issues/1",
                     data=dict(number=1, body="New body"),
                     response_body='{ "number": 1,'
                                   '  "body": "New body" }')]):

            issue = Github()["repos"]["octocat"]["Hello-World"]["issues"][1]
            issue["body"] = "New body"

        with self.request_override([
                dict(urlpath="/users/ninocat",
                     response_body='{ "login": "ninocat" }'),
                dict(urlpath="/repos/ninocat/Hello-Earth",
                     response_body='{ "name": "Hello-Earth" }'),
                dict(urlpath="/repos/ninocat/Hello-Earth/issues/1",
                     response_body='{ "number": 1,'
                                   '  "body": "Old body" }'),
                dict(method="PATCH",
                     urlpath="/repos/ninocat/Hello-Earth/issues/1",
                     data=dict(number=1, body="New body"),
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }')]):
            issue = Github()["repos"]["ninocat"]["Hello-Earth"]["issues"][1]
            self.assertRaises(ValueError,
                              lambda: issue.__setitem__("body", "New body"))
