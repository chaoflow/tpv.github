import tpv.cli
from aspects import stdout_to_pager

from ..github_base import set_on_new_dict, extract_repo_from_issue_url
from .types import repo_type, issue_type, user_type
from .switches import add_argument_switches
from tpv.cli import ListCompletion
from .completion import \
    RepositoryDynamicCompletion, \
    RepoChildIdDynamicCompletion


@add_argument_switches([
    dict(name="milestone", help=u"milestone number or '*' for any"),
    dict(name="state", help=u"Indicates the state of the issues to return. Can be either all, open or closed.", completion=ListCompletion("all", "open","closed")),
    dict(name="assignee", help=u"Can be the name of a user. Pass in none for issues with no assigned user, and * for issues assigned to any user."),
    dict(name="creator", help=u"The user that created the issue"),
    dict(name="mentioned", help=u"A user that's mentioned in the issue"),
    dict(name="labels", help=u"A list of comma separated label names"),
    dict(name="sort", help=u"What to sort results by. Can be either created, updated, comments."),
    dict(name="direction", help=u"The direction of the sort. Can be either asc or desc.", completion=ListCompletion("asc","desc")),
    dict(name="since", help=u"Only issues updated at or after this time are returned (YYYY-MM-DDTHH:MM:SSZ).")
])
#@stdout_to_pager
class List(tpv.cli.Command):
    """List issues matching filter criteria

The use of the stdout_to_pager aspect confuses plumbum into thinking
we accept a list of nondescript arguments, which blocks proper
completion of the options.

    """
    verbose = tpv.cli.Flag(["--verbose", "-v"],
                           help="Print more details on the issues")

    repo = tpv.cli.SwitchAttr("--repo", str, argname="",
                              help="The repository <user>/<repo>",
                              completion=RepositoryDynamicCompletion())

    mine = tpv.cli.SwitchAttr("--mine", str, argname="",
                              help="List my issues (all/assigned/created/mentioned/subscribed)",
                              completion=ListCompletion("all",
                                                        "assigned",
                                                        "created",
                                                        "mentioned",
                                                        "subscribed"),
                              excludes=("--milestone",
                                        "--assignee",
                                        "--creator",
                                        "--mentioned"))

    def __init__(self, *args):
        tpv.cli.Command.__init__(self, *args)
        self.arguments = dict()

    def print_issue(self, issue):
        if self.verbose:
            self.print_issue_long(issue)
        else:
            self.print_issue_short(issue)

    def print_issue_short(self, issue):
        tmpl = u"#{number}"
        if self.mine is not None and self.repo is None:
            (user, repo) = extract_repo_from_issue_url(issue["url"],
                                                       issue["number"])
            tmpl += " :{}/{}".format(user, repo)
        tmpl += " {cyanfont}{title}{normalfont}"
        if issue["assignee"] is not None:
            tmpl += " @{assignee[login]}"

        print tmpl.format(cyanfont="\033[0;36m", normalfont="\033[0m",
                          **issue).encode('utf-8')

    def print_issue_long(self, issue):
        tmpl = u"#{number} {cyanfont}{title}{normalfont}\n"
        if self.mine is not None and self.repo is None:
            (user, repo) = extract_repo_from_issue_url(issue["url"],
                                                       issue["number"])
            tmpl += "Repo: {}/{}\n".format(user, repo)
        tmpl += '''
State: {state}
Author: {user[login]}
        '''.strip()+"\n"

        if issue["assignee"] is not None:
            tmpl += "Assignee: {assignee[login]}\n"

        print tmpl.format(cyanfont="\033[0;36m", normalfont="\033[0m",
                          **issue).encode('utf-8')

    def __call__(self):
        if "state" not in self.arguments:
            self.arguments["state"] = "open"
        elif self.arguments["state"] == "all":
            del self.arguments["state"]

        if self.mine is None:
            repo = repo_type(self.repo)
            issues = repo["issues"].search(**self.arguments)
        elif self.repo is None:
            user = user_type(None)
            arguments = set_on_new_dict(self.arguments,
                                        "filter", self.mine)
            issues = user["issues"].search(**arguments)
        else:
            repo = repo_type(self.repo)
            user = user_type(None)

            try:
                arguments = set_on_new_dict(self.arguments,
                                            {'created': 'creator',
                                             'mentioned': 'mentioned',
                                             'assigned': 'assignee'}
                                            [self.mine],
                                            user['login'])
            except KeyError:
                raise ValueError("When specifying --repo as well as --mine, "
                                 "--mine can only be one of created, "
                                 "mentioned or assigned")

            issues = repo["issues"].search(**arguments)

        for no, issue in issues:
            self.print_issue(issue)


class Show(tpv.cli.Command):
    """Show a list of issues by their issuenumber """

    repo = tpv.cli.SwitchAttr("--repo", str, argname="",
                              help="The repository <user>/<repo>",
                              completion=RepositoryDynamicCompletion())

    with_comments = tpv.cli.Flag("--no-comments",
                                 help="Don't print comments",
                                 default=True)

    def print_comment(self, comment):
        tmpl = u'''
#{id} {cyanfont}{user[login]}{normalfont}
updated: {updated_at}
{body}
        '''.strip()+"\n"

        print tmpl.format(cyanfont="\033[0;36m", normalfont="\033[0m",
                          **comment).encode('utf-8')

    def print_issue(self, issue):
        tmpl = u'''
#{number} {cyanfont}{title}{normalfont}
State: {state}
Author: {user[login]}
Updated: {updated_at}
        '''.strip()+"\n"
        if issue["assignee"] is not None:
            tmpl += u"Assignee: {assignee[login]}\n"
        if len(issue["body"]) > 0:
            tmpl += u"\n{body}\n"

        print tmpl.format(cyanfont="\033[0;36m", normalfont="\033[0m",
                          **issue).encode('utf-8')

        if self.with_comments:
            print "{cyanfont}Comments:{normalfont}" \
                .format(cyanfont="\033[0;36m",
                        normalfont="\033[0m")

            for comment in issue["comments"].itervalues():
                self.print_comment(comment)

    @tpv.cli.completion(issuenumbers=RepoChildIdDynamicCompletion("issues"))
    def __call__(self, *issuenumbers):
        self.repo = repo_type(self.repo)

        for issueno in issuenumbers:
            issue = issue_type(self.repo, issueno)
            self.print_issue(issue)


@add_argument_switches([
    dict(name="milestone", help=u"milestone number or '*' for any"),
    dict(name="title", help=u"The title of the issue", mandatory=True),
    dict(name="body", flagname="--description",
         help=u"The contents of the issue."),
    dict(name="assignee",
         help=u"Login for the user that this issue should be assigned to."),
    dict(name="milestone",
         help=u"Milestone to associate this issue with."),
    dict(name="labels", flagname="--label", list=True,
         help=u"Labels to associate with this issue")
])
class Add(tpv.cli.Command):
    """Add a new issue """

    repo = tpv.cli.SwitchAttr("--repo", str, argname="",
                              help="The repository <user>/<repo>",
                              completion=RepositoryDynamicCompletion())

    def __init__(self, *args):
        tpv.cli.Command.__init__(self, *args)
        self.arguments = dict()

    def __call__(self):
        self.repo = repo_type(self.repo)

        self.repo["issues"].add(**self.arguments)


@add_argument_switches([
    dict(name="title", help=u"The title of the issue"),
    dict(name="body", flagname="--description",
         help=u"The contents of the issue."),
    dict(name="assignee",
         help=u"Login for the user that this issue should be assigned to."),
    dict(name="state",
         help=u"State of the issue (open/closed).",
         completion=ListCompletion("open", "closed")),
    dict(name="milestone",
         help=u"Milestone to associate this issue with."),
    dict(name="labels", flagname="--label", list=True,
         help=u"Labels to associate with this issue")
])
class Update(tpv.cli.Command):
    """Update an issue """

    repo = tpv.cli.SwitchAttr("--repo", str, argname="",
                              help="The repository <user>/<repo>",
                              completion=RepositoryDynamicCompletion())

    def __init__(self, *args):
        tpv.cli.Command.__init__(self, *args)
        self.arguments = dict()

    @tpv.cli.completion(issueno=RepoChildIdDynamicCompletion("issues"))
    def __call__(self, issueno):
        issue = issue_type(self.repo, issueno)
        issue.update(self.arguments)


class Issue(List):
    """Manage issues """
    mine = "all"


class Comment(tpv.cli.Command):
    """Manage comments of an issue"""
    def __call__(self):
        pass


class CommentList(tpv.cli.Command):
    """List comments of an issue """

    repo = tpv.cli.SwitchAttr("--repo", str, argname="",
                              help="The repository <user>/<repo>",
                              completion=RepositoryDynamicCompletion())

    def print_comment(self, comment):
        tmpl = u'''
#{id} {cyanfont}{user[login]}{normalfont}
updated: {updated_at}
{body}
        '''.strip()+"\n"

        print tmpl.format(cyanfont="\033[0;36m", normalfont="\033[0m",
                          **comment).encode('utf-8')

    @tpv.cli.completion(issueno=RepoChildIdDynamicCompletion("issues"))
    def __call__(self, issueno):
        issue = issue_type(self.repo, issueno)

        for comment in issue["comments"].itervalues():
            self.print_comment(comment)


class CommentAdd(tpv.cli.Command):
    """Add a comment """

    repo = tpv.cli.SwitchAttr("--repo", str, argname="",
                              help="The repository <user>/<repo>",
                              completion=RepositoryDynamicCompletion())
    text = tpv.cli.SwitchAttr("--text", str, argname="", help=u"The comment.")

    @tpv.cli.completion(issueno=RepoChildIdDynamicCompletion("issues"))
    def __call__(self, issueno, text=None):
        if text is None:
            text = self.text

        issue = issue_type(self.repo, issueno)
        issue["comments"].add(body=text)


class CommentUpdate(tpv.cli.Command):
    """Edits a comment """

    repo = tpv.cli.SwitchAttr("--repo", str, argname="",
                              help="The repository <user>/<repo>",
                              completion=RepositoryDynamicCompletion())
    text = tpv.cli.SwitchAttr("--text", str, argname="", help=u"The comment.")

    @tpv.cli.completion(commentid=RepoChildIdDynamicCompletion("comments"))
    def __call__(self, commentid, text=None):
        if text is None:
            text = self.text

        repo = repo_type(self.repo)
        repo["comments"][commentid].update(dict(body=text))


class CommentRemove(tpv.cli.Command):
    """Removes a comment """

    repo = tpv.cli.SwitchAttr("--repo", str, argname="",
                              help="The repository <user>/<repo>",
                              completion=RepositoryDynamicCompletion())

    @tpv.cli.completion(commentid=RepoChildIdDynamicCompletion("comments"))
    def __call__(self, commentid):
        repo = repo_type(self.repo)

        del repo["comments"][commentid]
