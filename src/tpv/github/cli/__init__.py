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
    """A formatter which replaces color placeholders from a dictionary

{=<color name>} is replaced by colors["<color name>"].
No colors are used if stdout is not connected to a tty.

Usage:
ColorFormatter().format(string_with_colors, ...)
    """
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

# define commonly used terminal color codes
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
    """Base class for all (sub)commands of the gh cli utility """

    no_colors = tpv.cli.Flag("--no-colors", help="Disable colors")

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        # The help text belonging to each ConfigSwitchAttr-attributes
        # shows default values configured in a config file.

        try:
            config_section = config_object[self.PROGNAME]
        except KeyError:
            config_section = {}

        if config_section:
            for func, swinfo in self._switches_by_func.iteritems():
                if isinstance(func, ConfigSwitchAttr) \
                   or hasattr(func, "__is_add_argument_switch__"):
                    try:
                        value = config_object[self.PROGNAME][swinfo.names[0]]
                        swinfo.help += (("; " if swinfo.help else "") +
                                        "configured to '{}'".format(value))
                    except KeyError:
                        pass

        # Prepare self.arguments, from default values and config values

        # __add_argument_switches__ is created by the
        # add_argument_switches decorator and holds a list
        # [ ("<keyname>", "<swname>", "<default value>"), ... ]

        arguments = getattr(self, "__add_argument_switches__", [])
        self.arguments = dict(
            (keyname, config_section.get(swname, default))
            for keyname, swname, default in arguments
            if swname in config_section or default is not None)

        self.colors = None

    def format(self, tmpl, **repls):
        """Return `tmpl` formatted by ColorFormatter """
        if self.colors is None:
            self.colors = ColorFormatter(not self.no_colors)

        return self.colors.format(tmpl, **repls).encode("utf-8")


class Github(Command):
    """Prototypical unified github command line.

    Come join the discussion!
    """
    VERSION = "v0"

    @tpv.cli.switch(["-d", "--debug"], argtype=None, list=True)
    def debug(self, value):
        """Increase debug level"""
        try:
            level = int(config_object["github.debug"])
        except KeyError:
            level = 0
        # set "github.debug" in the most specific config dictionary
        next(config_object.by_files().itervalues()) \
            .setdefault("github", dict())["debug"] = str(level + len(value))

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
