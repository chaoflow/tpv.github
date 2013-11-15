from requests import request
import os, ConfigParser

from metachao import aspect
from metachao import classtree

URL_BASE = 'https://api.github.com'


# Read in some authentication data from ~/.ghconfig.
# It should contain a section like
#
#   [github]
#   user=<username>
#   token=<personal access token>
#
# where the personal access token can be generated with "Create new
# token" on https://github.com/settings/applications.

config = ConfigParser.ConfigParser()
config.read(os.path.join(os.environ['HOME'], ".ghconfig"))


def github_request(method, urlpath):
    """Request `urlpath` from github using authentication from config

    Arguments:
    - `method`: one of "HEAD", "GET", "POST", "PATCH", "DELETE"
    - `urlpath`: the path part of the request url, i.e. /users/coroa
    """

    return request(method, URL_BASE + urlpath,
                   auth=(config.get("github", "user"),
                         config.get("github", "token")))


class GhRepoIssues(object):
    """The issues of some repository
    """

    def __init__(self, owner, repo):
        """
        Arguments:
        - `owner`:
        - `repo`:
        """
        self._owner = owner
        self._repo = repo


@classtree.instantiate
class GhRepo(classtree.Base):
    """Github repository representation
    """

    def __init__(self, owner, repo, data=None):
        """
        Arguments:
        - `owner`: owner of the repository
        - `repo`: name of the repository
        - `data`: json data of a get request on the url of the repository
        """
        self._owner = owner
        self._repo = repo

        if data is None:
            data = github_request("GET", "/repos/{}/{}".format(owner, repo)).json()
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

GhRepo["issues"] = (GhRepoIssues, "_owner", "_repo")


class GhOwnerRepos(object):
    """Github container for the repositories of owner `owner`
    """

    def __init__(self, owner):
        """
        Arguments:
        - `owner`: Github owner of the represented repositories
        """
        self._owner = owner

    def __getitem__(self, repo):
        """Return the GhRepo object for `repo`

Check if `repo` is a valid repo first.
"""
        # Check if `repo` is a valid repo/user
        req = github_request("GET", "/repos/{}/{}".format(self._owner, repo))
        if "200" not in req.headers["status"]:
            raise KeyError("Repo `{}/{}` does not exist."
                           .format(self._owner, repo))

        # Return GhOwnerRepos object
        return GhRepo(self._owner, repo, req.json())


class GhRepos(object):
    """Github repository container
    """

    def __getitem__(self, owner):
        """Return the GhOwnerRepos object for `owner`

Check if `owner` is a valid owner first.
"""
        # Check if `owner` is a valid owner/user
        if "200" not in github_request("HEAD", "/users/{}".format(owner)).headers["status"]:
            raise KeyError("Owner '{}' does not exist.".format(owner))

        # Return GhOwnerRepos object
        return GhOwnerRepos(owner)


@classtree.instantiate
class Github(classtree.Base):
    def __getitem__(self, key):
        return github_request("GET", "").json()[key]

Github["repos"] = GhRepos
# Github["users"] = GhUsers






# GhRepo["issues"] = GhRepoIssues
# GhRepo["pullrequests"] = GhRepoPullrequests
