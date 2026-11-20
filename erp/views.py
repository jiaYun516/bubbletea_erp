from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Employee, Ingredient, Order, OrderItem, Payroll, Product, Transaction,
)
from .permissions import ACCT, BOSS, STAFF, role_required
from .services import place_order


# ---------- 行銷：POS 點單 + 熱銷統計 ----------
@login_required
def pos(request):
    products = Product.objects.order_by("id")

    if request.method == "POST":
        items = {}
        for p in products:
            raw = request.POST.get(f"qty_{p.id}", "").strip()
            if raw.isdigit() and int(raw) > 0:
                items[p.id] = int(raw)
        if not items:
            messages.error(request, "請至少選一杯飲品")
        else:
            try:
                order = place_order(request.user, items)
                messages.success(
                    request, f"訂單 #{order.id} 已送出：共 {sum(items.values())} 杯，合計 ${order.total}"
                )
            except ValueError as e:
                messages.error(request, str(e))
        return redirect("pos")

    rank = list(
        OrderItem.objects.values(name=F("product__name"))
        .annotate(cups=Sum("quantity")).order_by("-cups")[:10]
    )
    top = rank[0]["cups"] if rank else 0
    for r in rank:
        r["pct"] = int(r["cups"] * 100 / top)

    return render(request, "erp/pos.html", {
        "products": products,
        "rank": rank,
        "recent": Order.objects.prefetch_related("items__product").order_by("-id")[:5],
        "low_count": Ingredient.objects.filter(stock__lte=F("safety_stock")).count(),
    })


# ---------- 生產製造：庫存 ----------
@role_required(BOSS, STAFF)
def inventory(request):
    ingredients = Ingredient.objects.order_by("id")
    return render(request, "erp/inventory.html", {
        "ingredients": ingredients,
        "low_count": sum(1 for i in ingredients if i.is_low),
    })


@role_required(BOSS)
@require_POST
def restock(request, pk):
    """叫貨：補庫存，同時寫入財會「進貨成本」。"""
    ing = get_object_or_404(Ingredient, pk=pk)
    cost = int(round(ing.reorder_qty * ing.unit_cost))
    with transaction.atomic():
        ing.stock += ing.reorder_qty
        ing.save(update_fields=["stock"])
        Transaction.objects.create(
            kind=Transaction.EXPENSE, category=Transaction.PURCHASE, amount=cost,
            note=f"叫貨 {ing.name} {ing.reorder_qty:.0f}{ing.unit}",
        )
    messages.success(request, f"已叫貨 {ing.name}，進貨成本 ${cost} 已記入財會")
    return redirect("inventory")


# ---------- 財會 ----------
def _sum(qs):
    return qs.aggregate(s=Sum("amount"))["s"] or 0


@role_required(BOSS, ACCT)
def finance(request):
    income = _sum(Transaction.objects.filter(kind=Transaction.INCOME))
    purchase = _sum(Transaction.objects.filter(category=Transaction.PURCHASE))
    salary = _sum(Transaction.objects.filter(category=Transaction.SALARY))
    gross = income - purchase          # 毛利 = 營收 - 進貨成本
    net = gross - salary               # 淨利 = 毛利 - 薪資
    return render(request, "erp/finance.html", {
        "income": income, "purchase": purchase, "salary": salary,
        "gross": gross, "net": net,
        "recent": Transaction.objects.order_by("-id")[:20],
    })


# ---------- 人資 ----------
@role_required(BOSS)
def hr(request):
    month = timezone.localdate().strftime("%Y-%m")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "hours":
            emp = get_object_or_404(Employee, pk=request.POST.get("emp"))
            try:
                hours = Decimal(request.POST.get("hours", "0"))
                if hours < 0:
                    raise InvalidOperation
                emp.hours = hours
                emp.save(update_fields=["hours"])
                messages.success(request, f"已更新 {emp.name} 的本月工時")
            except InvalidOperation:
                messages.error(request, "工時格式不正確")
        elif action == "settle":
            done = set(Payroll.objects.filter(month=month).values_list("employee_id", flat=True))
            count = total = 0
            with transaction.atomic():
                for e in Employee.objects.exclude(id__in=done):
                    amt = e.month_pay()
                    Payroll.objects.create(employee=e, month=month, amount=amt)
                    Transaction.objects.create(
                        kind=Transaction.EXPENSE, category=Transaction.SALARY,
                        amount=amt, note=f"{month} 薪資 {e.name}",
                    )
                    count += 1
                    total += amt
            if count:
                messages.success(request, f"已結算 {count} 位員工，共 ${total}，已記入財會")
            else:
                messages.error(request, f"{month} 薪資已全部結算過")
        return redirect("hr")

    done = set(Payroll.objects.filter(month=month).values_list("employee_id", flat=True))
    rows = [{"e": e, "pay": e.month_pay(), "settled": e.id in done}
            for e in Employee.objects.order_by("id")]
    return render(request, "erp/hr.html", {
        "month": month, "rows": rows,
        "all_settled": all(r["settled"] for r in rows) if rows else True,
        "total": sum(r["pay"] for r in rows),
    })
