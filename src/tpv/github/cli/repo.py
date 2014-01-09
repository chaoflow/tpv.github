import tpv.cli
from plumbum.cmd import git

from . import Command
from .types import user_type, repo_type
from .aspects import stdout_to_pager
from .switches import add_argument_switches, ConfigSwitchAttr
from .completion import RepositoryDynamicCompletion, OwnOrgsDynamicCompletion


#@stdout_to_pager
class List(Command):
    """List repos
    """
    def print_repo(self, repo):
        tmpl = u'''
{cyanfont}{name}{normalfont}
Description: {description}
        '''.strip()+"\n"
        if "master_branch" in repo and \
           repo["master_branch"] != "master":
            tmpl += u"master branch: {master_branch}\n"
        if repo["homepage"] is not None and \
           not repo["homepage"].startswith("https://github.com"):
            tmpl += u"homepage: {homepage}\n"
        tmpl += u"updated: {updated_at}\n"

        print tmpl.format(cyanfont="\033[0;36m", normalfont="\033[0m",
                          **repo).encode('utf-8')

    def __call__(self, user=None):
        '''List Repositories
Arguments:
`user` - User owning the repositories
        '''
        user = user_type(user)
        for name, repo in user["repos"].iteritems():
            self.print_repo(repo)


class Repo(List):
    """Manage repos """
    def __call__(self):
        super(Repo, self).__call__()


@add_argument_switches([
    dict(name="description", type=str,
         help="A short description of the repository"),
    dict(name="homepage", type=str,
         help="A URL with more information about the repository"),
    dict(name="private", type=bool, default=False,
         help="Either true to create a private repository, or false to create a public one"),
    dict(name="has_issues", flagname="--no-issues", type=bool, default=True,
         help="Either true to enable issues for this repository, false to disable them"),
    dict(name="has_wiki", flagname="--no-wiki", type=bool, default=True,
         help="Either true to enable the wiki for this repository, false to disable it"),
    dict(name="has_downloads", flagname="--no-downloads", type=bool, default=True,
         help="Either true to enable downloads for this repository, false to disable them"),
    dict(name="team_id", type=int,
         help="The id of the team that will be granted access to this repository"),
    dict(name="auto_init", type=bool, default=False,
         help="Pass true to create an initial commit with empty README"),
    dict(name="gitignore_template", type=str,
         help="Desired language or platform .gitignore template to apply")
])
class Add(Command):
    """Add a new Repo
    """
    org = ConfigSwitchAttr("--org", str, argname="",
                           help="Organization owning the repository",
                           completion=OwnOrgsDynamicCompletion())

    def __call__(self, name=None):
        user = user_type(self.org)

        if name is None:
            name = git['rev-parse', '--show-toplevel']().strip().split('/')[-1]

        user["repos"].add(name=name, **self.arguments)


@add_argument_switches([
    dict(name="name", type=str,
         help="A new name for the repository"),
    dict(name="description", type=str,
         help="A short description of the repository"),
    dict(name="homepage", type=str,
         help="A URL with more information about the repository"),
    dict(name="private", type=bool, default=False,
         help="Either true to create a private repository, or false to create a public one"),
    dict(name="has_issues", flagname="--no-issues", type=bool, default=True,
         help="Either true to enable issues for this repository, false to disable them"),
    dict(name="has_wiki", flagname="--no-wiki", type=bool, default=True,
         help="Either true to enable the wiki for this repository, false to disable it"),
    dict(name="has_downloads", flagname="--no-downloads", type=bool, default=True,
         help="Either true to enable downloads for this repository, false to disable them"),
    dict(name="team_id", type=int,
         help="The id of the team that will be granted access to this repository"),
    dict(name="auto_init", type=bool, default=False,
         help="Pass true to create an initial commit with empty README"),
    dict(name="gitignore_template", type=str,
         help="Desired language or platform .gitignore template to apply")
])
class Update(Command):
    """Update a Repo
    """

    @tpv.cli.completion(repo=RepositoryDynamicCompletion())
    def __call__(self, repo=None):
        '''Updating a repository
Arguments:
`repo` - Repository to be updated
        '''
        repo = repo_type(repo)
        repo.update(self.arguments)
