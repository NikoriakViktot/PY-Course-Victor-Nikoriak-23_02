from django.urls import path
from . import views
urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('note/<int:note_id>/', views.note_detail, name='note_detail'),
    path('register/', views.register_view, name='register_page'),
    path('login/', views.login_view, name='login_page'),
    path('logout/', views.logout_view, name='logout_action'),
]