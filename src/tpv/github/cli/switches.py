from ConfigParser import ConfigParser

from tpv.cli import Command, switch, SwitchAttr
from ..github_base import config


def make_function(name):
    return lambda self, param: self.arguments.__setitem__(name, param)


def make_bool_function(name, default):
    return lambda self: self.arguments.__setitem__(name, not default)


def add_argument_switches(parameters):
    def deco(cls):
        arguments = {}

        for param in parameters:
            if "flagname" not in param:
                param["flagname"] = "--" + param["name"].replace("_", "-")

            if param.get("type", str) == bool:
                f = make_bool_function(param["name"], param["default"])
                f = switch(param["flagname"],
                           help=param.get("help"))(f)
            else:
                f = switch(param["flagname"],
                           argtype=param.get("type", str),
                           argname="",
                           help=param.get("help"),
                           list=param.get("list", False),
                           completion=param.get("completion", None),
                           mandatory=param.get("mandatory", False)
                           )(make_function(param["name"]))

            setattr(cls, param["name"], f)

            arguments[param["flagname"][2:]] = (param["name"], f)

        init_func = getattr(cls, "__init__")

        def init(self, *args):
            if init_func:
                init_func(self, *args)
            else:
                Command.__init__(self, *args)

            if config.has_section(self.PROGNAME):
                def get_value_and_set_help(option, func):
                    value = config.get(self.PROGNAME, option)
                    self._switches_by_func[func].help += "; configured to '{}'".format(value)
                    return value

                self.arguments = dict(
                    (name, get_value_and_set_help(option, func))
                    for option in config.options(self.PROGNAME)
                    if option in arguments
                    for name, func in (arguments[option],)
                    )
            else:
                self.arguments = dict()

        setattr(cls, "__init__", init)

        return cls
    return deco


class ConfigSwitchAttr(SwitchAttr):
    def __get__(self, inst, cls):
        if isinstance(config, ConfigParser):
            argtype = self._switch_info.argtype
            name = self._switch_info.names[0]
            if argtype and config.has_option(inst.PROGNAME, name):
                if self._switch_info.list:
                    self._default_value = [
                        argtype(x)
                        for x in config.get(inst.PROGNAME, name).split(",")
                    ]
                else:
                    self._default_value = argtype(config.get(inst.PROGNAME,
                                                             name))

        return super(ConfigSwitchAttr, self).__get__(inst, cls)
