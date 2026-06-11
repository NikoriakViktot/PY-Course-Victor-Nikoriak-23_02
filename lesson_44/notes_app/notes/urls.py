from django.urls import path

from .views import UserLoginView, UserLogoutView, note_create, note_delete, note_detail, notes_list, register

urlpatterns = [
    path("", notes_list, name="notes_list"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
    path("notes/create/", note_create, name="note_create"),
    path("notes/<int:pk>/", note_detail, name="note_detail"),
    path("notes/<int:pk>/delete/", note_delete, name="note_delete"),
]
