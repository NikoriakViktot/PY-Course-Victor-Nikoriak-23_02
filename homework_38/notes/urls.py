from django.urls import path
from .views import hello_notes

urlpatterns = [
    path('', hello_notes),
]