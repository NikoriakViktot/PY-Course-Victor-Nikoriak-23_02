from django.contrib import admin
from .models import Note, Notebook, Tag, Reminder, TodoList, TodoItem, ShoppingList, ShopItem

admin.site.register(Note)
admin.site.register(Notebook)
admin.site.register(Tag)
admin.site.register(Reminder)
admin.site.register(TodoList)
admin.site.register(TodoItem)
admin.site.register(ShoppingList)
admin.site.register(ShopItem)
