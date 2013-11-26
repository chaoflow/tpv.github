import tpv.cli
from aspects import stdout_to_pager

from .types import repo_type
from .decorators import add_argument_switches


class Issues(tpv.cli.Command):
    """Manage issues
    """
    def __call__(self):
        pass


@add_argument_switches([
    dict(name="milestone", help=u"milestone number or '*' for any"),
    dict(name="state", help=u"Indicates the state of the issues to return. Can be either open or closed."),
    dict(name="assignee", help=u"Can be the name of a user. Pass in none for issues with no assigned user, and * for issues assigned to any user."),
    dict(name="creator", help=u"The user that created the issue"),
    dict(name="mentioned", help=u"A user that's mentioned in the issue"),
    dict(name="labels", help=u"A list of comma separated label names"),
    dict(name="sort", help=u"What to sort results by. Can be either created, updated, comments."),
    dict(name="direction", help=u"The direction of the sort. Can be either asc or desc."),
    dict(name="since", help=u"Only issues updated at or after this time are returned (YYYY-MM-DDTHH:MM:SSZ).")
])
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

        print tmpl.format(cyanfont="\033[0;36m", normalfont="\033[0m",
                          **issue).encode('utf-8')

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
