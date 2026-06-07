from django.urls import path
from . import views

# app_name — обов'язково якщо в головному urls.py вказано namespace=
# Дозволяє звертатись до маршрутів як: 'hello_app:index', 'hello_app:about'
app_name = "hello_app"

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('notes/', views.note_list, name='note_list'),
]