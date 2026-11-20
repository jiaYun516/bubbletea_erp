from django.contrib import admin

from .models import (
    Employee, Ingredient, Order, OrderItem, Payroll, Product, Recipe, Transaction,
)

admin.site.site_header = "手搖飲店 ERP 後台"
admin.site.site_title = "手搖飲店 ERP"


class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 1


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price")
    inlines = [RecipeInline]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "stock", "safety_stock", "reorder_qty", "unit_cost")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "created_by", "total")
    inlines = [OrderItemInline]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "pay_type", "monthly_salary", "hourly_wage", "hours")


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ("month", "employee", "amount", "paid_at")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "kind", "category", "amount", "note")
    list_filter = ("kind", "category")
