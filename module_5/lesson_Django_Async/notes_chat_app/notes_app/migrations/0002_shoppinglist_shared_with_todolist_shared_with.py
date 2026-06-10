# Generated manually — adds shared_with M2M to TodoList and ShoppingList

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notes_app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='todolist',
            name='shared_with',
            field=models.ManyToManyField(
                blank=True,
                related_name='shared_todo_lists',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Поділитись з',
            ),
        ),
        migrations.AddField(
            model_name='shoppinglist',
            name='shared_with',
            field=models.ManyToManyField(
                blank=True,
                related_name='shared_shopping_lists',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Поділитись з',
            ),
        ),
    ]
