'''
Decorator for structuring the code for REST api.
'''
import sys
import functools
from util.web import get_rest_method

ALLOWED_ATTRS = ['path', 'host', 'method']


def functor(*sub, **kwargs):
    """
    A simple wrapper make a class become a functor,
    the class need a __call__ function. The (*sub,
    **kwargs) will be passed for the __init__ function,
    and the name of class will be the name of function
    object.

    Example
    -------
    @functor(*sub, **kwargs)
    class functor_name(object):
        def __init__(self, *sub, **kwargs):
            ...
        def __call__(self):
            ...

    Then you may use functor_name() as a function.

    """

    def wrapper(cls):
        module = sys.modules[cls.__module__]
        obj = cls(*sub, **kwargs)
        setattr(module, cls.__name__, obj)
        return obj

    return wrapper


def _get_request_attr(req, attr_name):
    '''
    Safely get the attr from request object.
    '''
    if not attr_name in ALLOWED_ATTRS:
        return None
    if attr_name == 'method':
        return get_rest_method(req)
    else:
        return getattr(req, attr_name, None)


def _parse_rule_list(rule):
    rule_list = []
    for k, v in rule.items():
        if '__' in k:
            (key, op) = k.split('__', 1)
            rule_list.append((key, op, v))
        else:
            rule_list.append((k, '==', v))
    return rule_list


def _match_rule(req, rule_list):
    for (k, op, v) in rule_list:
        attr = _get_request_attr(req, k)
        if attr is None:
            break
        elif op == '==':
            if attr != v:
                break
        else:
            if not hasattr(attr, op):
                break
            else:
                if not getattr(attr, op)(v):
                    break
    else:
        return True
    return False


def rest_class(cls):
    '''
    Decorator for a rest like view class.

    Usage
    -----
    @rest_class
    class RestView(object):
        @route(path__startswith='/user/profile', method='GET')
        def user_profile_get_view(self, req):
            ...
        @route(path__startswith='/user/profile', method='POST')
        def user_profile_update_view(self, req):
            ...
    '''
    cls._route_rules = []
    for name in dir(cls):
        item = getattr(cls, name)
        if hasattr(item, '_route_rule'):
            if item._route_rule.get('default'):
                cls._default_item = item
            else:
                rule_list = _parse_rule_list(item._route_rule)
                if rule_list:
                    cls._route_rules.append((item, rule_list))

    def router_func(self, req, *sub, **kw):
        for (item, rule_list) in cls._route_rules:
            if _match_rule(req, rule_list):
                return item(self, req, *sub, **kw)
        else:
            if hasattr(cls, '_default_item'):
                return cls._default_item(self, req, *sub, **kw)
        raise Exception("No fules matched for request.")
    cls.__call__ = router_func
    return functor()(cls)


def route(**rule):
    '''
    Decorator indicating the routes for current view.
    '''
    def entangle(func):
        @functools.wraps(func)
        def wrapper(self, req, *sub, **kw):
            ret = func(self, req, *sub, **kw)
            return ret
        wrapper._route_rule = rule
        return wrapper
    return entangle
