from django.urls import path
from .views import hello_notes

# urlpatterns = [
#     path("", hello_notes, name="hello_notes"),
# ]

urlpatterns = [
    path("", notes_list_view, name="notes_list"),
]