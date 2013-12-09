from requests import request
import json
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


def authenticated_user():
    return config.get("github", "user")


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
                   data=None if data is None else json.dumps(data),
                   params=params)


def github_request_paginated(method, urlpath, params=None):
    while urlpath:
        req = github_request(method, urlpath, params=params)
        if '200 OK' not in req.headers['status']:
            raise RuntimeError(req.json()['message'])

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
        raise NotImplementedError()

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
        try:
            data = set_on_new_dict(data,
                                   self._parent.list_key,
                                   self._parameters[self._parent.child_parameter])
        except NotImplementedError:
            # the parent is not iterable, the caller of update has to
            # supply all mandatory arguments in data
            pass

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
        raise NotImplementedError("Collection is not iterable.")

    @property
    def list_key(self):
        raise NotImplementedError("Collection is not iterable.")

    @property
    def get_url_template(self):
        raise NotImplementedError()

    @property
    def child_class(self):
        raise NotImplementedError()

    @property
    def child_parameter(self):
        raise NotImplementedError()

    @property
    def add_url_template(self):
        raise NotImplementedError("Can't add to collection.")

    add_method = "POST"
    # add_required_arguments = [ "name", "..." ... ]

    def __init__(self, parent, data=None, **kwargs):
        self._parent = parent
        self._parameters = kwargs

        if not self._parameters and self._parent:
            self._parameters = self._parent._parameters

        for k, v in self._parameters.iteritems():
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
        parameters = set_on_new_dict(self._parameters,
                                     self.child_parameter,
                                     key)

        url = self.get_url_template.format(**parameters)
        req = github_request("GET", url)
        if "200" not in req.headers["status"]:
            raise KeyError("Resource {} does not exist.".format(key))

        return self.child_class(self, data=req.json(), **parameters)

    def add(self, **arguments):
        # check if all required arguments are provided
        for required_arg in getattr(self, 'add_required_arguments', []):
            if required_arg not in arguments:
                raise ValueError("Not all required arguments {} provided"
                                 .format(", ".join(self.add_required_arguments)))

        if self.add_method == "POST":
            url = self.add_url_template.format(**self._parameters)
            req = github_request("POST", url,
                                 data=arguments)
            if "201 Created" not in req.headers["status"]:
                raise ValueError("Couldn't create {} object: {}"
                                 .format(self.child_class.__name__,
                                         req.json()["message"]))
            else:
                data = req.json()
                parameters = set_on_new_dict(self._parameters,
                                             self.child_parameter,
                                             data[self.list_key])
                return self.child_class(parent=self, data=data, **parameters)

        elif self.add_method == "PUT":
            tmpl_vars = set_on_new_dict(self._parameters,
                                        self.child_parameter,
                                        arguments[self.list_key])
            url = self.add_url_template.format(**tmpl_vars)

            req = github_request("PUT", url,
                                 data=arguments)
            if "204 No Content" not in req.headers["status"]:
                raise ValueError("Couldn't create {} object: {}"
                                 .format(self.child_class.__name__,
                                         req.json()["message"]))
            # else:
            #     return self.child_class(parent=self, **tmpl_vars)

    def __delitem__(self, key):
        tmpl_vars = set_on_new_dict(self._parameters,
                                    self.child_parameter, key)
        url = self.delete_url_template.format(**tmpl_vars)
        req = github_request("DELETE", url)
        if "204 No Content" not in req.headers["status"]:
            raise ValueError("Couldn't delete {} object: {}"
                             .format(self.child_class.__name__,
                                     req.json()["message"]))


class GhComment(GhResource):
    """Comment of some issue """

    url_template = "/repos/{user}/{repo}/issues/comments/{commentid}"


class GhRepoComments(GhCollection):
    """The comments of some repository
    """

    list_url_template = "/repos/{user}/{repo}/issues/comments"
    list_key = "id"

    get_url_template = "/repos/{user}/{repo}/issues/comments/{commentid}"
    child_class = GhComment
    child_parameter = "commentid"

    delete_url_template = get_url_template


class GhIssueComments(GhCollection):
    """The comments of some issue
    """

    list_url_template = "/repos/{user}/{repo}/issues/{issueno}/comments"
    list_key = "id"

    get_url_template = "/repos/{user}/{repo}/issues/comments/{commentid}"
    child_class = GhComment
    child_parameter = "commentid"

    add_url_template = list_url_template
    add_required_arguments = ["body"]

    delete_url_template = get_url_template


@classtree.instantiate
class GhIssue(GhResource, classtree.Base):
    """Issue of some repository
    """

    url_template = "/repos/{user}/{repo}/issues/{issueno}"

GhIssue["comments"] = GhIssueComments


class GhRepoIssues(GhCollection):
    """The issues of some repository
    """

    list_url_template = "/repos/{user}/{repo}/issues"
    list_key = "number"

    get_url_template = "/repos/{user}/{repo}/issues/{issueno}"
    child_class = GhIssue
    child_parameter = "issueno"

    add_url_template = "/repos/{user}/{repo}/issues"

    def _get_resources(self, **arguments):
        urlpath = self.list_url_template.format(**self._parameters)
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

    url_template = "/repos/{user}/{repo}"

GhRepo["issues"] = GhRepoIssues
GhRepo["comments"] = GhRepoComments


class GhUserRepos(GhCollection):
    """Github container for the repositories of user `user`
    """

    list_url_template = "/users/{user}/repos"
    list_key = "name"

    get_url_template = "/repos/{user}/{repo}"
    child_class = GhRepo
    child_parameter = "repo"

    @property
    def add_url_template(self):
        if self._user == authenticated_user():
            return "/user/repos"
        elif self._parent._parent["users"][self._user]["type"] == "Organization":
            return "/orgs/{user}/repos"

        raise ValueError("Couldn't create repository: No permission.")

    delete_url_template = get_url_template


class GhRepos(GhCollection):
    """Github repository container
    """

    get_url_template = "/users/{user}"
    child_class = GhUserRepos
    child_parameter = "user"


class GhMember(GhResource):
    """Member of an organisation or team"""


class GhTeamMembers(GhCollection):
    """Members of a team"""

    list_url_template = "/teams/{teamid}/members"
    list_key = "login"

    child_class = GhMember
    child_parameter = "login"

    add_url_template = "/teams/{teamid}/members/{login}"
    add_method = "PUT"

    delete_url_template = "/teams/{teamid}/members/{login}"


class GhTeamRepos(GhCollection):
    """Repos in an organisation's team"""

    list_url_template = "/teams/{teamid}/repos"
    list_key = "name"

    child_class = GhResource
    child_parameter = "repo_name"

    add_url_template = "/teams/{teamid}/repos/{repo_name}"
    add_method = "PUT"

    delete_url_template = "/teams/{teamid}/repos/{repo_name}"


@classtree.instantiate
class GhTeam(GhResource, classtree.Base):
    """Team in an organisation """

    url_template = "/teams/{teamid}"

GhTeam["members"] = GhTeamMembers
GhTeam["repos"] = GhTeamRepos


class GhOrgTeams(GhCollection):
    """Teams in an organisation
    """

    list_url_template = "/orgs/{org}/teams"
    list_key = "id"

    get_url_template = "/teams/{teamid}"
    child_parameter = "teamid"
    child_class = GhTeam

    add_url_template = "/orgs/{org}/teams"
    delete_url_template = "/teams/{teamid}"


class GhOrgMembers(GhCollection):
    """Members of an organisation"""

    list_url_template = "/orgs/{org}/members"
    list_key = "login"

    child_class = GhMember
    child_parameter = "login"

    delete_url_template = "/orgs/{org}/members/{login}"


@classtree.instantiate
class GhOrg(GhResource, classtree.Base):
    """Organisation"""

    url_template = "/orgs/{org}"

GhOrg["members"] = GhOrgMembers
GhOrg["teams"] = GhOrgTeams


class GhOrgs(GhCollection):
    """Organisations representation
    """

    get_url_template = "/orgs/{org}"
    child_class = GhOrg
    child_parameter = "org"


class GhUserIssues(GhRepoIssues):
    """The issues of the authenticated user"""

    list_url_template = "/user/issues"

    @property
    def get_url_template(self):
        raise NotImplementedError()

    @property
    def add_url_template(self):
        raise NotImplementedError("Can't add to collection.")

    def _instantiate_child_from_url(self, issueno, data):
        m = re.match(URL_BASE + "/repos/(.+)/(.+)/issues/{}"
                     .format(issueno),
                     data["url"])
        return self.child_class(self,
                                data=data,
                                **{'user': m.group(1),
                                   'repo': m.group(2),
                                   'issueno': issueno})

    def search(self, **arguments):
        for data in self._get_resources(**arguments):
            issueno = data[self.list_key]
            yield (issueno, self._instantiate_child_from_url(issueno, data))


class GhUserOrgs(GhCollection):
    """The organisations of the authenticated user"""

    list_url_template = "/user/orgs"
    list_key = "login"

    get_url_template = "/orgs/{org}"
    child_parameter = "org"
    child_class = GhOrg


@classtree.instantiate
class GhUser(GhResource, classtree.Base):
    """User representation
    """
    @property
    def url_template(self):
        return "/user" \
            if self._user == authenticated_user() \
            else "/users/{user}"

GhUser["repos"] = GhUserRepos
GhUser["issues"] = GhUserIssues
GhUser["orgs"] = GhUserOrgs


class GhUsers(GhCollection):
    """Users representation"""

    get_url_template = "/users/{user}"
    child_class = GhUser
    child_parameter = "user"


@classtree.instantiate
class Github(classtree.Base):
    _parameters = dict()

    def __getitem__(self, key):
        return github_request("GET", "").json()[key]

Github["repos"] = GhRepos
Github["users"] = GhUsers
Github["orgs"] = GhOrgs




# GhRepo["issues"] = GhRepoIssues
# GhRepo["pullrequests"] = GhRepoPullrequests
