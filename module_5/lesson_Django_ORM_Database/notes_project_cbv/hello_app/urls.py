from django.urls import path
from . import views

# app_name — обов'язково якщо в головному urls.py вказано namespace=
# Дозволяє звертатись до маршрутів як: 'hello_app:index', 'hello_app:note_list'
app_name = "hello_app"

# ──────────────────────────────────────────────────────────────────────────────
# CBV vs FBV у urls.py:
#
#   FBV:  path('notes/', views.note_list, name='note_list')
#         → views.note_list — це вже callable функція
#
#   CBV:  path('notes/', views.NoteListView.as_view(), name='note_list')
#         → views.NoteListView — це клас, не callable!
#         → .as_view() → повертає callable функцію-обгортку
#         → Django router потребує callable, тому as_view() обов'язковий
#
#   as_view() робить щоразу при запиті:
#     1. Створює новий instance класу (View.__init__())
#     2. Встановлює request, args, kwargs на instance
#     3. Викликає instance.dispatch(request, *args, **kwargs)
#     4. dispatch() роутить: GET → get(), POST → post()
# ──────────────────────────────────────────────────────────────────────────────

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),

    # ── Notes ──────────────────────────────────────────────────────────────────
    path('notes/', views.NoteListView.as_view(), name='note_list'),
    path('notes/new/', views.NoteCreateView.as_view(), name='note_create'),
    path('notes/<int:pk>/', views.NoteDetailView.as_view(), name='note_detail'),
    path('notes/<int:pk>/edit/', views.NoteUpdateView.as_view(), name='note_edit'),
    path('notes/<int:pk>/delete/', views.NoteDeleteView.as_view(), name='note_delete'),

    # ── Notebooks ──────────────────────────────────────────────────────────────
    path('notebooks/', views.NotebookListView.as_view(), name='notebook_list'),
    path('notebooks/new/', views.NotebookCreateView.as_view(), name='notebook_create'),
    path('notebooks/<int:pk>/edit/', views.NotebookUpdateView.as_view(), name='notebook_edit'),
    path('notebooks/<int:pk>/delete/', views.NotebookDeleteView.as_view(), name='notebook_delete'),

    # ── Tags ───────────────────────────────────────────────────────────────────
    path('tags/new/', views.TagCreateView.as_view(), name='tag_create'),
]
