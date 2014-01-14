import tpv.cli
from aspects import stdout_to_pager

from . import Command
from ..github import set_on_new_dict
from .types import repo_type, pull_type, user_type
from .switches import add_argument_switches, ConfigSwitchAttr
from tpv.cli import ListCompletion
from .completion import \
    RepositoryDynamicCompletion, \
    RepoChildIdDynamicCompletion


@add_argument_switches([
    dict(name="state", help=u"Indicates the state of the pulls to return. Can be either open or closed.", completion=ListCompletion("open","closed")),
    dict(name="head", help=u"Filter pulls by head user and branch name in the format of user:ref-name. Example: github:new-script-format."),
    dict(name="base", help=u"Filter pulls by base branch name. Example: gh-pages.")
])
#@stdout_to_pager
class List(Command):
    """List pulls matching filter criteria

The use of the stdout_to_pager aspect confuses plumbum into thinking
we accept a list of nondescript arguments, which blocks proper
completion of the options.

    """
    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())

    def print_pull(self, pull):

        tmpl = u'''
#{number} {=cyan}{title}{=normal}
State: {state}
Head: {base[label]}
Base: {head[label]}
Updated at: {updated_at}
{body}
        '''.strip()+"\n"

        print self.format(tmpl, **pull)

    def __call__(self):
        repo = repo_type(self.repo)
        pulls = repo["pulls"].search(**self.arguments)

        for no, pull in pulls:
            self.print_pull(pull)


class Show(Command):
    """Show a list of pulls by their pullnumber """

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())

    with_comments = tpv.cli.Flag("--no-comments",
                                 help="Don't print comments",
                                 default=True)

    def print_reviewcomments(self, hunk):
        print ""  # newline

        tmpl = u'''
Path: {path}
{diff_hunk}
        '''.strip() + "\n"
        print self.format(tmpl, **hunk[0])

        for comment in hunk:
            commenttmpl = u'''
#{id} {=cyan}{user[login]}{=normal}
updated: {updated_at}
{body}
            '''.strip()+"\n"

            print self.format(tmpl, **comment)

    def print_comment(self, comment):
        tmpl = u'''
#{id} {=cyan}{user[login]}{=normal}
updated: {updated_at}
{body}
        '''.strip()+"\n"

        print self.format(tmpl, **comment)

    def print_pull(self, pull):
        tmpl = u'''
#{number} {=cyan}{title}{=normal}
State: {state}
Head: {base[label]}
Base: {head[label]}
Updated at: {updated_at}
{body}
        '''.strip()+"\n"

        print self.format(tmpl, **pull)

        if self.with_comments:
            hunks = dict()
            for comment in pull["comments"].itervalues():
                hunks.setdefault(comment["original_position"],
                                 []).append(comment)

            print self.format("{=cyan}Review Comments:{=normal}")
            for hunk in hunks.itervalues():
                self.print_reviewcomments(hunk)

            print self.format("{=cyan}Comments:{=normal}\n")

            for comment in pull["issue"]["comments"].itervalues():
                self.print_comment(comment)

    @tpv.cli.completion(pullnumbers=RepoChildIdDynamicCompletion("pulls"))
    def __call__(self, *pullnumbers):
        self.repo = repo_type(self.repo)

        for pullno in pullnumbers:
            pull = pull_type(self.repo, pullno)
            self.print_pull(pull)


@add_argument_switches([
    dict(name="title", help=u"The title of the pull", mandatory=True),
    dict(name="head", help=u"The branch, where your changes are implemented.", mandatory=True),
    dict(name="base", help=u"The branch, where you want your changes pulled into.", mandatory=True),
    dict(name="body", flagname="--description",
         help=u"The contents of the pull."),
])
class Add(Command):
    """Add a new pull """

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())

    def __call__(self):
        self.repo = repo_type(self.repo)

        self.repo["pulls"].add(**self.arguments)


@add_argument_switches([
    dict(name="title", help=u"The title of the pull"),
    dict(name="body", flagname="--description",
         help=u"The contents of the pull."),
    dict(name="state",
         help=u"State of the pull (open/closed).",
         completion=ListCompletion("open", "closed"))
])
class Update(Command):
    """Update a pull """

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())

    @tpv.cli.completion(pullno=RepoChildIdDynamicCompletion("pulls"))
    def __call__(self, pullno):
        pull = pull_type(self.repo, pullno)
        pull.update(self.arguments)


class Pull(List):
    """Manage pulls """


class Comment(Command):
    """Manage comments of a pull"""
    def __call__(self):
        pass


class CommentList(Command):
    """List comments of a pull """

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

    @tpv.cli.completion(pullno=RepoChildIdDynamicCompletion("pulls"))
    def __call__(self, pullno):
        pull = pull_type(self.repo, pullno)

        for comment in pull["issue"]["comments"].itervalues():
            self.print_comment(comment)


class CommentAdd(Command):
    """Add a comment """

    repo = ConfigSwitchAttr("--repo", str, argname="",
                            help="The repository <user>/<repo>",
                            completion=RepositoryDynamicCompletion())
    text = ConfigSwitchAttr("--text", str, argname="", help=u"The comment.")

    @tpv.cli.completion(pullno=RepoChildIdDynamicCompletion("pulls"))
    def __call__(self, pullno, text=None):
        if text is None:
            text = self.text

        pull = pull_type(self.repo, pullno)
        pull["issue"]["comments"].add(body=text)


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
