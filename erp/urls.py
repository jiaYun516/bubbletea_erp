from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="pos"), name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="erp/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("pos/", views.pos, name="pos"),
    path("inventory/", views.inventory, name="inventory"),
    path("inventory/restock/<int:pk>/", views.restock, name="restock"),
    path("finance/", views.finance, name="finance"),
    path("hr/", views.hr, name="hr"),
]
