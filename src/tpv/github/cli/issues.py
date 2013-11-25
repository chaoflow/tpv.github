import tpv.cli
from aspects import stdout_to_pager

from .types import repo_type


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


@add_argument_switches(["milestone",
                        "state",
                        "assignee",
                        "creator",
                        "mentioned",
                        "labels",
                        "sort",
                        "direction",
                        "since"])
@stdout_to_pager
class List(tpv.cli.Command):
    """List issues matching filter criteria
    """
    repo = tpv.cli.SwitchAttr("--repo", repo_type, help="The repository <user>/<repo>")

    def __init__(self, *args):
        tpv.cli.Command.__init__(self, *args)
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
