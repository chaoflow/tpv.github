from requests import request
import os
import ConfigParser
import re
import itertools

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


def set_on_new_dict(basedict, key, value):
    ret = basedict.copy()
    ret[key] = value
    return ret


def github_request(method, urlpath, data=None, params=None):
    """Request `urlpath` from github using authentication from config

    Arguments:
    - `method`: one of "HEAD", "GET", "POST", "PATCH", "DELETE"
    - `urlpath`: the path part of the request url, i.e. /users/coroa
    """

    return request(method, URL_BASE + urlpath,
                   auth=(config.get("github", "user"),
                         config.get("github", "token")),
                   data=data,
                   params=params)


def github_request_paginated(method, urlpath, params=None):
    while urlpath:
        req = github_request(method, urlpath, params=params)
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

    def __init__(self, parent, data=None, **kwargs):
        self._parent = parent
        self._parameters = kwargs
        for k, v in kwargs.iteritems():
            setattr(self, "_" + k, v)

        if data is None:
            url = self.url_template.format(**kwargs)
            data = github_request("GET", url).json()
        super(GhResource, self).update(data)

    def __setitem__(self, key, value):
        self.update({key: value})

    def update(self, data):
        url = self.url_template.format(**self._parameters)
        req = github_request("PATCH", url, data=data)
        if '200 OK' not in req.headers["status"]:
            raise ValueError("Couldn't update {} object: {}"
                             .format(self.__class__.__name__,
                                     req.json()["message"]))

        # update the cached data with the live data from
        # github. a detailed representation.
        super(GhResource, self).update(req.json())


class GhCollection(object):

    @property
    def list_url_template(self):
        raise NotImplemented("Collection is not iterable.")

    @property
    def list_key(self):
        raise NotImplemented("Collection is not iterable.")

    @property
    def get_url_template(self):
        raise NotImplemented()

    @property
    def child_class(self):
        raise NotImplemented()

    @property
    def child_parameter(self):
        raise NotImplemented()

    @property
    def add_url_template(self):
        raise NotImplemented("Can't add to collection.")

    def __init__(self, parent, data=None, **kwargs):
        self._parent = parent
        self._parameters = kwargs
        for k, v in kwargs.iteritems():
            setattr(self, "_" + k, v)

    def search(self, **arguments):
        return ((x[self.list_key],
                 self.child_class(self,
                                  data=x,
                                  **set_on_new_dict(self._parameters,
                                                    self.child_parameter,
                                                    x[self.list_key])))
                for x in self._get_resources(**arguments))

    def _get_resources(self, **arguments):
        url = self.list_url_template.format(**self._parameters)
        return github_request_paginated("GET", url, params=arguments)

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
        return self.search()

    def items(self):
        return list(self.iteritems())

    def __len__(self):
        return len(self.keys())

    def __getitem__(self, key):
        """Return the GhResource object for `key` """
        parameters = self._parameters
        parameters[self.child_parameter] = key

        url = self.get_url_template.format(**parameters)
        req = github_request("GET", url)
        if "200" not in req.headers["status"]:
            raise KeyError("Resource {} does not exist.".format(key))

        return self.child_class(self, data=req.json(), **parameters)

    def __setitem__(self, key, parameters):
        url = self.add_url_template.format(**self._parameters)
        parameters[self.list_key] = key
        req = github_request("POST", url,
                             data=parameters)
        if "201 Created" not in req.headers["status"]:
            raise ValueError("Couldn't create {} object: {}"
                             .format(self.child_class.__name__,
                                     req.json()["message"]))

    def __delitem__(self, key):
        url = self.delete_url_template.format(**self._parameters)
        req = github_request("DELETE", url)
        if "204 No Content" not in req.headers["status"]:
            raise ValueError("Couldn't delete {} object: {}"
                             .format(self.child_class.__name__,
                                     req.json()["message"]))



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

    add_url_template = "/repos/{owner}/{repo}/issues"

    def __init__(self, parent):
        super(GhRepoIssues, self).__init__(parent, **parent._parameters)

    def _get_resources(self, **arguments):
        urlpath = "/repos/{}/{}/issues".format(self._owner, self._repo)
        if "state" in arguments:
            return github_request_paginated("GET", urlpath, params=arguments)
        else:
            open_issues = github_request_paginated("GET", urlpath,
                                                   params=arguments)

            # due to asynchronicity we may not change the same object
            arguments = set_on_new_dict(arguments, "state", "closed")
            closed_issues = github_request_paginated("GET", urlpath,
                                                     params=arguments)
            return itertools.chain(open_issues, closed_issues)


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

    @property
    def add_url_template(self):
        if self._owner == config.get("github", "user"):
            return "/user/repos"
        elif self._parent._parent["users"][self._owner]["type"] == "Organization":
            return "/orgs/{owner}/repos"

        raise ValueError("Couldn't create repository: No permission.")

    delete_url_template = get_url_template


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
