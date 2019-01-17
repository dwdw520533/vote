# -*- coding=utf-8 -*-
"""
用户登录相关API
"""
import util.status_code as sc
from django.contrib.auth import logout
import user as user_ops
import vt as vote_ops
from util.dj import easy_login
from util.web import ApiResult, expose


@expose(rest=True)
def user_register(req):
    user_name = req.GET.get("user_name")
    password = req.GET.get("password")
    if not (user_name and password):
        return ApiResult(sc.E_PARAM)
    user = user_ops.get_user(user_name)
    if user:
        return ApiResult(sc.E_PARAM, msg="用户名已注册")
    # 创建用户
    user_ops.get_or_create_user(user_name, password)
    return ApiResult(sc.E_SUCC)


@expose(rest=True)
def user_login(req):
    user_name = req.GET.get("user_name")
    password = req.GET.get("password")
    if not (user_name and password):
        return ApiResult(sc.E_PARAM)
    # 创建用户
    user = user_ops.get_user(user_name)
    if not user:
        return ApiResult(sc.E_PARAM, msg='用户不存在')
    if not user_ops.verify_password(user_name, password):
        return ApiResult(sc.E_PARAM, msg='密码有误')
    # 登陆
    if not req.user.is_authenticated:
        easy_login(req, user)
    req.session.set_expiry(7257600)
    return ApiResult(sc.E_SUCC)


@expose(rest=True)
def user_logout(req):
    if req.user.is_authenticated:
        logout(req)
    return ApiResult(sc.E_SUCC)


@expose(rest=True)
def vote_list(req):
    return ApiResult(sc.E_SUCC, vote_ops.query_vote_themes())


@expose(rest=True, login_required=True)
def user_vote(req):
    code = req.GET.get("code")
    if not code:
        return ApiResult(sc.E_PARAM)
    code, res = vote_ops.user_vote(req.user.id, str(code))
    return ApiResult(code, msg=res)
