"""gh - prototypical unified cli for github
"""

import tpv.cli
import tpv.pkg_resources

from ..github_base import config


class Github(tpv.cli.Command):
    """Prototypical unified github command line.

    Come join the discussion!
    """
    VERSION = "v0"

    @tpv.cli.switch(["-d", "--debug"], argtype=None, list=True)
    def debug(self, value):
        config.set("github", "debug", str(len(value)))

    def __call__(self):
        self.help()


class Help(tpv.cli.Command):
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
