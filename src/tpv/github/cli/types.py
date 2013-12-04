from tpv.cli import DocPredicate
from plumbum.cmd import git
from itertools import ifilter

from ..github import Github, GhOrg, GhRepo, authenticated_user

github = Github()


@DocPredicate
def repo_type(repo_name, user_fallback=None):
    """repository"""
    if repo_name is None:
        # fetch from git repo
        url = git["config", "remote.origin.url"]().rstrip('\n')
        if url.startswith("git@github.com:") and url.endswith(".git"):
            repo_name = url[len("git@github.com:"):-len(".git")]
        elif url.startswith("https://github.com/") and url.endswith(".git"):
            repo_name = url[len("https://github.com/"):-len(".git")]
        else:
            raise ValueError("Remote origin is not from github.")

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


@DocPredicate
def user_type(user):
    """user"""
    if user is None:
        user = authenticated_user()

    try:
        return github["users"][user]
    except KeyError:
        raise ValueError("User `{}` not found on github."
                         .format(user))


@DocPredicate
def org_type(org):
    """organisation"""
    try:
        return github["orgs"][org]
    except KeyError:
        raise ValueError("Organisation `{}` not found on github."
                         .format(org))


@DocPredicate
def team_type(org, team_name):
    """teamno"""
    if not isinstance(org, GhOrg):
        org = org_type(org)

    if team_name is None:
        team_name = "Owners"

    try:
        teamid = next(ifilter(lambda x: x['name'] == team_name,
                              org["teams"].itervalues()))['id']
        return org["teams"][teamid]
    except (StopIteration, KeyError):
        raise ValueError("Team `{}` not found in organisation `{}` on github."
                         .format(team_name, org['login']))


@DocPredicate
def issue_type(repo, issueno):
    """issueno"""
    if not isinstance(repo, GhRepo):
        repo = repo_type(repo)

    try:
        return repo["issues"][issueno]
    except KeyError:
        raise ValueError("Issue `{}` not found in repository `{}`."
                         .format(issueno, repo['full_name']))
