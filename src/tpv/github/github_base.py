from requests import request
import json
import os
import sys
from ConfigParser import ConfigParser
import re
from itertools import chain

from metachao import aspect
from tpv.ordereddict import OrderedDict

URL_BASE = 'https://api.github.com'


# Read in some authentication data from ~/.ghconfig.
# It should contain a section like
#
#   [github]
#   user=<username>
#   token=<personal access token>
#
# where the personal access token can be generated with "Create new
# token" on https://github.com/settings/applications.


class RelativeDictionaryAccess(aspect.Aspect):
    @aspect.plumb
    def __getitem__(_next, self, key):
        try:
            for k in key.split("."):
                cur = _next(k)
                _next = cur.__getitem__
        except AttributeError:
            pass

        return cur

    @aspect.plumb
    def __contains__(_next, self, key):
        if "." not in key:
            return _next(key)

        nodes = key.split(".")
        curr = self
        try:
            for k in nodes[:-1]:
                curr = self[k]
        except KeyError:
            return False

        return nodes[-1] in curr


class DictConfigParser(object):
    def __init__(self, basename):
        def get_files(basename):
            home = os.path.expanduser("~")
            path = os.getcwd()

            while path and path != home:
                yield os.path.join(path, basename)
                path = path[:path.rfind(os.path.sep)]

            yield os.path.join(home, basename)

        def parse_config(f):
            config = ConfigParser()
            config.read(f)
            return RelativeDictionaryAccess(
                OrderedDict((section,
                             dict((option, value)
                                  for option, value in config.items(section)))
                            for section in config.sections())
            )

        self.config_dict = OrderedDict((f, parse_config(f))
                                       for f in get_files(basename))

    def by_files(self):
        return self.config_dict

    def __getitem__(self, key):
        for config in self.config_dict.itervalues():
            if key in config:
                return config[key]
        raise KeyError(key)

    def __contains__(self, key):
        for config in self.config_dict.itervalues():
            if key in config:
                return True
        return False

    def _flat_dict(self):
        return RelativeDictionaryAccess(OrderedDict(
            chain.from_iterable(
                x.iteritems()
                for x in reversed(self.config_dict.values())
            )))

    def __iter__(self):
        return iter(self._flat_dict())

    iterkeys = __iter__

    def itervalues(self):
        return self._flat_dict().itervalues()

    def iteritems(self):
        return self._flat_dict().iteritems()

    def keys(self):
        return list(self)

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

config = DictConfigParser(".ghconfig")


def authenticated_user():
    return config["github.user"]


def extract_repo_from_issue_url(url, issueno):
    m = re.match(URL_BASE + "/repos/(.+)/(.+)/issues/{}"
                 .format(issueno), url)
    return (m.group(1), m.group(2))


def merge_dicts(*dicts):
    return dict(chain(*(d.iteritems() for d in dicts)))


def set_on_new_dict(basedict, key, value):
    ret = basedict.copy()
    ret[key] = value
    return ret


def github_request(method, urlpath, data=None, params=None):
    """Request `urlpath` from github using authentication from config

    Arguments:
    - `method`: one of "HEAD", "GET", "POST", "PATCH", "DELETE"
    - `urlpath`: the path part of the request url, i.e. /users/coroa
    """
    req = request(method, URL_BASE + urlpath,
                  auth=(config["github.user"],
                        config["github.token"]),
                  data=None
                  if data is None
                  else json.dumps(data),
                  params=params)

    if "github.debug" in config and int(config["github.debug"]) >= 2:
        sys.stderr.write(('''
>>> Request
{method} {url}
{reqbody}
>>> Response
{status}
{respbody}
        '''.strip()+"\n").format(
            method=req.request.method,
            url=req.request.url,
            reqbody=req.request.body,
            status=req.headers["status"],
            respbody=json.dumps(req.json(),
                                indent=2,
                                separators=(',', ': '))
        ))

    return req


def github_request_paginated(method, urlpath, params=None):
    while urlpath:
        req = github_request(method, urlpath, params=params)
        if '200 OK' not in req.headers['status']:
            raise RuntimeError(req.json()['message'])

        for elem in req.json():
            yield elem

        urlpath = None
        if "Link" in req.headers:
            m = re.search('<(https[^>]*)>; rel="next"', req.headers["Link"])
            if m:
                urlpath = m.group(1)[len(URL_BASE):]


def github_request_length(urlpath):
    req = github_request("GET", urlpath + "?per_page=1")
    m = re.search('<https[^>]*[?&]page=(\d+)[^>]*>; rel="last"',
                  req.headers["Link"])
    if m:
        return int(m.group(1))
    else:
        return 0


class GhBase(dict):
    def __init__(self, parent, data=None, **kwargs):
        self._parent = parent
        self._parameters = kwargs

        if not self._parameters and self._parent:
            self._parameters = self._parent._parameters

        for k, v in self._parameters.iteritems():
            setattr(self, "_" + k, v)

    def __repr__(self):
        return "<{} [{}]>".format(
            self.__class__.__name__,
            " ".join("{}={}".format(k, v)
                     for k, v in self._parameters.iteritems())
        )

    def _debug(self, func, *args):
        if "github.debug" in config and int(config["github.debug"]) >= 1:
            sys.stderr.write("{}.{}({})\n".format(self, func, ", ".join(args)))


class GhResource(GhBase):
    @property
    def url_template(self):
        raise NotImplementedError()

    def __init__(self, parent, data=None, **kwargs):
        super(GhResource, self).__init__(parent, data, **kwargs)

        if data is None:
            url = self.url_template.format(**self._parameters)
            data = github_request("GET", url).json()
        super(GhResource, self).update(data)

    def __getitem__(self, key):
        self._debug("__getitem__", key)
        return super(GhResource, self).__getitem__(key)

    def __setitem__(self, key, value):
        self._debug("__setitem__", key, value)
        self.update({key: value})

    def update(self, data):
        try:
            if self._parent.list_key not in data:
                data = set_on_new_dict(data,
                                       self._parent.list_key,
                                       self._parameters[self._parent.child_parameter])
        except NotImplementedError:
            # the parent is not iterable, the caller of update has to
            # supply all mandatory arguments in data
            pass

        url = self.url_template.format(**self._parameters)
        req = github_request("PATCH", url, data=data)
        if '200 OK' not in req.headers["status"]:
            raise ValueError("Couldn't update {} object: {}"
                             .format(self.__class__.__name__,
                                     req.json()["message"]))

        # update the cached data with the live data from
        # github. a detailed representation.
        super(GhResource, self).update(req.json())


class GhCollection(GhBase):

    @property
    def list_url_template(self):
        raise NotImplementedError("Collection is not iterable.")

    @property
    def list_key(self):
        raise NotImplementedError("Collection is not iterable.")

    @property
    def get_url_template(self):
        raise NotImplementedError()

    @property
    def child_class(self):
        raise NotImplementedError()

    @property
    def child_parameter(self):
        raise NotImplementedError()

    @property
    def add_url_template(self):
        raise NotImplementedError("Can't add to collection.")

    add_method = "POST"
    # add_required_arguments = [ "name", "..." ... ]

    def search(self, **arguments):
        return ((x[self.list_key],
                 self.child_class(self,
                                  data=x,
                                  **set_on_new_dict(self._parameters,
                                                    self.child_parameter,
                                                    x[self.list_key])))
                for x in self._get_resources(**arguments))

    def _get_resources(self, **arguments):
        url = self.list_url_template.format(**self._parameters)
        return github_request_paginated("GET", url, params=arguments)

    def iterkeys(self):
        return (x[self.list_key] for x in self._get_resources())

    __iter__ = iterkeys

    def keys(self):
        return list(self.iterkeys())

    def itervalues(self):
        return (x[1] for x in self.iteritems())

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        return self.search()

    def items(self):
        return list(self.iteritems())

    def __len__(self):
        return len(self.keys())

    def __getitem__(self, key):
        """Return the GhResource object for `key` """
        self._debug("__getitem__", key)

        parameters = set_on_new_dict(self._parameters,
                                     self.child_parameter,
                                     key)

        url = self.get_url_template.format(**parameters)
        req = github_request("GET", url)
        if "200" not in req.headers["status"]:
            raise KeyError("Resource {} does not exist.".format(key))

        return self.child_class(self, data=req.json(), **parameters)

    def add(self, **arguments):
        self._debug("add", *("{}={}".format(k, v)
                             for k, v in arguments.iteritems()))

        # check if all required arguments are provided
        for required_arg in getattr(self, 'add_required_arguments', []):
            if required_arg not in arguments:
                raise ValueError("Not all required arguments {} provided"
                                 .format(", ".join(self.add_required_arguments)))

        if self.add_method == "POST":
            url = self.add_url_template.format(**self._parameters)
            req = github_request("POST", url,
                                 data=arguments)
            if "201 Created" not in req.headers["status"]:
                raise ValueError("Couldn't create {} object: {}"
                                 .format(self.child_class.__name__,
                                         req.json()["message"]))
            else:
                data = req.json()
                parameters = set_on_new_dict(self._parameters,
                                             self.child_parameter,
                                             data[self.list_key])
                return self.child_class(parent=self, data=data, **parameters)

        elif self.add_method == "PUT":
            if self.list_key not in arguments:
                raise ValueError("The required argument {} was not provided"
                                 .format(self.list_key))
            tmpl_vars = set_on_new_dict(self._parameters,
                                        self.child_parameter,
                                        arguments[self.list_key])
            url = self.add_url_template.format(**tmpl_vars)

            req = github_request("PUT", url,
                                 data=arguments)
            if "204 No Content" not in req.headers["status"]:
                raise ValueError("Couldn't create {} object: {}"
                                 .format(self.child_class.__name__,
                                         req.json()["message"]))
            # else:
            #     return self.child_class(parent=self, **tmpl_vars)

    def __delitem__(self, key):
        self._debug("__delitem__", key)

        tmpl_vars = set_on_new_dict(self._parameters,
                                    self.child_parameter, key)
        url = self.delete_url_template.format(**tmpl_vars)
        req = github_request("DELETE", url)
        if "204 No Content" not in req.headers["status"]:
            raise ValueError("Couldn't delete {} object: {}"
                             .format(self.child_class.__name__,
                                     req.json()["message"]))
