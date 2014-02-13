from tpv.cli import switch, SwitchAttr
from ..github_base import DictConfigParser, config


def make_function(keyname):
    """Create a new method for switch with `keyname` """
    def f(self, param):
        self.arguments[keyname] = param
    return f


def make_bool_function(keyname, default):
    def f(self):
        self.arguments[keyname] = not default
    return f


def add_argument_switches(parameters):
    """Decorator for adding a list of switches to a Command

The decorator takes a list of parameters. Each parameter is defined by
a dictionary, with the following keys:

`keyname`    -- name of the key in self.arguments.
`swname`     -- name of the switch for plumbum; typically inferred from keyname
                by replacing _ with -.
`argtype`    -- type of the argument, defaults to str.
`help`       -- help text for the switch.
`list`       -- whether the switch can be repeated;
                self.arguments then holds a list.
`mandatory`  -- whether the sitch is mandatory.
`completion` -- completion object.
`default`    -- the default value of the switch;
                only for switches with argtype==bool.

The argument supplied to each switch is stored in the dictionary
`arguments` on the Command instance.


Usage:

@add_argument_switches([
    dict(keyname="repo_names", swname="repo", list=True,
         help="The repositories to add the team to",
         completion=RepositoryDynamicCompletion()),
    dict(keyname="permission",
         help="The permission to grant the team. One of pull, push or admin.",
         completion=ListCompletion("pull", "push", "admin"))
])
class TeamAdd(Command):
    [...]

then:

gh team add --repo repo1 --repo repo2
will lead to
teamadd.arguments["repo_names"] = ["repo1", "repo2"]
where teamadd represents the instance of TeamAdd.

    """

    def deco(cls):
        arguments = []

        for param in parameters:
            if "swname" not in param:
                param["swname"] = param["keyname"].replace("_", "-")

            argtype = param.get("argtype", str)
            if argtype == bool:
                f = make_bool_function(param["keyname"], param["default"])
                f = switch(param["swname"], help=param.get("help"))(f)
            else:
                f = switch(param["swname"],
                           argtype=argtype,
                           argname="",
                           help=param.get("help"),
                           list=param.get("list", False),
                           completion=param.get("completion", None),
                           mandatory=param.get("mandatory", False)
                           )(make_function(param["keyname"]))

            # marks the function, so that Command.__init__ show its
            # configured default values in the help text
            setattr(f, "__is_add_argument_switch__", True)

            # after applying the switch decorator, we add the method
            # to the class (Command)
            setattr(cls, param["keyname"], f)
            arguments.append((param["keyname"], param["swname"],
                              param.get("default", None)))

        # the attribute __add_argument_switches__ will be used by
        # Command.__init__ to prepare the arguments dictionary
        setattr(cls, "__add_argument_switches__", arguments)

        return cls
    return deco


class ConfigSwitchAttr(SwitchAttr):
    """SwitchAttr with configurable default values"""
    def __get__(self, inst, cls):
        """Return the value of the switch attribute

Before returning the value by delegating back to SwitchAttr.__get__,
set the default value from the config file.

Can't be done by __init__ or any other method prior to __get__, as we
need the Command instance for knowing inst.PROGNAME.
        """
        if isinstance(config, DictConfigParser):
            argtype = self._switch_info.argtype
            name = self._switch_info.names[0]
            if argtype:
                try:
                    if self._switch_info.list:
                        self._default_value = [
                            argtype(x)
                            for x in config[inst.PROGNAME][name].split(",")
                        ]
                    else:
                        self._default_value = \
                            argtype(config[inst.PROGNAME][name])
                except KeyError:
                    pass
        return super(ConfigSwitchAttr, self).__get__(inst, cls)
