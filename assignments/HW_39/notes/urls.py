from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.notes_index, name='notes_index'),
    path('create/', views.note_create, name='note_create'),
    path('<int:note_id>/', views.note_detail, name='note_detail'),
    path('<int:note_id>/delete/', views.note_delete, name='note_delete'),

    # Вбудована сторінка входу та наш вихід
    path('login/', auth_views.LoginView.as_view(template_name='notes/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
]