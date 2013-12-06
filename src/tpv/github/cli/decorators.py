import tpv.cli

def make_function(name):
    return lambda self, param: self.arguments.__setitem__(name, param)

def make_bool_function(name, default):
    return lambda self: self.arguments.__setitem__(name, not default)

def add_argument_switches(parameters):
    def deco(cls):
        for param in parameters:
            if "flagname" not in param:
                param["flagname"]  = "--" + param["name"].replace("_", "-")

            if param.get("type", str) == bool:
                f = tpv.cli.switch(param["flagname"],
                                   help=param.get("help"))(make_bool_function(param["name"], param["default"]))
            else:
                f = tpv.cli.switch(param["flagname"],
                                   argtype=param.get("type", str),
                                   help=param.get("help"),
                                   list=param.get("list", False),
                                   completion=param.get("completion", None),
                                   mandatory=param.get("mandatory", False)
                                   )(make_function(param["name"]))

            setattr(cls, param["name"], f)
        return cls
    return deco
