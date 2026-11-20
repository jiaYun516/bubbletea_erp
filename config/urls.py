from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),   # 後台：管理使用者、群組(角色)、原始資料
    path("", include("erp.urls")),     # 前端：登入、點單、庫存、財會、人資
]
