from __future__ import absolute_import

import itertools

from .base import TestCase
from ..github import \
    Github, GhOrgs, GhUserOrgs, GhOrg, GhOrgTeams, GhOrgMembers, GhMember, \
    GhTeam, GhTeamMembers, GhTeamRepos, GhResource


class TestGithubOrgs(TestCase):

    def test_orgs(self):
        orgs = Github()["orgs"]
        self.assertTrue(isinstance(orgs, GhOrgs))

        with self.request_override([
                dict(urlpath="/user",
                     response_body='{ "login": "octocat" }'),
                dict(urlpath="/user/orgs",
                     response_body='[ { "login": "github" } ]')]):
            user_orgs = Github()["users"]["octocat"]["orgs"]
            self.assertTrue(isinstance(user_orgs, GhUserOrgs))
            self.assertEqual(["github"], user_orgs.keys())

    def test_org_getitem(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github",'
                                   '  "type": "Organization" }')]):

            org = Github()["orgs"]["github"]
            self.assertTrue(isinstance(org, GhOrg))
            self.assertEqual(org["login"], "github")
            self.assertEqual(org["type"], "Organization")

    def test_org_setitem(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(method="PATCH",
                     urlpath="/orgs/github",
                     data=dict(name="new name"),
                     response_body='{ "name": "new name" }')]):
            org = Github()["orgs"]["github"]
            org["name"] = "new name"


class TestGithubOrgTeams(TestCase):
    def test_team_iter(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(times=2,
                     urlpath="/orgs/github/teams",
                     response_body='[ { "id": 1, "name": "Owners" },'
                                   '  { "id": 2, "name": "dev" } ]')]):
            teams = Github()["orgs"]["github"]["teams"]

            self.assertTrue(isinstance(teams, GhOrgTeams))

            # list(comments) calls on __iter__ and __len__, resulting
            # in two separate requests
            self.assertEqual(teams.keys(), [1, 2])

            values = list(teams.itervalues())
            self.assertTrue(isinstance(values[0], GhTeam))
            self.assertEqual([v["name"] for v in values],
                             ["Owners", "dev"])

            team2 = next(
                itertools.dropwhile(lambda x: x[0] != 2,
                                    teams.iteritems()))
            self.assertTrue(isinstance(team2[1], GhTeam))
            self.assertEqual(team2[1]["name"], "dev")

            with self.request_override([
                dict(urlpath="/orgs/foreign",
                     response_body='{ "login": "foreign" }'),
                dict(urlpath="/orgs/foreign/teams",
                     response_status="403 Forbidden",
                     response_body='{  "message": "Must have admin ..." }')]):
                org = Github()["orgs"]["foreign"]
                self.assertRaises(RuntimeError,
                                  lambda: org["teams"].keys())

    def test_team_getitem(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(urlpath="/teams/1",
                     response_body='{ "id": 1 }'),
                dict(urlpath="/teams/3",
                     response_status="404 Not Found",
                     response_body='{ "message": "Not Found" }')]):
            teams = Github()["orgs"]["github"]["teams"]

            self.assertEquals(teams[1]["id"], 1)
            self.assertRaises(KeyError, lambda: teams[3])

    def test_team_add(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(method="POST",
                     urlpath="/orgs/github/teams",
                     data=dict(name="Foo"),
                     response_status="201 Created",
                     response_body='{ "id": 3, "name": "Foo" }')]):

            teams = Github()["orgs"]["github"]["teams"]

            team = teams.add(name="Foo")
            self.assertTrue(isinstance(team, GhTeam))
            self.assertEqual(team["name"], "Foo")
            self.assertEqual(team["id"], 3)

            self.assertRaises(ValueError, lambda: teams.add())

    def test_team_setitem(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(urlpath="/teams/1",
                     response_body='{ "id": 1, "name": "Owners" }'),
                dict(method="PATCH",
                     urlpath="/teams/1",
                     data=dict(id=1, name="New name"),
                     response_body='{ "id": 1,'
                                   '  "name": "New name" }')]):

            team = Github()["orgs"]["github"]["teams"][1]
            team["name"] = "New name"

    def test_team_delitem(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(method="DELETE",
                     urlpath="/teams/2",
                     response_status="204 No Content",
                     response_body='null')]):

            teams = Github()["orgs"]["github"]["teams"]
            del teams[2]


class TestGithubOrgTeamMembers(TestCase):
    def test_team_members_iter(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(urlpath="/teams/1",
                     response_body='{ "id": 1, "name": "Owners" }'),
                dict(times=2,
                     urlpath="/teams/1/members",
                     response_body='[ { "id": 1, "login": "octocat" },'
                                   '  { "id": 2, "login": "ninocat" } ]')]):
            members = Github()["orgs"]["github"]["teams"][1]["members"]

            self.assertTrue(isinstance(members, GhTeamMembers))

            # list(comments) calls on __iter__ and __len__, resulting
            # in two separate requests
            self.assertEqual(members.keys(), ["octocat", "ninocat"])

            values = list(members.itervalues())
            self.assertTrue(isinstance(values[0], GhMember))
            self.assertEqual([v["login"] for v in values],
                             ["octocat", "ninocat"])

            member2 = next(
                itertools.dropwhile(lambda x: x[0] != "ninocat",
                                    members.iteritems()))
            self.assertTrue(isinstance(member2[1], GhMember))
            self.assertEqual(member2[1]["login"], "ninocat")

    def test_team_member_add(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(urlpath="/teams/1",
                     response_body='{ "id": "1" }'),
                dict(method="PUT",
                     urlpath="/teams/1/members/ninocat",
                     data=dict(login="ninocat"),
                     response_status="204 No Content",
                     response_body='null')]):

            members = Github()["orgs"]["github"]["teams"][1]["members"]
            members.add(login="ninocat")

            self.assertRaises(ValueError, lambda: members.add())

    def test_team_members_delitem(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(urlpath="/teams/1",
                     response_body='{ "id": "1" }'),
                dict(method="DELETE",
                     urlpath="/teams/1/members/ninocat",
                     response_status="204 No Content",
                     response_body='null')]):

            members = Github()["orgs"]["github"]["teams"][1]["members"]
            del members["ninocat"]


class TestGithubOrgTeamRepos(TestCase):
    def test_team_repos_iter(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(urlpath="/teams/1",
                     response_body='{ "id": 1, "name": "Owners" }'),
                dict(times=2,
                     urlpath="/teams/1/repos",
                     response_body='[ { "id": 1, "name": "Hello-World" },'
                                   '  { "id": 2, "name": "Hello-Earth" } ]')]):
            repos = Github()["orgs"]["github"]["teams"][1]["repos"]

            self.assertTrue(isinstance(repos, GhTeamRepos))

            # list(comments) calls on __iter__ and __len__, resulting
            # in two separate requests
            self.assertEqual(repos.keys(), ["Hello-World", "Hello-Earth"])

            values = list(repos.itervalues())
            self.assertTrue(isinstance(values[0], GhResource))
            self.assertEqual([v["name"] for v in values],
                             ["Hello-World", "Hello-Earth"])

            repo2 = next(
                itertools.dropwhile(lambda x: x[0] != "Hello-Earth",
                                    repos.iteritems()))
            self.assertTrue(isinstance(repo2[1], GhResource))
            self.assertEqual(repo2[1]["name"], "Hello-Earth")

    def test_team_repo_add(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(urlpath="/teams/1",
                     response_body='{ "id": "1" }'),
                dict(method="PUT",
                     urlpath="/teams/1/repos/github/Hello-Moon",
                     data=dict(name="github/Hello-Moon"),
                     response_status="204 No Content",
                     response_body='null'),
                dict(method="PUT",
                     urlpath="/teams/1/repos/foreign/Hello-Saturn",
                     data=dict(name="foreign/Hello-Saturn"),
                     response_status="422 Unprocessable Entity",
                     response_body='{ "message": "Validation Failed" }')]):

            repos = Github()["orgs"]["github"]["teams"][1]["repos"]
            repos.add(name="github/Hello-Moon")

            self.assertRaises(ValueError,
                              lambda: repos.add(name="foreign/Hello-Saturn"))
            self.assertRaises(ValueError, lambda: repos.add())

    def test_team_repos_delitem(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(urlpath="/teams/1",
                     response_body='{ "id": "1" }'),
                dict(method="DELETE",
                     urlpath="/teams/1/repos/github/Hello-World",
                     response_status="204 No Content",
                     response_body='null')]):

            repos = Github()["orgs"]["github"]["teams"][1]["repos"]
            del repos["github/Hello-World"]


class TestGithubOrgMembers(TestCase):
    def test_org_members_iter(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(times=2,
                     urlpath="/orgs/github/members",
                     response_body='[ { "id": 1, "login": "octocat" },'
                                   '  { "id": 2, "login": "ninocat" } ]')]):
            members = Github()["orgs"]["github"]["members"]

            self.assertTrue(isinstance(members, GhOrgMembers))

            # list(comments) calls on __iter__ and __len__, resulting
            # in two separate requests
            self.assertEqual(members.keys(), ["octocat", "ninocat"])

            values = list(members.itervalues())
            self.assertTrue(isinstance(values[0], GhMember))
            self.assertEqual([v["login"] for v in values],
                             ["octocat", "ninocat"])

            repo2 = next(
                itertools.dropwhile(lambda x: x[0] != "ninocat",
                                    members.iteritems()))
            self.assertTrue(isinstance(repo2[1], GhResource))
            self.assertEqual(repo2[1]["login"], "ninocat")

    def test_org_members_delitem(self):
        with self.request_override([
                dict(urlpath="/orgs/github",
                     response_body='{ "login": "github" }'),
                dict(method="DELETE",
                     urlpath="/orgs/github/members/octocat",
                     response_status="204 No Content",
                     response_body='null')]):

            members = Github()["orgs"]["github"]["members"]
            del members["octocat"]
