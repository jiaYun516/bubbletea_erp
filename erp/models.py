from django.conf import settings
from django.db import models
from django.utils import timezone


# ============ 生產製造：原物料 / 飲品 / 配方 ============
class Ingredient(models.Model):
    """共用原物料（茶底、鮮奶、珍珠、紙杯…）"""
    name = models.CharField("原物料", max_length=50)
    unit = models.CharField("單位", max_length=10)
    stock = models.DecimalField("目前庫存", max_digits=10, decimal_places=1, default=0)
    safety_stock = models.DecimalField("安全庫存", max_digits=10, decimal_places=1, default=0)
    reorder_qty = models.DecimalField("每次叫貨量", max_digits=10, decimal_places=1, default=0)
    unit_cost = models.DecimalField("進貨單價", max_digits=6, decimal_places=2, default=0)

    class Meta:
        verbose_name = "原物料"
        verbose_name_plural = "原物料"

    def __str__(self):
        return self.name

    @property
    def is_low(self):
        return self.stock <= self.safety_stock


class Product(models.Model):
    """飲品"""
    name = models.CharField("飲品名稱", max_length=50)
    price = models.PositiveIntegerField("售價")
    ingredients = models.ManyToManyField(Ingredient, through="Recipe", verbose_name="原物料")

    class Meta:
        verbose_name = "飲品"
        verbose_name_plural = "飲品"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """配方：一杯飲品用多少原物料"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="飲品")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, verbose_name="原物料")
    quantity = models.DecimalField("每杯用量", max_digits=8, decimal_places=1)

    class Meta:
        verbose_name = "配方"
        verbose_name_plural = "配方"
        unique_together = ("product", "ingredient")

    def __str__(self):
        return f"{self.product} - {self.ingredient} {self.quantity}"


# ============ 行銷：POS 訂單 ============
class Order(models.Model):
    created_at = models.DateTimeField("下單時間", auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name="經手人",
    )
    total = models.PositiveIntegerField("總金額", default=0)

    class Meta:
        verbose_name = "訂單"
        verbose_name_plural = "訂單"

    def __str__(self):
        return f"訂單 #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="飲品")
    quantity = models.PositiveIntegerField("杯數")
    unit_price = models.PositiveIntegerField("單價")

    class Meta:
        verbose_name = "訂單明細"
        verbose_name_plural = "訂單明細"

    def __str__(self):
        return f"{self.product} x{self.quantity}"


# ============ 人資 ============
class Employee(models.Model):
    MONTHLY, HOURLY = "monthly", "hourly"
    PAY_CHOICES = [(MONTHLY, "月薪（正職）"), (HOURLY, "時薪（計時）")]

    name = models.CharField("姓名", max_length=30)
    title = models.CharField("職稱", max_length=30, default="工讀生")
    pay_type = models.CharField("薪資類型", max_length=10, choices=PAY_CHOICES, default=HOURLY)
    monthly_salary = models.PositiveIntegerField("月薪", default=0)
    hourly_wage = models.PositiveIntegerField("時薪", default=0)
    hours = models.DecimalField("本月工時", max_digits=6, decimal_places=1, default=0)

    class Meta:
        verbose_name = "員工"
        verbose_name_plural = "員工"

    def __str__(self):
        return self.name

    def month_pay(self):
        if self.pay_type == self.MONTHLY:
            return self.monthly_salary
        return int(round(self.hourly_wage * self.hours))


class Payroll(models.Model):
    """薪資結算紀錄（每人每月一筆）"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="員工")
    month = models.CharField("月份", max_length=7)  # 例如 2026-11
    amount = models.PositiveIntegerField("實發薪資")
    paid_at = models.DateTimeField("結算時間", auto_now_add=True)

    class Meta:
        verbose_name = "薪資紀錄"
        verbose_name_plural = "薪資紀錄"
        unique_together = ("employee", "month")

    def __str__(self):
        return f"{self.month} {self.employee} {self.amount}"


# ============ 財會 ============
class Transaction(models.Model):
    INCOME, EXPENSE = "income", "expense"
    KIND_CHOICES = [(INCOME, "收入"), (EXPENSE, "支出")]
    SALES, PURCHASE, SALARY = "銷售收入", "進貨成本", "薪資支出"

    date = models.DateField("日期", default=timezone.localdate)
    kind = models.CharField("類型", max_length=10, choices=KIND_CHOICES)
    category = models.CharField("科目", max_length=20)
    amount = models.PositiveIntegerField("金額")
    note = models.CharField("說明", max_length=100, blank=True)

    class Meta:
        verbose_name = "收支"
        verbose_name_plural = "收支"

    def __str__(self):
        return f"{self.date} {self.category} {self.amount}"
