from django.db import models
class category(models.Model):
    """модель для категорій нотаток."""
    title = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.title
class note(models.Model):
    """модель для самих нотаток."""
    title = models.CharField(max_length=200)
    text = models.TextField()
    reminder = models.DateTimeField(null=True, blank=True)
    # поєднуємо нотатки з категорією (один-до-багатьох)
    # on_delete=models.CASCADE видалить нотатки, якщо видалити категорію
    category = models.ForeignKey(
        category,
        on_delete=models.CASCADE,
        related_name="notes"
    )
    def __str__(self):
        return self.title

from django.db import models

# Create your models here.
