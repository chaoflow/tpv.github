import tpv.cli
from ..github import Github, GhRepoIssues
from plumbum.cmd import git


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

    (owner, repo) = repo_name.split("/", 1)
    try:
        return Github()["repos"][owner][repo]
    except KeyError:
        raise ValueError("Repository `{}` not found on github."
                         .format(repo_name))


class Issues(tpv.cli.Command):
    """Manage issues
    """
    def __call__(self):
        pass


def make_function(name):
    return lambda self, param: self.arguments.__setitem__(name, param)


def add_argument_switches(parameter_names):
    def deco(cls):
        for name in parameter_names:
            f = tpv.cli.switch("--" + name, argtype=str)(make_function(name))
            setattr(cls, name, f)
        return cls
    return deco


@add_argument_switches(["creator", "mentioned", "labels", "assignee"])
class List(tpv.cli.Command):
    """List issues matching filter criteria
    """
    repo = tpv.cli.SwitchAttr("--repo", repo_type, help="The repository <owner>/<repo>")

    def __init__(self, *args):
        super(List, self).__init__(*args)
        self.arguments = dict()

    def print_issue(self, issue):
        tmpl = u'''
{cyanfont}{number}: {title}{normalfont}
State: {state}
Author: {user[login]}
        '''.strip()+"\n"
        if issue["assignee"] is not None:
            tmpl += "Assignee: {assignee[login]}\n"

        print tmpl.format(cyanfont="\033[0;36m", normalfont="\033[0m", **issue)

    def __call__(self):
        if self.repo == None:
            self.repo = repo_type(None)

        for no, issue in self.repo["issues"].search(**self.arguments):
            self.print_issue(issue)


class Show(tpv.cli.Command):
    """Show a list of issues by their issuenumber
    """
    def __call__(self, *issuenumbers):
        for issueno in issuenumbers:
            # great stuff to happen here
            pass


class Add(tpv.cli.Command):
    """Add a new issue
    """
    def __call__(self):
        pass
