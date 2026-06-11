from django.urls import path

from .views import note_create, note_delete, note_detail, notes_list

urlpatterns = [
    path("", notes_list, name="notes_list"),
    path("notes/create/", note_create, name="note_create"),
    path("notes/<int:pk>/", note_detail, name="note_detail"),
    path("notes/<int:pk>/delete/", note_delete, name="note_delete"),
]
