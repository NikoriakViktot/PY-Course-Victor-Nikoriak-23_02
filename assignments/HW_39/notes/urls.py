from django.urls import path
from . import views

urlpatterns = [
    path('', views.notes_index, name='notes_index'),
]