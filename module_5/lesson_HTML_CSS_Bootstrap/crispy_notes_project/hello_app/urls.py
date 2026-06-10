from django.urls import path
from . import views

app_name = "hello_app"

urlpatterns = [
    path('', views.index, name='index'),

    # ── Notes (main CRUD) ──────────────────────────────────────────────────────
    path('notes/', views.note_list, name='note_list'),
    path('notes/new/', views.note_create, name='note_create'),
    path('notes/<int:pk>/', views.note_detail, name='note_detail'),
    path('notes/<int:pk>/edit/', views.note_edit, name='note_edit'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),

    # ── Notebooks ──────────────────────────────────────────────────────────────
    path('notebooks/', views.notebook_list, name='notebook_list'),
    path('notebooks/new/', views.notebook_create, name='notebook_create'),
    path('notebooks/<int:pk>/edit/', views.notebook_edit, name='notebook_edit'),
    path('notebooks/<int:pk>/delete/', views.notebook_delete, name='notebook_delete'),

    # ── Tags ───────────────────────────────────────────────────────────────────
    path('tags/new/', views.tag_create, name='tag_create'),

    # ── Registration ───────────────────────────────────────────────────────────
    path('register/', views.register, name='register'),

    # ── TodoList ───────────────────────────────────────────────────────────────
    path('todo/',                             views.todo_list_list,    name='todo_list'),
    path('todo/new/',                         views.todo_list_create,  name='todo_create'),
    path('todo/<int:pk>/',                    views.todo_list_detail,  name='todo_detail'),
    path('todo/<int:pk>/edit/',               views.todo_list_edit,    name='todo_edit'),
    path('todo/<int:pk>/delete/',             views.todo_list_delete,  name='todo_delete'),
    path('todo/<int:pk>/share/',              views.todo_list_share,   name='todo_share'),
    path('todo/<int:list_pk>/items/add/',     views.todo_item_add,     name='todo_item_add'),
    path('todo/items/<int:pk>/toggle/',       views.todo_item_toggle,  name='todo_item_toggle'),
    path('todo/items/<int:pk>/delete/',       views.todo_item_delete,  name='todo_item_delete'),

    # ── ShoppingList ────────────────────────────────────────────────────────────
    path('shopping/',                              views.shopping_list_list,    name='shopping_list'),
    path('shopping/new/',                          views.shopping_list_create,  name='shopping_create'),
    path('shopping/<int:pk>/',                     views.shopping_list_detail,  name='shopping_detail'),
    path('shopping/<int:pk>/edit/',                views.shopping_list_edit,    name='shopping_edit'),
    path('shopping/<int:pk>/delete/',              views.shopping_list_delete,  name='shopping_delete'),
    path('shopping/<int:pk>/share/',               views.shopping_list_share,   name='shopping_share'),
    path('shopping/<int:list_pk>/items/add/',      views.shop_item_add,         name='shop_item_add'),
    path('shopping/items/<int:pk>/toggle/',        views.shop_item_toggle,      name='shop_item_toggle'),
    path('shopping/items/<int:pk>/delete/',        views.shop_item_delete,      name='shop_item_delete'),

    # ── Reminders ──────────────────────────────────────────────────────────────
    path('notes/<int:note_pk>/reminders/add/', views.reminder_create, name='reminder_create'),
    path('reminders/<int:pk>/delete/',         views.reminder_delete,  name='reminder_delete'),
]
