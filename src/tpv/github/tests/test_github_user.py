from __future__ import absolute_import

from .base import TestCase
from ..github import Github


class TestGithubUser(TestCase):

    def test_user_getitem(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat",'
                                   '  "type": "User",'
                                   '  "location": "Berlin" }'),
                dict(urlpath="/users/non-existant",
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }')]):
            users = Github()["users"]
            user = users["octocat"]
            self.assertEqual(user["login"], "octocat")
            self.assertEqual(user["type"], "User")
            self.assertEqual(user["location"], "Berlin")

            self.assertRaises(KeyError, lambda: users["non-existant"])

    def test_user_setitem(self):
        with self.request_override([
                dict(urlpath="/users/octocat",
                     response_body='{ "login": "octocat" }'),
                dict(method="PATCH", urlpath="/user",
                     data=dict(bio="Foo"),
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/users/ninocat",
                     response_body='{ "login": "ninocat" }'),
                dict(method="PATCH", urlpath="/users/ninocat",
                     data=dict(bio="Foo"),
                     # not the same as authorized_user, thus "Not Found"
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }')]):

            user = Github()["users"]["octocat"]
            user["bio"] = "Foo"

            user = Github()["users"]["ninocat"]
            self.assertRaises(ValueError,
                              lambda: user.__setitem__("bio", "Foo"))
