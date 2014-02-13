import sys

from . import Command
from ..github import authenticated_user
from .types import user_type
from .switches import add_argument_switches


class Show(Command):
    """Show users
    """

    def print_user(self, user):
        tmpl = u"{=cyan}{login}"
        if "name" in user or "email" in user:
            tmpl += " - " + (u"{name} "
                             if "name" in user and user["name"] is not None
                             else "") \
                    + (u"<{email}>"
                       if "email" in user and user["email"] is not None
                       else "")
        tmpl += u"{=normal}\n"

        if user["type"] != "User":
            tmpl += u"Type: {type}\n"
        if "company" in user and user["company"] is not None:
            tmpl += u"Company: {company}\n"
        if "location" in user and user["location"] is not None:
            tmpl += u"Location: {location}\n"

        print self.format(tmpl, **user)

    def __call__(self, *users):
        if len(users) < 1:
            users = [authenticated_user()]

        for user in users:
            try:
                self.print_user(user_type(user))
            except ValueError:
                print >> sys.stderr, "User {} does not exist.".format(user)


@add_argument_switches([
    dict(keyname="name",
         help="The new name of the user"),
    dict(keyname="email",
         help="Publicly visible email address."),
    dict(keyname="blog",
         help="The new blog URL of the user."),
    dict(keyname="company",
         help="The new company of the user."),
    dict(keyname="location",
         help="The new location of the user."),
    dict(keyname="hireable",
         help="The new hiring availability of the user (true/false)."),
    dict(keyname="bio",
         help="The new short biography of the user.")
])
class Update(Command):
    """Update user info of the authenticated user
    """

    def __call__(self):
        self.user = user_type(authenticated_user())
        self.user.update(self.arguments)


class User(Show):
    '''Manage own user '''
    pass
