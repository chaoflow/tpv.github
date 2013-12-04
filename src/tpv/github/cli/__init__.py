"""gh - prototypical unified cli for github
"""

import tpv.cli
import tpv.pkg_resources


class Github(tpv.cli.Command):
    """Prototypical unified github command line.

    Come join the discussion!
    """
    VERSION = "v0"

    def __call__(self):
        self.help()

tpv.pkg_resources.load_entry_points("tpv.github.gh.commands", Github)

app = Github.run
