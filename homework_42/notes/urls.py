from django.urls import path

from .views import (
    api_note_detail,
    api_notes,
    categories_list,
    category_create,
    category_delete,
    category_update,
    note_create,
    note_delete,
    note_detail,
    notes_list,
)

urlpatterns = [
    path("", notes_list, name="notes_list"),
    path("create/", note_create, name="note_create"),
    path("categories/", categories_list, name="categories_list"),
    path("api/notes/", api_notes, name="api_notes"),
    path("api/notes/<int:note_id>/", api_note_detail, name="api_note_detail"),
    path("categories/create/", category_create, name="category_create"),
    path("categories/<int:category_id>/edit", category_update, name="category_update"),
    path("categories/<int:category_id>/delete", category_delete, name="category_delete"),
    path("<int:note_id>/", note_detail, name="note_detail"),
    path("<int:note_id>/delete/", note_delete, name="note_delete"),
]