from __future__ import absolute_import

import itertools

from .base import TestCase
from ..github import Github, GhIssue, \
    GhRepoPulls, GhPull, GhPullComments, GhPullComment


class TestGithubPulls(TestCase):

    def test_repo_pulls(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/pulls",
                     response_body='[ { "number": 1, "state": "open"} ]'),
                dict(urlpath="/repos/octocat/Hello-World/pulls",
                     params=dict(state="closed"),
                     response_body='[ { "number": 2, "state": "closed" } ]'),
                dict(urlpath="/repos/octocat/Hello-World/pulls",
                     response_body='[ { "number": 1, "state": "open"} ]'),
                dict(urlpath="/repos/octocat/Hello-World/pulls",
                     params=dict(state="closed"),
                     response_body='[ { "number": 2, "state": "closed" } ]')]):
            repo = Github()["repos"]["octocat"]["Hello-World"]
            pulls = repo["pulls"]
            self.assertTrue(isinstance(pulls, GhRepoPulls))
            self.assertEqual(pulls._user, "octocat")
            self.assertEqual(pulls._repo, "Hello-World")

            self.assertTrue(len(pulls) == 2)
            self.assertEqual(pulls.keys(), [1, 2])

        with self.request_override([
                dict(urlpath="/repos/octocat/Hello-World/pulls",
                     response_body='[ { "number": 1, "state": "open"} ]'),
                dict(urlpath="/repos/octocat/Hello-World/pulls",
                     params=dict(state="closed"),
                     response_body='[ { "number": 2, "state": "closed" } ]'),
                dict(urlpath="/repos/octocat/Hello-World/pulls",
                     params=dict(state="closed"),
                     response_body='[ { "number": 2, "state": "closed" } ]')]):
            self.assertEqual(
                list(x
                     for x, y in pulls.iteritems()
                     if y["state"] == "closed"),
                list(x for x, y in pulls.search(state="closed"))
            )

    def test_pulls_getitem(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/pulls/1",
                     response_body='{ "number": 1 }'),
                dict(urlpath="/repos/octocat/Hello-World/issues/1",
                     response_body='{ "number": 1, "body": "Issue Body" }'),
                dict(urlpath="/repos/octocat/Hello-World/pulls/12",
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }')]):
            pulls = Github()["repos"]["octocat"]["Hello-World"]["pulls"]
            pull = pulls[1]

            self.assertTrue(isinstance(pull, GhPull))
            self.assertEqual(pull["number"], 1)

            issue = pull["issue"]
            self.assertTrue(isinstance(issue, GhIssue))
            self.assertEqual(issue["body"], "Issue Body")

            self.assertRaises(KeyError, lambda: pulls[12])

    def test_pulls_add(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(method="POST",
                     urlpath="/repos/octocat/Hello-World/pulls",
                     data=dict(title="New pull"),
                     response_status="201 Created",
                     response_body='{ "number": 2 }'),
                dict(method="POST",
                     urlpath="/repos/octocat/Hello-World/pulls",
                     data=dict(body="Missing title"),
                     response_status="422 Unprocessable Entity",
                     response_body='{ "message": "Validation Failed" }')]):
            pulls = Github()["repos"]["octocat"]["Hello-World"]["pulls"]

            newpull = pulls.add(title="New pull")
            self.assertTrue(isinstance(newpull, GhPull))
            self.assertEqual(newpull["number"], 2)

            self.assertRaises(ValueError,
                              lambda: pulls.add(body="Missing title"))

    def test_pull_setitem(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/pulls/1",
                     response_body='{ "number": 1,'
                                   '  "body": "Old body" }'),
                dict(method="PATCH",
                     urlpath="/repos/octocat/Hello-World/pulls/1",
                     data=dict(number=1, body="New body"),
                     response_body='{ "number": 1,'
                                   '  "body": "New body" }')]):

            pull = Github()["repos"]["octocat"]["Hello-World"]["pulls"][1]
            pull["body"] = "New body"

        with self.request_override([
                dict(urlpath="/users/ninocat",
                     response_body='{ "login": "ninocat" }'),
                dict(urlpath="/repos/ninocat/Hello-Earth",
                     response_body='{ "name": "Hello-Earth" }'),
                dict(urlpath="/repos/ninocat/Hello-Earth/pulls/1",
                     response_body='{ "number": 1,'
                                   '  "body": "Old body" }'),
                dict(method="PATCH",
                     urlpath="/repos/ninocat/Hello-Earth/pulls/1",
                     data=dict(number=1, body="New body"),
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }')]):
            pull = Github()["repos"]["ninocat"]["Hello-Earth"]["pulls"][1]
            self.assertRaises(ValueError,
                              lambda: pull.__setitem__("body", "New body"))


class TestGithubComments(TestCase):

    def test_comments_iter(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/pulls/1",
                     response_body='{ "number": 1, "state": "open"}'),
                dict(times=3,
                     urlpath="/repos/octocat/Hello-World/pulls/1/comments",
                     response_body='[ { "id": 1, "body": "Foo" },'
                                   '  { "id": 2, "body": "Bar" } ]')]):
            pull = Github()["repos"]["octocat"]["Hello-World"]["pulls"][1]
            comments = pull["comments"]

            self.assertTrue(isinstance(comments, GhPullComments))

            # list(comments) calls on __iter__ and __len__, resulting
            # in two separate requests
            self.assertEqual(comments.keys(), [1, 2])

            values = list(comments.itervalues())
            self.assertTrue(isinstance(values[0], GhPullComment))
            self.assertEqual([v["body"] for v in values],
                             ["Foo", "Bar"])

            comment2 = next(
                itertools.dropwhile(lambda x: x[0] != 2,
                                    comments.iteritems()))
            self.assertTrue(isinstance(comment2[1], GhPullComment))
            self.assertEqual(comment2[1]["body"], "Bar")

    def test_comments_getitem(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/pulls/1",
                     response_body='{ "number": 1, "state": "open"}'),
                dict(urlpath="/repos/octocat/Hello-World/pulls/comments/1",
                     response_body='{ "id": 1, "body": "Foo" }'),
                dict(urlpath="/repos/octocat/Hello-World/pulls/comments/12",
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }'),
                dict(urlpath="/repos/octocat/Hello-World/pulls/comments/2",
                     response_body='{ "id": 2, "body": "Bar" }')]):

            repo = Github()["repos"]["octocat"]["Hello-World"]
            pull = repo["pulls"][1]

            comment = pull["comments"][1]
            self.assertTrue(isinstance(comment, GhPullComment))
            self.assertEqual(comment["body"], "Foo")

            self.assertRaises(KeyError, lambda: pull["comments"][12])

            self.assertEqual(repo["pullcomments"][2]["body"], "Bar")

    def test_comments_add(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/pulls/1",
                     response_body='{ "number": 1, "state": "open"}'),
                dict(method="POST",
                     urlpath="/repos/octocat/Hello-World/pulls/1/comments",
                     data=dict(body="Foo"),
                     response_status="201 Created",
                     response_body='{ "id": 3, "body": "Foo" }')]):
            pull = Github()["repos"]["octocat"]["Hello-World"]["pulls"][1]
            comments = pull["comments"]

            comment = comments.add(body="Foo")
            self.assertTrue(isinstance(comment, GhPullComment))
            self.assertEqual(comment["body"], "Foo")
            self.assertEqual(comment["id"], 3)

            self.assertRaises(ValueError, lambda: comments.add())

    def test_comment_setitem(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/repos/octocat/Hello-World",
                     response_body='{ "name": "Hello-World" }'),
                dict(urlpath="/repos/octocat/Hello-World/pulls/1",
                     response_body='{ "number": 1, "state": "open" }'),
                dict(urlpath="/repos/octocat/Hello-World/pulls/comments/1",
                     response_body='{ "id": 1, "body": "Old body" }'),
                dict(method="PATCH",
                     urlpath="/repos/octocat/Hello-World/pulls/comments/1",
                     data=dict(id=1, body="New body"),
                     response_body='{ "id": 1,'
                                   '  "body": "New body" }')]):

            pull = Github()["repos"]["octocat"]["Hello-World"]["pulls"][1]
            comment = pull["comments"][1]
            comment["body"] = "New body"

        with self.request_override([
                dict(urlpath="/users/ninocat",
                     response_body='{ "login": "ninocat" }'),
                dict(urlpath="/repos/ninocat/Hello-Earth",
                     response_body='{ "name": "Hello-Earth" }'),
                dict(urlpath="/repos/ninocat/Hello-Earth/pulls/1",
                     response_body='{ "number": 1, "state": "open" }'),
                dict(urlpath="/repos/ninocat/Hello-Earth/pulls/comments/1",
                     response_body='{ "id": 1, "body": "Old body" }'),
                dict(method="PATCH",
                     urlpath="/repos/ninocat/Hello-Earth/pulls/comments/1",
                     data=dict(id=1, body="New body"),
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }')]):
            pull = Github()["repos"]["ninocat"]["Hello-Earth"]["pulls"][1]
            comment = pull["comments"][1]
            self.assertRaises(ValueError,
                              lambda: comment.__setitem__("body", "New body"))
