from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    # Django built-in auth: login, logout, password change
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("hello_app.urls", namespace="hello_app")),
] + debug_toolbar_urls()
