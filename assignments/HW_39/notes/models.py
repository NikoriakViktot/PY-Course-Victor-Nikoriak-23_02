from django.db import models
from django.contrib.auth.models import User  # Імпортуємо модель користувача


class Category(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Note(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    reminder = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    # ПРИВ'ЯЗКА ДО КОРИСТУВАЧА: Якщо користувача видаляють, його нотатки теж видаляються (CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes', null=True, blank=True)

    def __str__(self):
        return self.title