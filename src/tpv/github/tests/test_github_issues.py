from __future__ import absolute_import

import itertools

from .base import TestCase
from ..github import Github, GhRepoIssues, GhIssue, GhIssueComments, GhComment


class TestGithubIssues(TestCase):

    def test_repo_issues(self):
        with self.request_override([
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
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


class TestGithubComments(TestCase):

    def test_comments_iter(self):
        with self.request_override([
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/issues/1",
                     response_body='{ "number": 1, "state": "open"}'),
                dict(times=2,
                     urlpath="/repos/octocat/Hello-World/issues/1/comments",
                     response_body='[ { "id": 1, "body": "Foo" },'
                                   '  { "id": 2, "body": "Bar" } ]')]):
            issue = Github()["repos"]["octocat"]["Hello-World"]["issues"][1]
            comments = issue["comments"]

            self.assertTrue(isinstance(comments, GhIssueComments))

            # list(comments) calls on __iter__ and __len__, resulting
            # in two separate requests
            self.assertEqual(comments.keys(), [1, 2])

            values = list(comments.itervalues())
            self.assertTrue(isinstance(values[0], GhComment))
            self.assertEqual([v["body"] for v in values],
                             ["Foo", "Bar"])

            comment2 = next(
                itertools.dropwhile(lambda x: x[0] != 2,
                                    comments.iteritems()))
            self.assertTrue(isinstance(comment2[1], GhComment))
            self.assertEqual(comment2[1]["body"], "Bar")

    def test_comments_getitem(self):
        with self.request_override([
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/issues/1",
                     response_body='{ "number": 1, "state": "open"}'),
                dict(urlpath="/repos/octocat/Hello-World/issues/comments/1",
                     response_body='{ "id": 1, "body": "Foo" }'),
                dict(urlpath="/repos/octocat/Hello-World/issues/comments/12",
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }'),
                dict(urlpath="/repos/octocat/Hello-World/issues/comments/2",
                     response_body='{ "id": 2, "body": "Bar" }')]):

            repo = Github()["repos"]["octocat"]["Hello-World"]
            issue = repo["issues"][1]

            comment = issue["comments"][1]
            self.assertTrue(isinstance(comment, GhComment))
            self.assertEqual(comment["body"], "Foo")

            self.assertRaises(KeyError, lambda: issue["comments"][12])

            self.assertEqual(repo["comments"][2]["body"], "Bar")

    def test_comments_add(self):
        with self.request_override([
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/issues/1",
                     response_body='{ "number": 1, "state": "open"}'),
                dict(method="POST",
                     urlpath="/repos/octocat/Hello-World/issues/1/comments",
                     data=dict(body="Foo"),
                     response_status="201 Created",
                     response_body='{ "id": 3, "body": "Foo" }')]):
            issue = Github()["repos"]["octocat"]["Hello-World"]["issues"][1]
            comments = issue["comments"]

            comment = comments.add(body="Foo")
            self.assertTrue(isinstance(comment, GhComment))
            self.assertEqual(comment["body"], "Foo")
            self.assertEqual(comment["id"], 3)

            self.assertRaises(ValueError, lambda: comments.add())

    def test_comment_setitem(self):
        with self.request_override([
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/issues/1",
                     response_body='{ "number": 1, "state": "open" }'),
                dict(urlpath="/repos/octocat/Hello-World/issues/comments/1",
                     response_body='{ "id": 1, "body": "Old body" }'),
                dict(method="PATCH",
                     urlpath="/repos/octocat/Hello-World/issues/comments/1",
                     data=dict(id=1, body="New body"),
                     response_body='{ "id": 1,'
                                   '  "body": "New body" }')]):

            issue = Github()["repos"]["octocat"]["Hello-World"]["issues"][1]
            comment = issue["comments"][1]
            comment["body"] = "New body"

        with self.request_override([
                dict(urlpath="/repos/ninocat/Hello-Earth",
                     response_body='{ "name": "Hello-Earth" }'),
                dict(urlpath="/repos/ninocat/Hello-Earth/issues/1",
                     response_body='{ "number": 1, "state": "open" }'),
                dict(urlpath="/repos/ninocat/Hello-Earth/issues/comments/1",
                     response_body='{ "id": 1, "body": "Old body" }'),
                dict(method="PATCH",
                     urlpath="/repos/ninocat/Hello-Earth/issues/comments/1",
                     data=dict(id=1, body="New body"),
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }')]):
            issue = Github()["repos"]["ninocat"]["Hello-Earth"]["issues"][1]
            comment = issue["comments"][1]
            self.assertRaises(ValueError,
                              lambda: comment.__setitem__("body", "New body"))
