
import tpv.cli
#from aspects import stdout_to_pager

from . import Command
from ..github_base import set_on_new_dict, extract_repo_from_issue_url
from .types import repo_type, issue_type, user_type
from .switches import add_argument_switches, ConfigSwitchAttr
from tpv.cli import ListCompletion
from .completion import \
    RepositoryDynamicCompletion, \
    RepoChildIdDynamicCompletion


@add_argument_switches([
    dict(keyname="milestone", help=u"milestone number or '*' for any"),
    dict(keyname="state", help=u"Indicates the state of the issues to return. Can be either all, open or closed.", completion=ListCompletion("all", "open","closed")),
    dict(keyname="assignee", help=u"Can be the name of a user. Pass in none for issues with no assigned user, and * for issues assigned to any user."),
    dict(keyname="creator", help=u"The user that created the issue"),
    dict(keyname="mentioned", help=u"A user that's mentioned in the issue"),
    dict(keyname="labels", help=u"A list of comma separated label names"),
    dict(keyname="sort", help=u"What to sort results by. Can be either created, updated, comments."),
    dict(keyname="direction", help=u"The direction of the sort. Can be either asc or desc.", completion=ListCompletion("asc","desc")),
    dict(keyname="since", help=u"Only issues updated at or after this time are returned (YYYY-MM-DDTHH:MM:SSZ).")
])
#@stdout_to_pager
class List(Command):
    """List issues matching filter criteria

The use of the stdout_to_pager aspect confuses plumbum into thinking
we accept a list of nondescript arguments, which blocks proper
completion of the options.

    """
    verbose = tpv.cli.Flag(["--verbose", "-v"],
                           help="Print more details on the issues")

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())

    mine = ConfigSwitchAttr("--mine", str, argname="",
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

    def print_issue(self, issue):
        if self.verbose:
            self.print_issue_long(issue)
        else:
            self.print_issue_short(issue)

    def print_issue_short(self, issue):
        tmpl = u"#{number}"
        if self.mine is not None and self.repo is None:
            (user, repo) = extract_repo_from_issue_url(issue["url"])
            tmpl += " :{}/{}".format(user, repo)
        tmpl += " {=cyan}{title}{=normal}"
        if issue["assignee"] is not None:
            tmpl += " @{assignee[login]}"

        print self.format(tmpl, **issue)

    def print_issue_long(self, issue):
        tmpl = u"#{number} {=cyan}{title}{=normal}\n"
        if self.mine is not None and self.repo is None:
            (user, repo) = extract_repo_from_issue_url(issue["url"])
            tmpl += "Repo: {}/{}\n".format(user, repo)
        tmpl += '''
State: {state}
Author: {user[login]}
        '''.strip()+"\n"

        if issue["assignee"] is not None:
            tmpl += "Assignee: {assignee[login]}\n"

        print self.format(tmpl, **issue)

    def __call__(self):
        # the backend by default returns all issues. if the cli user
        # doesn't specify the state, show the open ones. if he sets
        # state to all, don't pass it along to the backend. if he sets
        # state to closed, the backend returns the closed ones, anyway.
        if "state" not in self.arguments:
            self.arguments["state"] = "open"
        elif self.arguments["state"] == "all":
            del self.arguments["state"]

        # the mine attribute can be set to "all" (default for the call
        # to "gh issue"), "assigned", "created", "mentioned",
        # "subscribed"

        if self.mine is None:
            # it has been omitted => show the issues of the current
            # repository
            repo = repo_type(self.repo)
            issues = repo["issues"].search(**self.arguments)
        elif self.repo is None:
            # if mine is set and no repo is explicitly provided
            # show user issues
            user = user_type(None)
            arguments = set_on_new_dict(self.arguments,
                                        "filter", self.mine)
            issues = user["issues"].search(**arguments)
        else:
            # if mine is set together with an explicit repository, we
            # list the issues by searching the issues of this repository;
            # thus mine can not be set to all

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


class Show(Command):
    """Show a list of issues by their issuenumber """

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())

    with_comments = tpv.cli.Flag("--no-comments",
                                 help="Don't print comments",
                                 default=True)

    def print_comment(self, comment):
        tmpl = u'''
#{id} {=cyan}{user[login]}{=normal}
updated: {updated_at}
{body}
        '''.strip()+"\n"

        print self.format(tmpl, **comment)

    def print_issue(self, issue):
        tmpl = u'''
#{number} {=cyan}{title}{=normal}
State: {state}
Author: {user[login]}
Updated: {updated_at}
        '''.strip()+"\n"
        if issue["assignee"] is not None:
            tmpl += u"Assignee: {assignee[login]}\n"
        if len(issue["body"]) > 0:
            tmpl += u"\n{body}\n"

        print self.format(tmpl, **issue)

        if self.with_comments:
            print self.format("{=cyan}Comments:{=normal}")

            for comment in issue["comments"].itervalues():
                self.print_comment(comment)

    @tpv.cli.completion(issuenumbers=RepoChildIdDynamicCompletion("issues"))
    def __call__(self, *issuenumbers):
        self.repo = repo_type(self.repo)

        for issueno in issuenumbers:
            issue = issue_type(self.repo, issueno)
            self.print_issue(issue)


@add_argument_switches([
    dict(keyname="milestone", help=u"milestone number or '*' for any"),
    dict(keyname="title", help=u"The title of the issue", mandatory=True),
    dict(keyname="body", swname="description",
         help=u"The contents of the issue."),
    dict(keyname="assignee",
         help=u"Login for the user that this issue should be assigned to."),
    dict(keyname="milestone",
         help=u"Milestone to associate this issue with."),
    dict(keyname="labels", swname="label", list=True,
         help=u"Labels to associate with this issue")
])
class Add(Command):
    """Add a new issue """

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())

    def __call__(self):
        self.repo = repo_type(self.repo)

        self.repo["issues"].add(**self.arguments)


@add_argument_switches([
    dict(keyname="title", help=u"The title of the issue"),
    dict(keyname="body", swname="description",
         help=u"The contents of the issue."),
    dict(keyname="assignee",
         help=u"Login for the user that this issue should be assigned to."),
    dict(keyname="state",
         help=u"State of the issue (open/closed).",
         completion=ListCompletion("open", "closed")),
    dict(keyname="milestone",
         help=u"Milestone to associate this issue with."),
    dict(keyname="labels", swname="label", list=True,
         help=u"Labels to associate with this issue")
])
class Update(Command):
    """Update an issue """

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())

    @tpv.cli.completion(issueno=RepoChildIdDynamicCompletion("issues"))
    def __call__(self, issueno):
        issue = issue_type(self.repo, issueno)
        issue.update(self.arguments)


class Issue(List):
    """Manage issues """

    # gh issue lists all user issues
    mine = "all"


class Comment(Command):
    """Manage comments of an issue"""
    def __call__(self):
        pass


class CommentList(Command):
    """List comments of an issue """

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())

    def print_comment(self, comment):
        tmpl = u'''
#{id} {=cyan}{user[login]}{=normal}
updated: {updated_at}
{body}
        '''.strip()+"\n"

        print self.format(tmpl, **comment)

    @tpv.cli.completion(issueno=RepoChildIdDynamicCompletion("issues"))
    def __call__(self, issueno):
        issue = issue_type(self.repo, issueno)

        for comment in issue["comments"].itervalues():
            self.print_comment(comment)


class CommentAdd(Command):
    """Add a comment """

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())
    text = ConfigSwitchAttr("--text", str, argname="", help=u"The comment.")

    @tpv.cli.completion(issueno=RepoChildIdDynamicCompletion("issues"))
    def __call__(self, issueno, text=None):
        if text is None:
            text = self.text

        issue = issue_type(self.repo, issueno)
        issue["comments"].add(body=text)


class CommentUpdate(Command):
    """Edits a comment """

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())
    text = ConfigSwitchAttr("--text", str, argname="", help=u"The comment.")

    @tpv.cli.completion(commentid=RepoChildIdDynamicCompletion("comments"))
    def __call__(self, commentid, text=None):
        if text is None:
            text = self.text

        repo = repo_type(self.repo)
        repo["comments"][commentid].update(dict(body=text))


class CommentRemove(Command):
    """Removes a comment """

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())

    @tpv.cli.completion(commentid=RepoChildIdDynamicCompletion("comments"))
    def __call__(self, commentid):
        repo = repo_type(self.repo)

        del repo["comments"][commentid]
