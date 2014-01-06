from __future__ import absolute_import

import unittest
import tempfile
import os

from ..github_base import RecursiveConfigParser


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        with open(os.path.join(self.dir, ".ghconfig"), "w") as f:
            f.write('''
[test]
foo = 1
bar = 1
            ''')

        os.mkdir(os.path.join(self.dir, "a"))
        with open(os.path.join(self.dir, "a", ".ghconfig"), "w") as f:
            f.write('''
[test]
bar = 2
baz = 2
            ''')

        os.mkdir(os.path.join(self.dir, "a", "b"))
        with open(os.path.join(self.dir, "a", "b", ".ghconfig"), "w") as f:
            f.write('''
[test]
baz = 3
xyz = 3
            ''')

        self.oldpath = os.getcwd()
        os.chdir(os.path.join(self.dir, "a", "b"))

        self.oldexpanduser = os.path.expanduser
        os.path.expanduser = lambda path: path.replace("~", self.dir)


    def tearDown(self):
        os.chdir(self.oldpath)
        os.path.expanduser = self.oldexpanduser

    def test_recursive_config(self):
        r = RecursiveConfigParser()
        r.read(".ghconfig")

        self.assertEqual(r.get("test", "foo"), "1")
        self.assertEqual(r.get("test", "bar"), "2")
        self.assertEqual(r.get("test", "baz"), "3")
        self.assertEqual(r.get("test", "xyz"), "3")
