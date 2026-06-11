from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models


class Category(models.Model):
    title = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["title"]

    def __str__(self):
        return self.title


class Note(models.Model):
    title = models.CharField(max_length=150)
    text = models.TextField()
    reminder = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="notes")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name="notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["reminder", "title"]

    def __str__(self):
        return self.title

    @property
    def is_group_note(self):
        return self.group is not None
