# -*- coding=utf-8 -*-
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


def get_user_by_id(user_id):
    try:
        return User.objects.get(id=user_id)
    except:
        return None


def get_user(username):
    try:
        return User.objects.get(username=username)
    except:
        return None


def update_user(user, **user_data):
    """
    Update a user's account.
    """
    user = user if hasattr(user, "id") else get_user_by_id(user)
    for key, value in user_data.items():
        setattr(user, key, value)
    user.save()
    return user


def get_or_create_user(username, password):
    """
    Create a new user.
    Parameters
    ----------
    username: string,
        The username of the user, not optional.
    password: string, optional
        The password of the user, if None, means unusable password.
    req: HttpRequest object, optional,
        The HttpRequest object, if sent from a view.
    """
    user = get_user(username=username)
    if not user:
        user = User.objects.create_user(username=username)
        if password:
            user.set_password(password)

        user.save()
        return True, user
    else:
        return False, user


def verify_password(username, password):
    user = authenticate(username=username, password=password)
    return user
