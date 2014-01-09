"""gh - prototypical unified cli for github
"""

import tpv.cli
import tpv.pkg_resources

from .switches import ConfigSwitchAttr
from ..github_base import config


class Command(tpv.cli.Command):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        for func, swinfo in self._switches_by_func.iteritems():
            if isinstance(func, ConfigSwitchAttr) and \
               config.has_option(self.PROGNAME, swinfo.names[0]):
                value = config.get(self.PROGNAME, swinfo.names[0])
                swinfo.help += ("; " if swinfo.help else "") + \
                               "configured to '{}'".format(value)



class Github(Command):
    """Prototypical unified github command line.

    Come join the discussion!
    """
    VERSION = "v0"

    @tpv.cli.switch(["-d", "--debug"], argtype=None, list=True)
    def debug(self, value):
        config.set("github", "debug", str(len(value)))

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
