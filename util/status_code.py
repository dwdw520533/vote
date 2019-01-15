# coding:utf-8
import json
import types

'''
status code dict的定义：
    key为数字的错误代码，
    value为一个二元组，(<错误代码名称>, <默认错误信息>)
'''
DEFAULT_DICT = {
    0: ('E_SUCC', '成功'),
    1: ('E_PARAM', '参数错误'),
    2: ('E_INTER', '程序内部错误'),
    3: ('E_EXTERNAL', '外部接口错误'),
    4: ('E_TIMEOUT', '第三方接口超时'),
    5: ('E_RESRC', '接口不存在'),
    6: ('E_AUTH', '鉴权失败'),
    7: ('E_FORBIDDEN', '访问被禁止'),
    8: ('E_RESOURCE_NOT_FIND', '资源不存在或已删除'),

    # 用户模块
    1000: ('E_USER_LOCKED', '用户被锁定'),
    1001: ('E_USER_EXIST', '该手机号已被注册'),
    1002: ('E_USER_NOT_EXIST', '用户不存在, 请检查手机号码是否正确，或者前往注册'),
    1003: ('E_USER_LOGIN', '用户已登录'),
    1004: ('E_USER_NOT_LOGIN', '用户未登录'),
    1005: ('E_USER_NAME_OR_PWD_ERROR', '手机号码与密码不匹配'),
}


class StatusCodeStore(object):
    '''
    Store of status codes.
    '''
    DEFAULT_STORE = None

    def __init__(self, codes=None):
        self.codes = codes if type(codes) is dict else {}
        self.refresh()

    def refresh(self):
        self.reverse = {}
        set_into_modules(self.reverse, from_store=self)

    def get_error_msg(self, code):
        '''
        获取error_msg
        '''
        if isinstance(code, str) and code.isdigit():
            code = int(code)
        __, msg = self.codes.get(code, (None, None))
        return msg or '未知错误'

    def __getattr__(self, name):
        code = self.reverse[name]
        return code

    def send_json_result(self, code, result=None, msg=None):
        if isinstance(code, dict) and "code" in code:
            return json.dumps(code)
        return json.dumps({'code': code,
                           'result': {} if result is None else result,
                           'msg': msg or self.get_error_msg(code)})


def replace(status_codes_dict, target_store=None):
    '''
    Replace the content of store, use global store
    if store is None.
    '''
    target_store = StatusCodeStore.DEFAULT_STORE\
                   if target_store is None else target_store
    target_store.codes = status_codes_dict
    target_store.refresh()


def update(status_codes_dict, target_store=None):
    target_store = StatusCodeStore.DEFAULT_STORE\
                   if target_store is None else target_store
    target_store.codes.update(status_codes_dict)
    target_store.refresh()


def update_from_json(json_file, target_store=None):
    json_list = json.load(open(json_file))
    status_codes_dict = {code: (name, msg) for (code, name, msg) in json_list}
    return update(status_codes_dict, target_store=target_store)


def set_into_modules(target, from_store=None):
    from_store = StatusCodeStore.DEFAULT_STORE\
                 if from_store is None else from_store
    if isinstance(target, dict):
        target_dict = target
    elif isinstance(target, types.ModuleType):
        target_dict = target.__dict__
    for (code, (name, msg)) in from_store.codes.items():
        target_dict[name] = code


def get_error_msg(code, from_store=None):
    '''
    获取error_msg
    '''
    from_store = StatusCodeStore.DEFAULT_STORE\
                 if from_store is None else from_store
    return from_store.get_error_msg(code)


'''
全局的status code存储, 建议在同一个project直接使用这个store
'''
store = StatusCodeStore.DEFAULT_STORE = StatusCodeStore(DEFAULT_DICT)
set_into_modules(globals())
