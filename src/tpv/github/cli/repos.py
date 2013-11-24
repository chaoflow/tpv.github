import tpv.cli
from plumbum.cmd import git

from .types import owner_type, repo_type
from aspects import stdout_to_pager


def make_function(name):
    return lambda self, param: self.arguments.__setitem__(name, param)

def make_bool_function(name, default):
    return lambda self: self.arguments.__setitem__(name, not default)

def add_argument_switches(parameters):
    def deco(cls):
        for param in parameters:
            if "flagname" not in param:
                param["flagname"]  = "--" + param["name"].replace("_", "-")

            if param.get("type", str) == bool:
                f = tpv.cli.switch(param["flagname"],
                                   help=param.get("help"))(make_bool_function(param["name"], param["default"]))
            else:
                f = tpv.cli.switch(param["flagname"],
                                   argtype=param.get("type", str),
                                   help=param.get("help"))(make_function(param["name"]))

            setattr(cls, param["name"], f)
        return cls
    return deco


class Repos(tpv.cli.Command):
    """Manage repos
    """
    def __call__(self):
        pass


@stdout_to_pager
class List(tpv.cli.Command):
    """List repos
    """
    owner = tpv.cli.SwitchAttr("--owner", owner_type,
                               help="The repository owner")

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

        print tmpl.format(cyanfont="\033[0;36m", normalfont="\033[0m", **repo)

    def __call__(self):
        if self.owner is None:
            self.owner = owner_type(None)

        for name, repo in self.owner["repos"].iteritems():
            self.print_repo(repo)


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
class Add(tpv.cli.Command):
    """Add a new Repo
    """
    owner = tpv.cli.SwitchAttr("--owner", owner_type,
                               help="The repository owner")

    def __init__(self, *args, **kwargs):
        tpv.cli.Command.__init__(self, *args, **kwargs)
        self.arguments = dict()

    def __call__(self, name=None):
        if self.owner is None:
            self.owner = owner_type(None)

        if name is None:
            name = git['rev-parse', '--show-toplevel']().strip().split('/')[-1]

        self.owner["repos"][name] = self.arguments


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
class Update(tpv.cli.Command):
    """Update a Repo
    """
    repo = tpv.cli.SwitchAttr("--repo", repo_type,
                              help="The repository")

    def __init__(self, *args, **kwargs):
        tpv.cli.Command.__init__(self, *args, **kwargs)
        self.arguments = dict()

    def __call__(self, name=None):
        if self.repo is None:
            self.repo = repo_type(None)

        self.repo.update(self.arguments)
