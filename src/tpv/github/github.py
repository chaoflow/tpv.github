from metachao import classtree
import itertools
import re

from .github_base import \
    URL_BASE, extract_repo_from_issue_url, \
    GhResource, GhCollection, \
    github_request, github_request_paginated, \
    set_on_new_dict, authenticated_user


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


class GhPullComment(GhResource):
    """ReviewComment of a pull request """

    url_template = "/repos/{user}/{repo}/pulls/comments/{commentid}"


class GhPullComments(GhCollection):
    """The comments of some pull request
    """

    list_url_template = "/repos/{user}/{repo}/pulls/{issueno}/comments"
    list_key = "id"

    get_url_template = "/repos/{user}/{repo}/pulls/comments/{commentid}"
    child_class = GhPullComment
    child_parameter = "commentid"

    add_url_template = list_url_template
    add_required_arguments = ["body"]

    delete_url_template = get_url_template


class GhRepoPullComments(GhCollection):
    """The comments of some repository
    """

    list_url_template = "/repos/{user}/{repo}/pulls/comments"
    list_key = "id"

    get_url_template = "/repos/{user}/{repo}/pulls/comments/{commentid}"
    child_class = GhPullComment
    child_parameter = "commentid"

    delete_url_template = get_url_template


@classtree.instantiate
class GhPull(GhResource, classtree.Base):
    """Pullrequest of some repository
    """

    url_template = "/repos/{user}/{repo}/pulls/{issueno}"

GhPull["issue"] = GhIssue
GhPull["comments"] = GhPullComments


class GhRepoPulls(GhCollection):
    """The issues of some repository
    """

    list_url_template = "/repos/{user}/{repo}/pulls"
    list_key = "number"

    get_url_template = "/repos/{user}/{repo}/pulls/{issueno}"
    child_class = GhPull
    child_parameter = "issueno"

    add_url_template = "/repos/{user}/{repo}/pulls"

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
GhRepo["pulls"] = GhRepoPulls
GhRepo["pullcomments"] = GhRepoPullComments


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
        grandparent = self._parent._parent
        if self._user == authenticated_user():
            return "/user/repos"
        elif grandparent["users"][self._user]["type"] == "Organization":
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
        (user, repo) = extract_repo_from_issue_url(data["url"], issueno)
        return self.child_class(self,
                                data=data,
                                **{'user': user,
                                   'repo': repo,
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
