from __future__ import absolute_import

import unittest

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
