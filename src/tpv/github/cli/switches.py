from tpv.cli import Command, switch, SwitchAttr
from ..github_base import DictConfigParser, config


def make_function(name):
    def f(self, param):
        self.arguments[name] = param
    return f


def make_bool_function(name, default):
    def f(self):
        self.arguments[name] = not default
    return f


def add_argument_switches(parameters):
    def deco(cls):
        arguments = {}

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

            setattr(cls, param["keyname"], f)
            arguments[param["swname"]] = (param["keyname"], f)

        setattr(cls, "__add_argument_switches__", arguments)

        return cls
    return deco


class ConfigSwitchAttr(SwitchAttr):
    def __get__(self, inst, cls):
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
