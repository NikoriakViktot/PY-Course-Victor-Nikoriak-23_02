from django.urls import path

from .views import (
    note_api_create,
    note_api_detail,
    note_api_update,
    note_create,
    note_delete,
    note_detail,
    notes_api_list,
    notes_list,
)

urlpatterns = [
    path("", notes_list, name="notes_list"),
    path("notes/create/", note_create, name="note_create"),
    path("notes/<int:pk>/", note_detail, name="note_detail"),
    path("notes/<int:pk>/delete/", note_delete, name="note_delete"),
    path("api/notes/", notes_api_list, name="notes_api_list"),
    path("api/notes/create/", note_api_create, name="note_api_create"),
    path("api/notes/<int:pk>/", note_api_detail, name="note_api_detail"),
    path("api/notes/<int:pk>/update/", note_api_update, name="note_api_update"),
]
