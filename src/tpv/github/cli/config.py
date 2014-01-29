import os
import tpv.cli

from . import Command
from ..github_base import config


class Config(Command):
    """Show config """

    verbose = tpv.cli.Flag("-v", default=False,
                           help="List all config parameters")

    def print_config(self, fn, config, verbose):
        tmpl = u"{=cyan}{filename}{=normal}"
        print self.format(tmpl, filename=fn.replace(os.getenv("HOME"), "~"))
        if verbose:
            for option, value in (("{}.{}".format(section, option), value)
                                  for section, sec_config in config.iteritems()
                                  for option, value in sec_config.iteritems()):
                print "{} = {}".format(option, value)
            print ""

    def __call__(self):
        for fn, file_config in config.by_files().iteritems():
            self.print_config(fn, file_config, self.verbose)
