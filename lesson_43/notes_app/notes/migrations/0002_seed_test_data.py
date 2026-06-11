# Generated manually for homework 40

from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def create_test_data(apps, schema_editor):
    Category = apps.get_model("notes", "Category")
    Note = apps.get_model("notes", "Note")

    study = Category.objects.create(title="Study")
    work = Category.objects.create(title="Work")
    personal = Category.objects.create(title="Personal")

    now = timezone.now()

    Note.objects.create(
        title="Learn Django models",
        text="Create Category and Note models with a foreign key.",
        reminder=now + timedelta(days=1),
        category=study,
    )
    Note.objects.create(
        title="Prepare homework",
        text="Run migrations and check notes on the main page.",
        reminder=now + timedelta(days=2),
        category=work,
    )
    Note.objects.create(
        title="Buy groceries",
        text="Milk, bread, apples and tea.",
        reminder=now + timedelta(days=3),
        category=personal,
    )


def delete_test_data(apps, schema_editor):
    Category = apps.get_model("notes", "Category")
    Category.objects.filter(title__in=["Study", "Work", "Personal"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("notes", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_test_data, delete_test_data),
    ]
