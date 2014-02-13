import sys
import tpv.cli

from tpv.cli import ListCompletion

from . import Command
from .types import user_type, org_type, team_type, repo_type
from .switches import add_argument_switches, ConfigSwitchAttr
from .completion import \
    OwnOrgsDynamicCompletion, \
    RepositoryDynamicCompletion, \
    TeamDynamicCompletion, \
    TeamOrgMembersDynamicCompletion

from .user import Show as UserShow


class Org(Command):
    """Manage organisations """

    def __call__(self):
        """List organizations of authenticated user"""
        user = user_type(None)
        print ", ".join(user["orgs"])


class Show(UserShow):
    """Show Org

For now does the same, as UserShow. but extra information like showing
members, teams and/or repos are possible.
    """

    @tpv.cli.completion(orgs=OwnOrgsDynamicCompletion())
    def __call__(self, *orgs):
        super(Show, self).__call__(*orgs)


@add_argument_switches([
    dict(keyname="name",
         help="The shorthand name of the company."),
    dict(keyname="email",
         help="Publicly visible email address."),
    dict(keyname="company",
         help="The company name."),
    dict(keyname="location",
         help="The location."),
    dict(keyname="billing_email",
         help="Billing email address. Not public.")
])
class Update(Command):
    """Update organisation info of the organisation <org> """

    @tpv.cli.completion(org=OwnOrgsDynamicCompletion())
    def __call__(self, org):
        org = org_type(org)
        org.update(self.arguments)


class Member(Command):
    """Manage members of an organisation """
    def __call__(self):
        pass


class MemList(Command):
    """List members of an organisation """

    # TODO to complete teams one would have to adapt the
    # plumbum.cli.completions.complete method so that it passes the
    # tailargs to the completion objects.
    team = ConfigSwitchAttr("--team", argtype=str, argname="",
                            help="Team from which to list the members")

    def print_member(self, member):
        tmpl = u"""
{=cyan}{login}{=normal}
id: {id}
site_admin: {site_admin}
        """.strip()+"\n"
        print self.format(tmpl, **member)

    @tpv.cli.completion(org_name=OwnOrgsDynamicCompletion())
    def __call__(self, org_name):
        org = org_type(org_name)

        if self.team is not None:
            # with the team switch, show members of the team
            try:
                team = team_type(org, self.team)
            except KeyError:
                raise ValueError("No team `{}` in the organisation `{}`"
                                 .format(self.team, org['login']))

            for login, member in team["members"].iteritems():
                self.print_member(member)
        else:
            # without the team switch, show members of the organisation
            for login, member in org["members"].iteritems():
                self.print_member(member)


class MemAdd(Command):
    '''Add members to the team of an organisation '''

    team = ConfigSwitchAttr("--team", argtype=str, argname="",
                            help="Team to which to add members",
                            completion=TeamDynamicCompletion())

    @tpv.cli.completion(org=OwnOrgsDynamicCompletion())
    def __call__(self, org, *users):
        org = org_type(org)
        team = team_type(org, self.team)

        for user_name in users:
            try:
                user = user_type(user_name)
                team["members"].add(login=user['login'])
            except ValueError:
                print >> sys.stderr, \
                    "User `{}` not found, ignoring.".format(user_name)


class MemRemove(Command):
    '''Remove members from an organisation or teams of an organisation '''

    team = ConfigSwitchAttr("--team", argtype=str, argname="",
                            help="Team from which to list the members",
                            completion=TeamDynamicCompletion())

    @tpv.cli.completion(org=OwnOrgsDynamicCompletion(),
                        users=TeamOrgMembersDynamicCompletion())
    def __call__(self, org, *users):
        org = org_type(org)

        # remove the member either from the given team or from the
        # organisation (which means from all teams)
        if self.team is not None:
            removefrom = team_type(org, self.team)
        else:
            removefrom = org

        for user_name in users:
            try:
                del removefrom["members"][user_name]
            except KeyError:
                print >> sys.stderr, \
                    "User `{}` not a member, ignoring.".format(user_name)


class Team(Command):
    """Manage teams of an organisation """
    def __call__(self):
        pass


class TeamList(Command):
    '''List teams of an organisation '''

    def print_team(self, team):
        print "{name} ({id})\n".format(**team)

    @tpv.cli.completion(org=OwnOrgsDynamicCompletion())
    def __call__(self, org):
        org = org_type(org)

        for team in org["teams"].itervalues():
            self.print_team(team)


class TeamShow(Command):
    """Show one team with its members and so on """

    def print_team(self, team):
        tmpl = u"""
{=cyan}{name}{=normal} ({id})
members count: {members_count}
repos count: {repos_count}
members: {members}
        """.strip()
        print self.format(tmpl,
                          members=", ".join(m["login"]
                                            for m in team["members"].itervalues()),
                          **team)

    @tpv.cli.completion(org=OwnOrgsDynamicCompletion(),
                        team=TeamDynamicCompletion())
    def __call__(self, org, team):
        team = team_type(org, team)
        self.print_team(team)


@add_argument_switches([
    dict(keyname="repo_names", swname="repo", list=True,
         help="The repositories to add the team to",
         completion=RepositoryDynamicCompletion()),
    dict(keyname="permission",
         help="The permission to grant the team. One of pull, push or admin.",
         completion=ListCompletion("pull", "push", "admin"))
])
class TeamAdd(Command):
    """Add a team to an organisation """

    @tpv.cli.completion(org=OwnOrgsDynamicCompletion(),
                        team=TeamDynamicCompletion())
    def __call__(self, org, team):
        org = org_type(org)

        if 'repo_names' in self.arguments:
            self.arguments['repo_names'] = \
                [repo_type(x, org['login'])['full_name']
                 for x in self.arguments['repo_names']]
        org["teams"].add(name=team, **self.arguments)


class TeamRemove(Command):
    """Remove a team from an organisation """

    @tpv.cli.completion(org=OwnOrgsDynamicCompletion(),
                        team=TeamDynamicCompletion())
    def __call__(self, org, team):
        org = org_type(org)
        team = team_type(org, team)
        del org["teams"][team["id"]]


class TeamRepo(Command):
    """Manage repos of of an organisation's teams """
    def __call__(self):
        pass


class TeamRepoList(Command):
    """List team repos """

    def print_repo(self, repo):
        tmpl = """
{=cyan}{name}{=normal}
{description}
        """.strip() + "\n"
        print self.format(tmpl, **repo)

    @tpv.cli.completion(org=OwnOrgsDynamicCompletion(),
                        team=TeamDynamicCompletion())
    def __call__(self, org, team):
        team = team_type(org, team)
        for repo in team["repos"].itervalues():
            self.print_repo(repo)


class TeamRepoAdd(Command):
    """Add repos to an organisation's team """

    @tpv.cli.completion(org=OwnOrgsDynamicCompletion(),
                        team=TeamDynamicCompletion(),
                        repo=RepositoryDynamicCompletion())
    def __call__(self, org, team, repo):
        org = org_type(org)
        team = team_type(org, team)
        repo = repo_type(repo, org["login"])

        team["repos"].add(name=repo["full_name"])


class TeamRepoRemove(Command):
    """Remove repos from an organisation's team """

    @tpv.cli.completion(org=OwnOrgsDynamicCompletion(),
                        team=TeamDynamicCompletion(),
                        repo=RepositoryDynamicCompletion())
    def __call__(self, org, team, repo):
        org = org_type(org)
        team = team_type(org, team)
        repo = repo_type(repo, org["login"])

        del team["repos"][repo["full_name"]]
