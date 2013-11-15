import tpv.cli


class Issues(tpv.cli.Command):
    """Manage issues
    """
    def __call__(self):
        pass


class List(tpv.cli.Command):
    """List issues matching filter criteria
    """
    def __call__(self):
        pass


class Show(tpv.cli.Command):
    """Show a list of issues by their issuenumber
    """
    def __call__(self, *issuenumbers):
        for issueno in issuenumbers:
            # great stuff to happen here
            pass


class Add(tpv.cli.Command):
    """Add a new issue
    """
    def __call__(self):
        pass
