import tpv.cli


class Pullrequests(tpv.cli.Command):
    """Manage pullrequests
    """
    def __call__(self):
        pass


class List(tpv.cli.Command):
    """List pull requests matching filter criteria
    """
    def __call__(self):
        pass


class Show(tpv.cli.Command):
    """Show a list of pull requests by their pull request number
    """
    def __call__(self, *numbers):
        pass


class Add(tpv.cli.Command):
    """Add a new pull request
    """
    def __call__(self):
        pass
