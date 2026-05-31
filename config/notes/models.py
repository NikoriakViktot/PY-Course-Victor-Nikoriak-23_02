from django.db import models


class Category(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Note(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    reminder = models.DateTimeField()

    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.title