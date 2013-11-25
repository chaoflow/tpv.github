from plumbum.cmd import git

from ..github import Github, authenticated_user


def repo_type(repo_name):
    if repo_name is None:
        # fetch from git repo
        url = git["config", "remote.origin.url"]().rstrip('\n')
        if url.startswith("git@github.com:") and url.endswith(".git"):
            repo_name = url[len("git@github.com:"):-len(".git")]
        elif url.startswith("https://github.com/") and url.endswith(".git"):
            repo_name = url[len("https://github.com/"):-len(".git")]
        else:
            raise ValueError("Remote origin is not from github.")

    (user, repo) = repo_name.split("/", 1)
    try:
        return Github()["repos"][user][repo]
    except KeyError:
        raise ValueError("Repository `{}` not found on github."
                         .format(repo_name))


def user_type(user):
    if user is None:
        user = authenticated_user()

    try:
        return Github()["users"][user]
    except KeyError:
        raise ValueError("User `{}` not found on github."
                         .format(user))
