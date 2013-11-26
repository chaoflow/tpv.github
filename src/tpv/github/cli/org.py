import sys
import tpv.cli

from .types import user_type, org_type
from .decorators import add_argument_switches

from .user import Show as UserShow


class Org(tpv.cli.Command):
    """Manage organizations
    """
    def __call__(self):
        pass


class Show(UserShow):
    """Show Org
    """


@add_argument_switches([
    dict(name="name",
         help="The shorthand name of the company."),
    dict(name="email",
         help="Publicly visible email address."),
    dict(name="company",
         help="The company name."),
    dict(name="location",
         help="The location."),
    dict(name="billing_email",
         help="Billing email address. Not public.")
])
class Update(tpv.cli.Command):
    """Update organization info of the organization <org>
    """

    def __init__(self, *args, **kwargs):
        tpv.cli.Command.__init__(self, *args, **kwargs)
        self.arguments = dict()

    def __call__(self, org):
        org = org_type(org)
        org.update(self.arguments)


class Members(tpv.cli.Command):
    """Manage members of an organization
    """
    def __call__(self):
        pass


class MemList(tpv.list.Command):
    """List members of an organization"""

    team = tpv.cli.SwitchAttr("--team", argtype=str,
                              help="Team from which to list the members")

    def __call__(self, org_name):
        org = org_type(org_name)

        if self.team is not None:
            try:
                team =  org["teams"][self.team]
            except KeyError:
                raise ValueError("No team `{}` in the organization `{}`"
                                 .format(self.team, org['name']))

            for member in team["members"]:
                self.print_member(member)
        else:
            for member in org["members"]:
                self.print_member(member)


class MemAdd(tpv.cli.Command):
    '''Add members to the team of an organization'''

    team = tpv.cli.SwitchAttr("--team", argtype=str,
                              help="Team from which to list the members")

    def __call__(self, org, *users):
        org = org_type(org)
        team = team_type(org, self.team)

        for user_name in users:
            try:
                user = user_type(user_name)
                team["members"][user['login']] = {}
            except ValueError:
                print >> sys.stderr, "User `{}` not found, ignoring.".format(user_name)


class MemRemove(tpv.cli.Command):
    '''Remove members from an organization or teams of an organization'''

    team = tpv.cli.SwitchAttr("--team", argtype=str,
                              help="Team from which to list the members")

    def __call__(self, org, *users):
        org = org_type(org)
        if self.team is not None:
            removefrom = team_type(org, self.team)
        else:
            removefrom = org

        for user_name in users:
            try:
                del removefrom["members"][user_name]
            except KeyError:
                print >> sys.stderr, "User `{}` not a member, ignoring.".format(user_name)
