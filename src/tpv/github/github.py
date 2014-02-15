from metachao import classtree
import itertools

from .github_base import \
    cache, \
    extract_repo_from_issue_url, \
    GhBase, GhResource, GhCollection, \
    github_request, github_request_paginated, \
    set_on_new_dict, authenticated_user


class GhComment(GhResource):
    """Comment of some issue """

    url_template = "/repos/{user}/{repo}/issues/comments/{commentid}"


class GhRepoComments(GhCollection):
    """The comments of some repository
    """

    child_class = GhComment
    child_parameter = "commentid"

    get_url_template = "/repos/{user}/{repo}/issues/comments/{commentid}"

    list_url_template = "/repos/{user}/{repo}/issues/comments"
    list_key = "id"

    delete_url_template = get_url_template


class GhIssueComments(GhCollection):
    """The comments of some issue
    """

    child_class = GhComment
    child_parameter = "commentid"

    get_url_template = "/repos/{user}/{repo}/issues/comments/{commentid}"

    list_url_template = "/repos/{user}/{repo}/issues/{issueno}/comments"
    list_key = "id"

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

    child_class = GhIssue
    child_parameter = "issueno"

    get_url_template = "/repos/{user}/{repo}/issues/{issueno}"

    list_url_template = "/repos/{user}/{repo}/issues"
    list_key = "number"

    add_url_template = "/repos/{user}/{repo}/issues"

    # as github provides only either open or closed issues, we chain
    # two separate calls to get all of them
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

    child_class = GhPullComment
    child_parameter = "commentid"

    get_url_template = "/repos/{user}/{repo}/pulls/comments/{commentid}"

    list_url_template = "/repos/{user}/{repo}/pulls/{issueno}/comments"
    list_key = "id"

    add_url_template = list_url_template
    add_required_arguments = ["body"]

    delete_url_template = get_url_template


class GhRepoPullComments(GhCollection):
    """The comments of some repository
    """

    child_class = GhPullComment
    child_parameter = "commentid"

    get_url_template = "/repos/{user}/{repo}/pulls/comments/{commentid}"

    list_url_template = "/repos/{user}/{repo}/pulls/comments"
    list_key = "id"

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

    child_class = GhPull
    child_parameter = "issueno"

    get_url_template = "/repos/{user}/{repo}/pulls/{issueno}"

    list_url_template = "/repos/{user}/{repo}/pulls"
    list_key = "number"

    add_url_template = "/repos/{user}/{repo}/pulls"

    # as github provides only either open or closed pull requests, we
    # chain two separate calls to get all of them
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

    child_class = GhRepo
    child_parameter = "repo"

    get_url_template = "/repos/{user}/{repo}"

    list_url_template = "/users/{user}/repos"
    list_key = "name"

    # Repositories can only be created for the authenticated user or
    # an organization, which the user is part of (checked by github).
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

    child_class = GhUserRepos
    child_parameter = "user"

    get_url_template = "/users/{user}"


class GhMember(GhResource):
    """Member of an organisation or team"""


class GhTeamMembers(GhCollection):
    """Members of a team"""

    child_class = GhMember
    child_parameter = "login"

    list_url_template = "/teams/{teamid}/members"
    list_key = "login"

    add_url_template = "/teams/{teamid}/members/{login}"
    add_method = "PUT"
    add_required_arguments = ["login"]

    delete_url_template = "/teams/{teamid}/members/{login}"


class GhTeamRepos(GhCollection):
    """Repos in an organisation's team"""

    child_class = GhResource
    child_parameter = "repo_name"

    list_url_template = "/teams/{teamid}/repos"
    list_key = "name"

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

    child_class = GhTeam
    child_parameter = "teamid"

    get_url_template = "/teams/{teamid}"

    list_url_template = "/orgs/{org}/teams"
    list_key = "id"

    add_url_template = "/orgs/{org}/teams"
    add_required_arguments = ["name"]
    delete_url_template = "/teams/{teamid}"


class GhOrgMembers(GhCollection):
    """Members of an organisation"""

    child_class = GhMember
    child_parameter = "login"

    list_url_template = "/orgs/{org}/members"
    list_key = "login"

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

    child_class = GhOrg
    child_parameter = "org"

    get_url_template = "/orgs/{org}"


class GhUserIssues(GhRepoIssues):
    """The issues of the authenticated user"""

    list_url_template = "/user/issues"

    # Getting a single resource can only be done from within a repository
    @property
    def get_url_template(self):
        raise NotImplementedError()

    # Creating a new issue can only be done from within a repository
    @property
    def add_url_template(self):
        raise NotImplementedError("Can't add to collection.")

    def _instantiate_child_from_url(self, issueno, data):
        """Instantiate an issue ressource by deducing the necessary owner and
repo tuple from the url of the issue.
        """

        (user, repo) = extract_repo_from_issue_url(data["url"])
        return self.child_class(self,
                                data=data,
                                **{'user': user,
                                   'repo': repo,
                                   'issueno': issueno})

    def search(self, **arguments):
        """Return a subset of issue resources, which can only be instantiated
by using the url of the issue
        """
        for data in self._get_resources(**arguments):
            issueno = data[self.list_key]
            yield (issueno, self._instantiate_child_from_url(issueno, data))


class GhUserOrgs(GhCollection):
    """The organisations of the authenticated user"""

    child_class = GhOrg
    child_parameter = "org"

    get_url_template = "/orgs/{org}"

    list_url_template = "/user/orgs"
    list_key = "login"


@classtree.instantiate
class GhUser(GhResource, classtree.Base):
    """User representation
    """

    # The url depends on whether the GhUser resource refers to the
    # authenticated user or any other one
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

    child_class = GhUser
    child_parameter = "user"

    get_url_template = "/users/{user}"


@cache(node_class=GhBase)
@classtree.instantiate
class Github(GhBase, classtree.Base):
    _parameters = dict()

    def __init__(self):
        GhBase.__init__(self, None)

    def __getitem__(self, key):
        return github_request("GET", "").json()[key]

Github["repos"] = GhRepos
Github["users"] = GhUsers
Github["orgs"] = GhOrgs
