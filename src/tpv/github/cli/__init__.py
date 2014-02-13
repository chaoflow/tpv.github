"""gh - prototypical unified cli for github
"""

import string
import sys

import tpv.cli
import tpv.pkg_resources

from .switches import ConfigSwitchAttr

# load_entry_points below overwrites the name config by the config module.
from ..github_base import config as config_object


class ColorFormatter(string.Formatter):
    def __init__(self, use_colors=True):
        self.use_colors = use_colors and sys.stdout.isatty()

    def get_field(self, field_name, args, kwargs):
        if field_name.startswith("="):
            return (self.colors[field_name[1:]]
                    if self.use_colors
                    else "", field_name)
        else:
            return super(ColorFormatter, self).get_field(field_name,
                                                         args, kwargs)

ColorFormatter.colors = dict(
    normal="\033[0m",
    black="\033[0;30m",
    blue="\033[0;34m",
    green="\033[0;32m",
    cyan="\033[0;36m",
    red="\033[0;31m",
    purple="\033[0;35m",
    brown="\033[0;33m",
    yellow="\033[1;33m",
    white="\033[1;37m"
)


class Command(tpv.cli.Command):
    use_colors = tpv.cli.Flag("--no-colors", help="Disable colors",
                              default=True)

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        for func, swinfo in self._switches_by_func.iteritems():
            if isinstance(func, ConfigSwitchAttr):
                try:
                    value = config_object[self.PROGNAME][swinfo.names[0]]
                    swinfo.help += (("; " if swinfo.help else "") +
                                    "configured to '{}'".format(value))
                except KeyError:
                    pass

        arguments = getattr(self, "__add_argument_switches__", {})
        if self.PROGNAME in config_object:
            def get_value_and_set_help(value, func):
                self._switches_by_func[func].help += "; configured to '{}'".format(value)
                return value

            self.arguments = dict(
                (name, get_value_and_set_help(value, func))
                for option, value in config_object[self.PROGNAME].iteritems()
                if option in arguments
                for name, func in (arguments[option],)
            )
        else:
            self.arguments = dict()
        self.colors = None

    def format(self, tmpl, **repls):
        if self.colors is None:
            self.colors = ColorFormatter(self.use_colors)

        return self.colors.format(tmpl, **repls).encode("utf-8")


class Github(Command):
    """Prototypical unified github command line.

    Come join the discussion!
    """
    VERSION = "v0"

    @tpv.cli.switch(["-d", "--debug"], argtype=None, list=True)
    def debug(self, value):
        next(config_object.by_files().itervalues()) \
            .setdefault("github", dict())["debug"] = str(len(value))

    def __call__(self):
        self.help()


class Help(Command):
    """Show help """

    def __call__(self):
        self.parent.help()


tpv.pkg_resources.load_entry_points("tpv.github.gh.commands", Github)


# def app():
#     try:
#         Github.run()
#     except Exception as exc:
#         print "Error:", exc.message

app = Github.run
