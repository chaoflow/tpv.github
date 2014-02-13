from plumbum.cmd import git
from itertools import ifilter

from ..github import Github, GhOrg, GhRepo, authenticated_user

github = Github()


def repo_type(repo_name, user_fallback=None):
    """Return GhRepo object for `repo_name`

If `repo_name` is omitted, the origin remote of the current directory's
git repository is used.

if `repo_name` is not a full name (i.e. doesn't include the owner),
either `user_fallback` or the authenticated user is used.
    """
    if repo_name is None:
        # fetch from git repo
        url = git["config", "remote.origin.url"]().rstrip('\n')
        if url.startswith("git@github.com:"):
            repo_name = url[len("git@github.com:"):]
        elif url.startswith("https://github.com/"):
            repo_name = url[len("https://github.com/"):]
        else:
            raise ValueError("Remote origin is not from github.")

        if repo_name.endswith(".git"):
            repo_name = repo_name[:-len(".git")]

    if '/' not in repo_name:
        user = authenticated_user() \
            if user_fallback is None \
            else user_fallback
        repo = repo_name
    else:
        (user, repo) = repo_name.split("/", 1)

    try:
        return github["repos"][user][repo]
    except KeyError:
        raise ValueError("Repository `{}` not found on github."
                         .format(repo_name))


def user_type(user):
    """Return GhUser object for `user` or the authenticated user"""
    if user is None:
        user = authenticated_user()

    try:
        return github["users"][user]
    except KeyError:
        raise ValueError("User `{}` not found on github."
                         .format(user))


def org_type(org):
    """Return GhOrg object for `org`"""
    try:
        return github["orgs"][org]
    except KeyError:
        raise ValueError("Organisation `{}` not found on github."
                         .format(org))


def team_type(org, team_name):
    """Return GhTeam object for the `team_name` team from `org`

`org` can be the name of the organization or its GhOrg object.
`team_name` defaults to "Owners"
    """
    if not isinstance(org, GhOrg):
        org = org_type(org)

    if team_name is None:
        team_name = "Owners"

    try:
        # as teams are accessed by their team id, we have to iterate
        # until we find `team_name`
        return next(ifilter(lambda x: x['name'] == team_name,
                            org["teams"].itervalues()))
    except (StopIteration, KeyError):
        raise ValueError("Team `{}` not found in organisation `{}` on github."
                         .format(team_name, org['login']))


def issue_type(repo, issueno):
    """Return GhIssue object for the issue with `issueno` from `repo`

`repo` can be the name of the repository or its GhRepo object.
    """
    if not isinstance(repo, GhRepo):
        repo = repo_type(repo)

    try:
        return repo["issues"][issueno]
    except KeyError:
        raise ValueError("Issue `{}` not found in repository `{}`."
                         .format(issueno, repo['full_name']))


def pull_type(repo, pullno):
    """Return GhPull object for the pull request with `pullno` from `repo`

`repo` can be the name of the repository or its GhRepo object.
    """
    if not isinstance(repo, GhRepo):
        repo = repo_type(repo)

    try:
        return repo["pulls"][pullno]
    except KeyError:
        raise ValueError("Pull request `{}` not found in repository `{}`."
                         .format(pullno, repo['full_name']))
