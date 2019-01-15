#-*- coding: utf-8 -*-
'''
Utilities with Django.
'''
import os
import sys
from django.contrib.auth import get_backends, login


def easy_login(req, user):
    '''
    Login a user without password authentication.
    '''
    backend = get_backends()[0]
    user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
    login(req, user)


def force_logout(session_key, session_model=None):
    '''
    Force logout a session.
    '''
    if not session_model:
        from django.contrib.sessions.models import Session
        session_model = Session
    if session_key:
        sess = session_model.get(session_key=session_key)
        if sess:
            try:
                sess.delete()
            except Exception as e:
                pass


def dj_setting(name=None):
    '''
    Get the setting moudle of django.
    if name is provided, the value of name will be returned,
    else the module itself will be returned.
    '''
    module_name = os.environ.get('DJANGO_SETTINGS_MODULE', '')
    if module_name:
        __import__(module_name)
        module = sys.modules[module_name]
        if name is None:
            return module
        else:
            return getattr(module, name, None)
    else:
        raise Exception("No Django setting module found.")


def get_request_object(user_id=None, session_key=None):
    '''
    Get a request object from user_id or session_key.
    '''
    from django.http import HttpRequest
    from django.contrib.auth import get_user_model
    from importlib import import_module
    user_model = get_user_model()
    session_model = import_module(dj_setting('SESSION_ENGINE')).SessionStore
    req = HttpRequest()
    req.method = 'GET'
    if session_key:
        req.session = session_model(session_key)
        if '_auth_user_id' in req.session:
            req.user = user_model.get(id=req.session['_auth_user_id'])
    elif user_id:
        req.user = user_model.get(id=user_id)
        req.session = session_model()
        easy_login(req, req.user)
    return req


def close_db():
    import django.db
    return django.db.close_old_connections()
