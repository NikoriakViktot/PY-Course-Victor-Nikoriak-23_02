# Generated manually — adds group FK to Note and ShoppingList for group-based sharing

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('hello_app', '0002_shoppinglist_shared_with_todolist_shared_with'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='group',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='notes',
                to='auth.group',
            ),
        ),
        migrations.AddField(
            model_name='shoppinglist',
            name='group',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='shopping_lists',
                to='auth.group',
            ),
        ),
    ]
