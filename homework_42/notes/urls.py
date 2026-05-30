from django.urls import path

from .views import notes_list, note_create, note_delete, note_detail

urlpatterns = [
    path('', notes_list, name='notes_list'),

    path('create/', note_create, name='note_create'),
    path('<int:note_id>/', note_detail, name='note_detail'),
    path('<int:note_id>/delete/', note_delete, name='note_delete'),
]