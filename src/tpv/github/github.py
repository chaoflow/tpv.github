from requests import request
import os
import ConfigParser
import re
import itertools

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


def merge_dicts(*dicts):
    return dict(itertools.chain(*(d.iteritems() for d in dicts)))


def github_request(method, urlpath, data=None):
    """Request `urlpath` from github using authentication from config

    Arguments:
    - `method`: one of "HEAD", "GET", "POST", "PATCH", "DELETE"
    - `urlpath`: the path part of the request url, i.e. /users/coroa
    """

    return request(method, URL_BASE + urlpath,
                   auth=(config.get("github", "user"),
                         config.get("github", "token")),
                   data=data)


def github_request_paginated(method, urlpath):
    while urlpath:
        req = github_request(method, urlpath)
        for elem in req.json():
            yield elem

        urlpath = None
        if "Link" in req.headers:
            m = re.search('<(https[^>]*)>; rel="next"', req.headers["Link"])
            if m:
                urlpath = m.group(1)[len(URL_BASE):]


def github_request_length(urlpath):
    req = github_request("GET", urlpath + "?per_page=1")
    m = re.search('<https[^>]*[?&]page=(\d+)[^>]*>; rel="last"',
                  req.headers["Link"])
    if m:
        return int(m.group(1))
    else:
        return 0


class GhResource(dict):
    @property
    def url_template(self):
        raise NotImplemented()

    def __init__(self, parent, data = None, **kwargs):
        self._parent = parent
        for k, v in kwargs.iteritems():
            setattr(self, "_" + k, v)

        if data is None:
            data = github_request("GET", self.url_template
                                         .format(**kwargs).json())
        self.merge(data)


class GhIssue(object):
    """Issue of some repository
    """
    def __init__(self, owner, repo, number, data=None):
        """
        Arguments:
        - `owner`:
        - `repo`:
        - `number`:
        - `data`:
        """
        self._owner = owner
        self._repo = repo
        self._number = number

        if data is None:
            data = github_request("GET", "/repos/{}/{}/issues/{}"
                                         .format(owner, repo, number)).json()
        self._data = data

    def iterkeys(self):
        return self._data.iterkeys()
    __iter__ = iterkeys

    def itervalues(self):
        return self._data.itervalues()

    def iteritems(self):
        return self._data.iteritems()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __getitem__(self, key):
        return self._data[key]


class GhRepoIssues(object):
    """The issues of some repository
    """

    def __init__(self, parent):
        """
        Arguments:
        - `ghrepo`: the parent GhRepo instance
        """
        self._owner = parent._owner
        self._repo = parent._repo

    def _get_all_issues(self):
        urlpath = "/repos/{}/{}/issues".format(self._owner, self._repo)
        return itertools.chain(github_request_paginated("GET", urlpath),
                               github_request_paginated("GET", urlpath + "?state=closed"))

    def __len__(self):
        return len(self.keys())

    def iterkeys(self):
        """Enumerate issues of the repository"""
        return (x["number"] for x in self._get_all_issues())

    __iter__ = iterkeys

    def keys(self):
        return list(self.iterkeys())

    def itervalues(self):
        return (x[1] for x in self.iteritems())

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        return ((x["number"], GhIssue(self._owner, self._repo, x["number"], x))
                for x in self._get_all_issues())

    def items(self):
        return list(self.iteritems())

    def __getitem__(self, number):
        """Return the GhIssue object for issue number `number`"""
        # Check if `repo` is a valid repo/user
        req = github_request("GET", "/repos/{}/{}/issues/{}"
                                    .format(self._owner, self._repo, number))
        if "200" not in req.headers["status"]:
            raise KeyError("Issue with number `{}` does not exist in repo `{}/{}`."
                           .format(number, self._owner, self._repo))

        # Return GhOwnerRepos object
        return GhIssue(self._owner, self._repo, number, req.json())


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

GhRepo["issues"] = GhRepoIssues


class GhOwnerRepos(object):
    """Github container for the repositories of owner `owner`
    """

    def __init__(self, owner):
        """
        Arguments:
        - `owner`: Github owner of the represented repositories
        """
        self._owner = owner

    def iterkeys(self):
        """Enumerate repositories of the owner"""
        repos = github_request_paginated("GET", "/users/{}/repos".format(self._owner))
        return (x["name"] for x in repos)

    __iter__ = iterkeys

    def keys(self):
        return list(self.iterkeys())

    def itervalues(self):
        return (x[1] for x in self.iteritems())

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        repos = github_request_paginated("GET", "/users/{}/repos".format(self._owner))
        return ((x["name"], GhRepo(self._owner, x["name"], x)) for x in repos)

    def items(self):
        return list(self.iteritems())

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

    def __setitem__(self, repo, parameters):
        if self._owner == config.get("github", "user"):
            url = "/user/repos"
        elif Github()["users"][self._owner]["type"] == "Organization":
            url = "/orgs/{}/repos".format(self._owner)
        else:
            raise ValueError("Couldn't create repository: No permission.")

        req = github_request("POST", url,
                             data = merge_dicts(dict(name=repo), parameters))
        if "201 Created" not in req.headers["status"]:
            raise ValueError("Couldn't create repository: {}"
                             .format(req.json()["message"]))


class GhRepos(object):
    """Github repository container
    """
    def __init__(self, parent):
        self._parent = parent

    def __getitem__(self, owner):
        """Return the GhOwnerRepos object for `owner`

Check if `owner` is a valid owner first.
        """
        # Check if `owner` is a valid owner/user
        if "200" not in github_request("HEAD", "/users/{}".format(owner)).headers["status"]:
            raise KeyError("Owner '{}' does not exist.".format(owner))

        # Return GhOwnerRepos object
        return GhOwnerRepos(owner)


class GhUser(GhResource):
    """User representation
    """
    url_template = "/users/{user}"


class GhUsers(object):
    """Users representation
    """
    def __init__(self, parent):
        self._parent = parent

    def __getitem__(self, user):
        """Return the GhUser object for `user`"""
        # Check if `user` is valid
        req = github_request("HEAD", "/users/{}".format(user))
        if "200" not in req.headers["status"]:
            raise KeyError("User '{}' does not exist.".format(user))

        return GhUser(self, user=user, data=req.json())


@classtree.instantiate
class Github(classtree.Base):
    def __getitem__(self, key):
        return github_request("GET", "").json()[key]

Github["repos"] = GhRepos
Github["users"] = GhUsers






# GhRepo["issues"] = GhRepoIssues
# GhRepo["pullrequests"] = GhRepoPullrequests
