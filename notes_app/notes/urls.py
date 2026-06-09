from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('note/<int:note_id>/', views.note_detail, name='note_detail'),
]