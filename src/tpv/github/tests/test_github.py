from __future__ import absolute_import

import unittest
import itertools

from ..github import *


class TestGithub(unittest.TestCase):
    def test_repos(self):
        github = Github()
        nixosrepos = github["repos"]["nixos"]
        self.assertTrue(isinstance(nixosrepos, GhOwnerRepos))

        nixpkgsrepo = nixosrepos["nixpkgs"]
        self.assertTrue(isinstance(nixpkgsrepo, GhRepo))
        self.assertEqual(nixpkgsrepo["full_name"], "NixOS/nixpkgs")

        issues = nixpkgsrepo["issues"]
        self.assertTrue(isinstance(issues, GhRepoIssues))
        self.assertEqual(issues._owner, "nixos")
        self.assertEqual(issues._repo, "nixpkgs")

    def test_owner_repos_enumeration(self):
        nixosreponames = ("nixpkgs", "nixops", "nix", "hydra")

        nixosrepos = Github()["repos"]["nixos"]
        self.assertTrue(isinstance(nixosrepos, GhOwnerRepos))
        self.assertTrue(set(nixosrepos).issuperset(nixosreponames))

        values = nixosrepos.itervalues()
        self.assertTrue(isinstance(next(values), GhRepo))
        self.assertTrue(set(v["full_name"] for v in values)
                        .issuperset(("NixOS/" + x for x in nixosreponames)))

        patchelf = next(itertools.dropwhile(lambda x: x[0] != "patchelf",
                                            nixosrepos.iteritems()))
        self.assertTrue(isinstance(patchelf[1], GhRepo))
        self.assertEqual(patchelf[1]["full_name"], "NixOS/patchelf")


    def test_github_request_paginated(self):
        repos = github_request_paginated("GET", "/users/nixos/repos?per_page=2")
        self.assertTrue(len(list(itertools.islice(repos, 5))) == 5)

    def test_issues(self):
        patchelf = Github()["repos"]["nixos"]["patchelf"]
        issues = patchelf["issues"]
        no_of_issues = len(issues)
        self.assertTrue(no_of_issues >= 7)

        open_issues = list(itertools.takewhile(lambda x: x["state"]=="open", issues.itervalues()))
        self.assertTrue(len(open_issues) <= no_of_issues)

    def test_complete_data(self):
        pass
