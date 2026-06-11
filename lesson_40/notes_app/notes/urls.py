from django.urls import path

from .views import notes_list

urlpatterns = [
    path("", notes_list, name="notes_list"),
]
