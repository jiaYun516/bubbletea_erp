from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

# 角色 = Django 的「群組」，可在 /admin/ 的「群組」「使用者」管理
BOSS = "店長"
STAFF = "店員"
ACCT = "會計"


def has_role(user, *names):
    """超級管理員一律通過；其餘看是否屬於指定群組。"""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name__in=names).exists()


def role_required(*names):
    """限制只有指定角色能進入的頁面；沒權限就導回點單頁。"""
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if has_role(request.user, *names):
                return view(request, *args, **kwargs)
            messages.error(request, "你沒有權限使用此功能")
            return redirect("pos")
        return wrapper
    return decorator
