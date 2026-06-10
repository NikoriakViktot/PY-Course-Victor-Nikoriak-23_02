from django.urls import path
from . import views

# app_name — обов'язково якщо в головному urls.py вказано namespace=
# Дозволяє звертатись до маршрутів як: 'hello_app:index', 'hello_app:about'
app_name = "hello_app"

urlpatterns = [
    path('', views.index, name='index'),

    # ── Notes ──────────────────────────────────────────────────────
    path('notes/', views.note_list, name='note_list'),
    path('notes/new/', views.note_create, name='note_create'),
    path('notes/<int:pk>/', views.note_detail, name='note_detail'),
    path('notes/<int:pk>/edit/', views.note_edit, name='note_edit'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),

    # ── Notebooks ──────────────────────────────────────────────────
    path('notebooks/', views.notebook_list, name='notebook_list'),
    path('notebooks/new/', views.notebook_create, name='notebook_create'),
    path('notebooks/<int:pk>/edit/', views.notebook_edit, name='notebook_edit'),
    path('notebooks/<int:pk>/delete/', views.notebook_delete, name='notebook_delete'),

    # ── Tags ───────────────────────────────────────────────────────
    path('tags/new/', views.tag_create, name='tag_create'),
]