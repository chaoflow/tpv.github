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
        self._parameters = kwargs
        for k, v in kwargs.iteritems():
            setattr(self, "_" + k, v)

        if data is None:
            data = github_request("GET", self.url_template
                                         .format(**kwargs).json())
        self.update(data)


class GhCollection(object):

    list_url_template = None
    list_key = None

    @property
    def get_url_template(self):
        raise NotImplemented()

    @property
    def child_class(self):
        raise NotImplemented()

    @property
    def child_parameter(self):
        raise NotImplemented()

    def __init__(self, parent, data = None, **kwargs):
        self._parent = parent
        self._parameters = kwargs
        for k, v in kwargs.iteritems():
            setattr(self, "_" + k, v)

    def _get_resources(self):
        if self.list_url_template is None or self.list_key is None:
            raise NotImplemented("Not iterable")

        url = self.list_url_template.format(**self._parameters)
        return github_request_paginated("GET", url)

    def iterkeys(self):
        return (x[self.list_key] for x in self._get_resources())

    __iter__ = iterkeys

    def keys(self):
        return list(self.iterkeys())

    def itervalues(self):
        return (x[1] for x in self.iteritems())

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        return ((x[self.list_key],
                 self.child_class(self,
                                  data=x,
                                  **merge_dicts(self._parameters,
                                                {self.child_parameter:
                                                 x[self.list_key]})))
                for x in self._get_resources())

    def items(self):
        return list(self.iteritems())

    def __len__(self):
        return len(self.keys())

    def __getitem__(self, key):
        """Return the GhResource object for `key` """
        parameters = self._parameters
        parameters[self.child_parameter] = key

        req = github_request("GET", self.get_url_template
                                    .format(**parameters))
        if "200" not in req.headers["status"]:
            raise KeyError("Resource {} does not exist.".format(key))

        return self.child_class(self, data=req.json(), **parameters)


class GhIssue(GhResource):
    """Issue of some repository
    """

    url_template = "/repos/{owner}/{repo}/issues/{number}"


class GhRepoIssues(GhCollection):
    """The issues of some repository
    """

    list_url_template = "/repos/{owner}/{repo}/issues"
    list_key = "number"

    get_url_template = "/repos/{owner}/{repo}/issues/{number}"
    child_class = GhIssue
    child_parameter = "number"

    def __init__(self, parent):
        super(GhRepoIssues, self).__init__(parent, **parent._parameters)

    def _get_resources(self):
        urlpath = "/repos/{}/{}/issues".format(self._owner, self._repo)
        return itertools.chain(github_request_paginated("GET", urlpath),
                               github_request_paginated("GET", urlpath + "?state=closed"))


@classtree.instantiate
class GhRepo(GhResource, classtree.Base):
    """Github repository representation
    """

    url_template = "/repos/{owner}/{repo}"

GhRepo["issues"] = GhRepoIssues


class GhOwnerRepos(GhCollection):
    """Github container for the repositories of owner `owner`
    """

    list_url_template = "/users/{owner}/repos"
    list_key = "name"

    get_url_template = "/repos/{owner}/{repo}"
    child_class = GhRepo
    child_parameter = "repo"

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


class GhRepos(GhCollection):
    """Github repository container
    """

    get_url_template = "/users/{owner}"
    child_class = GhOwnerRepos
    child_parameter = "owner"


class GhUser(GhResource):
    """User representation
    """
    url_template = "/users/{user}"


class GhUsers(GhCollection):
    """Users representation
    """

    get_url_template = "/users/{user}"
    child_class = GhUser
    child_parameter = "user"


@classtree.instantiate
class Github(classtree.Base):
    def __getitem__(self, key):
        return github_request("GET", "").json()[key]

Github["repos"] = GhRepos
Github["users"] = GhUsers






# GhRepo["issues"] = GhRepoIssues
# GhRepo["pullrequests"] = GhRepoPullrequests
