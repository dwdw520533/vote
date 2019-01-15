#-*- coding=utf-8 -*-
'''
Provide utility for web applications.
'''
import simplejson as json
import time
import datetime
import functools
import uuid
import types
import logging
import util.status_code as sc
from util.lazy import LazyObject
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import REDIRECT_FIELD_NAME
from collections import OrderedDict
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import sys
PY3 = sys.version_info.major >= 3
if PY3:
    basestring = str
    unicode = str
else:
    basestring = basestring
    unicode = unicode

logger = logging.getLogger(__name__)


def date_time_handler(obj):
    odict = OrderedDict()
    odict[1] = 1
    __dict = {1:1}
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif "{}".format(type(obj)) in ["<class 'odict_values'>", "<class 'dict_values'>"]:
        return list(obj)
    else:
        raise TypeError("%s is not JSON serializable" % obj)


def get_rest_method(req):
    '''
    Get the rest method of request. The function means to get
    the method when browser doesn't support PUT/DELETE http
    methods. So all requests are made by POST/GET, but the
    actual method may be in the _method value from POST query.
    '''
    _m = req.method
    if _m.upper() == 'POST' and '_method' in req.GET:
        _m = req.GET.get('_method').upper()
    return _m


def get_ip(req):
    '''
    Get the real ip address of a request.
    '''
    return req.META.get('HTTP_X_REAL_IP')\
           or req.META.get('HTTP_X_FORWARDED_FOR')\
           or req.META.get('REMOTE_ADDR')


def _protected(req, cache_client=None, threshold=1.0):
    '''
    Protected the address from repeatly access.
    '''
    if not cache_client:
        return
    ip = str(get_ip(req))
    ret = cache_client.incr('protect_%s' % ip, 1)
    if not ret:
        cache_client.set('protect_%s' % ip, 1, 60)
    else:
        if ret > 10000:
            return  HttpResponse(status=403)
        if float(ret) / 60.0 > threshold:
            cache_client.set('protect_%s' % ip, 10001, 3600)
            return  HttpResponse(status=403)


def _ip_allowed(req, ip_allowed_list=None):
    '''
    Protected the address from repeatly access.
    '''
    if ip_allowed_list is None:
        ip_allowed_list = []
    ip = str(get_ip(req))
    if not ip_allowed_list:
        return True
    elif ip in ip_allowed_list:
        return True
    else:
        return False


def _is_mocked(data):
    if hasattr(data, 'get')\
            and data.get('_mock'):
        return True
    else:
        return False


def _get_mock_response(req, data, template, **kw):
    if template is None:
        return HttpResponse(data.get('_mock'), **kw)
    else:
        return render(req, template,
                      context=json.loads(data.get('_mock')))


def _to_response(ret, func, req, template, rest, **kw):
    if not isinstance(ret, HttpResponse):
        if kw.pop('flex', None) and req.META.get('HTTP_REST') == '1':
            template = None
        if template is not None:
            dictionary = {} if ret is None else ret
            template = dictionary.pop('__template')\
                if '__template' in dictionary else template
            return render(req, template,
                          context=dictionary)
        elif isinstance(ret, basestring):
            if 'content_type' not in kw:
                if req.META.get('PATH_INFO', '').endswith('js'):
                    kw['content_type'] = 'application/javascript; charset=utf-8'
                elif req.META.get('PATH_INFO', '').endswith('css'):
                    kw['content_type'] = 'text/css; charset=utf-8'
                else:
                    kw['content_type'] = 'text/plain; charset=utf-8'
        elif isinstance(ret, dict):
            ret = json.dumps(ret, default=date_time_handler)
            if 'content_type' not in kw:
                kw['content_type'] = 'application/json; charset=utf-8'
        elif isinstance(ret, (tuple, list)):
            if rest:
                ret = to_rest_json(ret)
                kw['content_type'] = 'application/json; charset=utf-8'
            else:
                ret = json.dumps(ret, default=date_time_handler)
                if 'content_type' not in kw:
                    kw['content_type'] = 'application/json; charset=utf-8'
        else:
            raise Exception("The return of %s.%s can not be handled"
                            % (getattr(func, '__module__', ''),
                               getattr(func, '__name__', '')))
        ret = HttpResponse(ret, **kw)
    return ret


def _set_redirect(req, rest, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    '''
    used when req is not authenticated but login is required.
    '''
    if not rest:
        path = req.build_absolute_uri()

        resolved_login_url = login_url

        from django.contrib.auth.views import redirect_to_login
        resp = redirect_to_login(
            path, resolved_login_url, redirect_field_name)

        resp.set_cookie(redirect_field_name, path)
        return resp
    else:
        return 1, {}, '未登录'


def _to_log(req, resp, params):
    req_columns = ['REQUEST_METHOD', 'PATH_INFO',
                   'QUERY_STRING', 'HTTP_USER_AGENT', 'HTTP_REFERER']
    ret = ["'%s'" % datetime.datetime.now()]
    ret.append("'%s'" % get_ip(req))
    ret.extend(["'%s'" % req.META.get(col, '') for col in req_columns])
    ret.append("'%s'" % req.COOKIES.get('sessionid', ''))
    if hasattr(req, 'user'):
        ret.append("'%s'" % getattr(req.user, 'id', ''))
    ret.append("'%s'" % len(resp.content))
    ret.append("'%s'" % resp.status_code)
    for param in params:
        ret.append("'%s'" % param)
    #return ' '.join([i.encode('utf-8', 'ignore') if isinstance(i, bytes) else i for i in ret])
    return ' '.join(ret)


def get_site_referrer(req):
    ref = req.META.get('HTTP_REFERER', '')
    if ref:
        parsed_ref = urlparse(ref)
        http_host = req.META.get('HTTP_HOST', '')
        if parsed_ref.netloc == http_host:
            return ref
    return None


def redirect_all(to, req=None):
    to_url = to
    if req:
        #if req.META.get('PATH_INFO'):
        #    to_url += req.META.get('PATH_INFO')
        if req.META.get('QUERY_STRING'):
            to_url = '%s?%s' % (to_url,
                                req.META.get('QUERY_STRING'))
    return redirect(to_url)


def expose(**kw):
    '''
    A decorator for simplifying web controllers, make sure the
    return value from web controllers to be a HttpResponse object.

    Mock suport
    -----------
    If a '_mock' parameter is in the request, the decorator
    will directly return the content of '_mock', or use the
    content as the dictionary of render_to_response when a
    template is specfied. The wrapped function will not be
    executed.

    Parameters
    ----------
    rest: boolean, default False
        Constuct {'status': status_code, ...} like json response.
    template: string, default None
        The template path.
    login_required: boolean, default False
        The view need logined to be accessed. When enabled, if the user
        is not authenticated, and rest is not True, the response will be
        a redirect to the login_url.
    login_url: string, optional
        The login address url, or will use LOGIN_URL if None.
    protected: object, optional
        The provide an cache object to keep the counter of access times.
    other parameters in kw:
        The parameters passed to generated HttpResponse object.

    Example
    -------
    @utility.expose(template='xxx/yyy.html')
    def test(req):
        return dict(name='Zhang San')

    @utility.expose(rest=True)
    def resttest(req):
        return 200, dict(content='Nothing')
    Above function will result a json formatted the resposne
    like {"status": 200, "content": "Nothing"}.
    '''
    rest = kw.pop('rest', False)
    template = kw.pop('template', None)
    login_required = kw.pop('login_required', False)
    login_url = kw.pop('login_url', None)
    protected = kw.pop('protected', None)
    ip_allowed = kw.pop('ip_allowed', None)

    def entangle(func):
        def wrapper(*sub, **kwargs):
            # Get self and req
            if isinstance(sub[0], HttpRequest):
                self, req = None, sub[0]
            elif len(sub) > 1 and isinstance(sub[1], HttpRequest):
                self, req = sub[0], sub[1]
            else:
                raise Exception("Incorrect calling of gsweb.expose, no request object.")

            # Setup transcation id
            req._trans_id = str(uuid.uuid1())

            # Handling request
            data = getattr(req, req.method, {})

            # Handling _mock data
            if _is_mocked(data):
                return _get_mock_response(req, data, template, **kw)
            use_time = time.time()

            # ip check
            if ip_allowed and not _ip_allowed(req, ip_allowed):
                return HttpResponse(status=403)

            # Handling hijacking protection
            forbidden = _protected(req, protected)
            if forbidden:
                return forbidden

            req._resp = LazyObject()
            if login_required and hasattr(req, 'user') and \
                    not (req.user.is_authenticated() if isinstance(req.user.is_authenticated, types.MethodType) else req.user.is_authenticated):
                ret = _set_redirect(req, rest, login_url=login_url,
                                    redirect_field_name=REDIRECT_FIELD_NAME)
            else:
                ret = func(*sub, **kwargs)

            # Handling response
            ret = _to_response(ret, func, req, template, rest, **kw)
            req._resp._set_obj(ret)
            req._resp._flush()

            # Make sure the ret is rendered
            if hasattr(ret, 'is_rendered') and not ret.is_rendered:
                ret.render()

            use_time = '%4.3f' % (time.time() - use_time)

            return ret
        if type(func) == types.FunctionType:
            wrapper = functools.wraps(func)(wrapper)
        wrapper._exposed = True
        wrapper._original = func
        return wrapper
    return entangle


def to_jsonp(callback, data):
    '''
    Convert to jsonp formatted string.
    '''
    return "%s(%s);" % (callback, json.dumps(data, default=date_time_handler))


def to_rest_json(data):
    code = data[0]
    msg = str(data[2]) if len(data) == 3 else ''
    result = data[1] if len(data) > 1 else {}
    ret = {'code': code,
           'msg': msg,
           'result': result}
    #return json.dumps(ret)
    return json.dumps(ret, default=date_time_handler)


@expose()
def dummy_web(req, **kw):
    split = "=" * 10
    print("URL\n%s\n    %s\n" % (split, req.build_absolute_uri()))
    print("PARAMS\n%s" % split)
    for k, v in kw.items():
        print("    ", k, v)
    print("QUERIES\n%s" % split)
    for k, v in req.REQUEST.items():
        print("    ", k, v)
    print("HEADERS\n%s" % split)
    for k, v in req.META.items():
        if k.startswith("HTTP"):
            print("    ", k, v)
    print("FILES\n%s" % split)
    if req.FILES:
        for filename in req.FILES:
            print("    ", filename, len(req.FILES.get(filename).read()))
    return ''


def get_next_url(req, redirect_field_name=REDIRECT_FIELD_NAME):
    '''
    Get the next url from the web request.
    '''
    next_url = getattr(req, req.method).get(REDIRECT_FIELD_NAME, None)\
        or req.COOKIES.get(REDIRECT_FIELD_NAME, None)
    return next_url


def redirect_to_next_url(req, redirect_field_name=REDIRECT_FIELD_NAME,
                         default_url=None):
    '''
    Generate a HttpResponse object redirecting to the next url, and clear
    the related cookies.
    '''
    if default_url is None:
        default_url = '/'
    next_url = get_next_url(req, redirect_field_name=REDIRECT_FIELD_NAME)\
        or default_url
    resp = redirect(next_url)
    resp.delete_cookie(redirect_field_name)
    return resp


def authed(login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    '''
    A decorator to replace django default login_required decorator.
    '''
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            authenticated = request.user.is_authenticated
            login = authenticated() if callable(authenticated) else authenticated
            if login:
                return view_func(request, *args, **kwargs)

            path = request.build_absolute_uri()

            resolved_login_url = login_url

            from django.contrib.auth.views import redirect_to_login
            resp = redirect_to_login(
                path, resolved_login_url, redirect_field_name)

            # Set next url to cookie
            resp.set_cookie(redirect_field_name, path, max_age=7200)
            return resp
        return _wrapped_view
    return decorator


def get_protocol_and_host(req):
    '''
    根据req生成http(s)://www.tifen.cn/
    主要是为了满足域名变更的需求
    '''
    protocol = 'https://' if req.is_secure() else 'http://'
    return '%s%s' % (protocol, req.META['HTTP_HOST'])


def from_current_host(req, allow_empty_referer=False):
    '''
    from_current_host(req, allow_empty_referer=False)
    Check if a Django Request Object is issued from the
    same host via http referer check.
    '''
    referer = req.META.get('HTTP_REFERER') or ''
    protocol = 'https://' if req.is_secure() else 'http://'
    host_prefix = "%s%s" % (protocol, req.get_host())
    if allow_empty_referer and not referer:
        return True
    return referer.startswith(host_prefix)


def is_mobile(req):
    '''
    Determine whether the req is issued by a mobile browser.
    '''
    TABLET_AGENTS = ('tablet', 'ipad', 'xoom', 'playbook', 'kindle')
    user_agent = req.META.get('HTTP_USER_AGENT', '').lower()
    for tab in TABLET_AGENTS:
        if tab in user_agent:
            return False
    if 'mobile' in user_agent:
        return True
    if 'android' in user_agent:
        # Android with Chrome(if not with mobile) are not mobile browser.
        if 'chrome' in user_agent:
            return False
        return True
    return False


def agent_contain(req, condition=None):
    user_agent = req.META.get('HTTP_USER_AGENT', '').lower()
    if isinstance(condition, basestring):
        return condition in user_agent
    elif callable(condition):
        return condition(user_agent)
    else:
        return False


def is_weixin(req):
    '''
    Determine whether the req is issued inside weixin.
    '''
    return agent_contain(req, 'micromessenger')


def is_qq(req):
    '''
    Determine whether the req is issued inside QQ.
    '''
    return agent_contain(req, lambda s: 'qq' in s and not 'qqbrowser' in s)


def is_android(req):
    '''
    Determine whether the req is issued inside QQ.
    '''
    return agent_contain(req, 'android')


def is_ios(req):
    '''
    Determine whether the req is issued inside QQ.
    '''
    return agent_contain(req, lambda s: 'iphone' in s or 'ipad' in s\
                                         or 'ipod' in s)


def get_json_argument(req, key, default=None):
    try:
        json_body = getattr(req, '__json_body', None)
        if json_body is None:
            json_body = json.loads(req.body.decode('utf-8')) if req.body else {}
            json_body = json_body if isinstance(json_body, dict) else {"body": json_body}
            req.__json_body = json_body
        return json_body.get(key, default)
    except json.JSONDecodeError as ex:
        logger.info("#deserialize request body JSONDecodeError error: %s", req.body)
        raise ex


def json_default(obj):
    '''实现json包对datetime的处理
    '''
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.strftime('%Y-%m-%d %H:%M:%S')


def ApiResult(code, result=None, msg=None):
    """
    return rest result format
    """
    if isinstance(code, dict) and "code" in code:
        return code["code"], code["result"], code["msg"]
    logging.info("======>code: %s", code)
    logging.debug("======>result: %s", json.dumps(result, default=json_default))
    logging.info("======>msg: %s", msg or sc.get_error_msg(code))
    return code, {} if result is None else result, msg or sc.get_error_msg(code)
