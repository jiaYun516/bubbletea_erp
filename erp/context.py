from .permissions import ACCT, BOSS, STAFF, has_role


def nav(request):
    """讓所有模板都能知道目前使用者能看哪些選單。"""
    u = request.user
    if not u.is_authenticated:
        return {}
    if u.is_superuser:
        label = "超級管理員"
    else:
        label = "、".join(u.groups.values_list("name", flat=True)) or "未分配角色"
    return {
        "role_label": label,
        "can_inventory": has_role(u, BOSS, STAFF),
        "can_finance": has_role(u, BOSS, ACCT),
        "can_hr": has_role(u, BOSS),
        "is_boss": has_role(u, BOSS),
    }
