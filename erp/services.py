from collections import defaultdict
from decimal import Decimal

from django.db import transaction

from .models import Ingredient, Order, OrderItem, Product, Recipe, Transaction


@transaction.atomic
def place_order(user, items):
    """
    送出訂單。items = {product_id: 杯數}
    一次完成：建立訂單 → 依配方扣原物料庫存 → 寫入財會「銷售收入」。
    庫存不足會丟 ValueError，整筆不成立。
    """
    products = {p.id: p for p in Product.objects.filter(id__in=items.keys())}

    # 1. 算出這張單總共需要多少原物料
    need = defaultdict(Decimal)
    for r in Recipe.objects.filter(product_id__in=items.keys()):
        need[r.ingredient_id] += r.quantity * items[r.product_id]

    # 2. 檢查庫存
    ingredients = {i.id: i for i in Ingredient.objects.filter(id__in=need.keys())}
    short = [ingredients[i].name for i, n in need.items() if ingredients[i].stock < n]
    if short:
        raise ValueError("庫存不足，無法出單：" + "、".join(short))

    # 3. 建立訂單與明細
    order = Order.objects.create(created_by=user)
    total = 0
    for pid, qty in items.items():
        p = products[pid]
        OrderItem.objects.create(order=order, product=p, quantity=qty, unit_price=p.price)
        total += p.price * qty
    order.total = total
    order.save(update_fields=["total"])

    # 4. 扣庫存
    for iid, n in need.items():
        ing = ingredients[iid]
        ing.stock -= n
        ing.save(update_fields=["stock"])

    # 5. 財會：銷售收入
    Transaction.objects.create(
        kind=Transaction.INCOME, category=Transaction.SALES,
        amount=total, note=f"訂單 #{order.id}",
    )
    return order
