from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.notes_list, name="notes_list"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="notes/login.html"),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
    path("create/", views.note_create, name="note_create"),
    path("categories/", views.categories_list, name="categories_list"),
    path("api/notes/", views.api_notes, name="api_notes"),
    path("api/notes/<int:note_id>/", views.api_note_detail, name="api_note_detail"),
    path("categories/create/", views.categories_create, name="category_create"),
    path(
        "categories/<int:category_id>/edit",
        views.categories_update,
        name="categories_update",
    ),
    path(
        "categories/<int:category_id>/delete",
        views.categories_delete,
        name="categories_delete",
    ),
    path("<int:note_id>/", views.note_detail, name="note_detail"),
    path("<int:note_id>/delete/", views.note_delete, name="note_delete"),
]