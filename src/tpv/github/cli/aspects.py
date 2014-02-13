import subprocess
import sys

from metachao import aspect
import tpv.cli


class stdout_to_pager(aspect.Aspect):
    '''Aspect for a Command to reroute all output to stdout into a pager
unless a --no-pager flag is set.

    WARNING: as subprocess isn't able to create full-grown utf-8
    pipes, you will have to make sure utf-8 strings are encoded before
    printing to stdout.
    '''
    no_pager = tpv.cli.Flag("--no-pager", default=False)

    @aspect.plumb
    def __call__(_next, self, *args):
        if self.no_pager:
            return _next(*args)
        else:
            # reroute stdout to pager

            less = subprocess.Popen(["less", "-R"],
                                    stdin=subprocess.PIPE,
                                    stdout=sys.stdout)
            sys.stdout = less.stdin

            try:
                ret = _next(*args)
                less.communicate()
                return ret
            except IOError as err:
                # don't print an error on broken pipe
                if err.errno != 32:
                    raise err
                return 0
            except Exception:
                # make sure to kill the pager in the case of an
                # exception
                less.terminate()
                raise
