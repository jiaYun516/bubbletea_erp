import random

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from erp.models import Employee, Ingredient, Order, Product, Recipe
from erp.permissions import ACCT, BOSS, STAFF
from erp.services import place_order

# 名稱: (單位, 初始庫存, 安全庫存, 每次叫貨量, 進貨單價)
INGREDIENTS = {
    "紅茶基底": ("ml", 10000, 2000, 10000, 0.05),
    "綠茶基底": ("ml", 10000, 2000, 10000, 0.05),
    "青茶基底": ("ml", 10000, 2000, 10000, 0.06),
    "鮮奶":     ("ml", 8000, 1500, 8000, 0.08),
    "珍珠":     ("g", 3000, 500, 3000, 0.10),
    "椰果":     ("g", 600, 500, 3000, 0.10),   # 故意設低，方便示範紅燈叫貨
    "果糖":     ("ml", 5000, 1000, 5000, 0.06),
    "紙杯":     ("個", 500, 100, 500, 1.50),
}

# 飲品: (售價, {原物料: 每杯用量})
PRODUCTS = {
    "熟成紅茶":     (30, {"紅茶基底": 300, "果糖": 15, "紙杯": 1}),
    "茉莉綠茶":     (30, {"綠茶基底": 300, "果糖": 15, "紙杯": 1}),
    "四季春青茶":   (35, {"青茶基底": 300, "果糖": 15, "紙杯": 1}),
    "紅茶拿鐵":     (55, {"紅茶基底": 200, "鮮奶": 150, "果糖": 15, "紙杯": 1}),
    "茉綠拿鐵":     (55, {"綠茶基底": 200, "鮮奶": 150, "果糖": 15, "紙杯": 1}),
    "鐵觀音拿鐵":   (60, {"青茶基底": 200, "鮮奶": 150, "果糖": 15, "紙杯": 1}),
    "珍珠紅茶拿鐵": (65, {"紅茶基底": 150, "鮮奶": 150, "珍珠": 60, "果糖": 15, "紙杯": 1}),
    "波霸紅茶":     (40, {"紅茶基底": 300, "珍珠": 60, "果糖": 15, "紙杯": 1}),
    "椰果綠茶":     (45, {"綠茶基底": 300, "椰果": 50, "果糖": 15, "紙杯": 1}),
    "雙Q青茶":      (50, {"青茶基底": 300, "珍珠": 40, "椰果": 40, "果糖": 15, "紙杯": 1}),
}

# 姓名, 職稱, 薪資類型, 月薪, 時薪, 本月工時
EMPLOYEES = [
    ("王店長", "店長", Employee.MONTHLY, 38000, 0, 0),
    ("阿明", "工讀生", Employee.HOURLY, 0, 190, 60),
    ("小美", "工讀生", Employee.HOURLY, 0, 190, 45),
    ("小華", "工讀生", Employee.HOURLY, 0, 190, 52),
]

# 帳號, 密碼, 群組(角色), 是否超級管理員
USERS = [
    ("admin", "admin123", None, True),
    ("boss", "boss123", BOSS, False),
    ("staff", "staff123", STAFF, False),
    ("acct", "acct123", ACCT, False),
]


class Command(BaseCommand):
    help = "建立示範資料：角色/帳號、原物料、10 種飲品與配方、員工、範例訂單"

    def handle(self, *args, **options):
        # 角色與帳號
        for g in (BOSS, STAFF, ACCT):
            Group.objects.get_or_create(name=g)
        for username, pwd, group, is_super in USERS:
            u, _ = User.objects.get_or_create(username=username)
            u.set_password(pwd)
            u.is_superuser = is_super
            u.is_staff = is_super
            u.save()
            if group:
                u.groups.set([Group.objects.get(name=group)])

        # 原物料
        ing = {}
        for name, (unit, stock, safety, reorder, cost) in INGREDIENTS.items():
            ing[name], _ = Ingredient.objects.update_or_create(
                name=name,
                defaults=dict(unit=unit, stock=stock, safety_stock=safety,
                              reorder_qty=reorder, unit_cost=cost),
            )

        # 飲品與配方
        for name, (price, recipe) in PRODUCTS.items():
            p, _ = Product.objects.update_or_create(name=name, defaults={"price": price})
            for iname, qty in recipe.items():
                Recipe.objects.update_or_create(
                    product=p, ingredient=ing[iname], defaults={"quantity": qty}
                )

        # 員工
        for name, title, pay_type, monthly, hourly, hours in EMPLOYEES:
            Employee.objects.update_or_create(
                name=name,
                defaults=dict(title=title, pay_type=pay_type, monthly_salary=monthly,
                              hourly_wage=hourly, hours=hours),
            )

        # 範例訂單（只在還沒有訂單時建立，會真的扣庫存、寫入財會）
        if not Order.objects.exists():
            random.seed(7)
            staff = User.objects.get(username="staff")
            products = list(Product.objects.all())
            weights = [5, 3, 2, 4, 3, 2, 6, 5, 2, 3]  # 讓排行榜有高低差
            for _ in range(12):
                picked = random.choices(products, weights=weights, k=random.randint(1, 3))
                items = {}
                for p in picked:
                    items[p.id] = items.get(p.id, 0) + random.randint(1, 3)
                try:
                    place_order(staff, items)
                except ValueError:
                    pass  # 庫存不足的單直接略過

        self.stdout.write(self.style.SUCCESS("示範資料建立完成"))
        self.stdout.write("登入帳號：admin/admin123（超管）、boss/boss123（店長）、"
                          "staff/staff123（店員）、acct/acct123（會計）")
