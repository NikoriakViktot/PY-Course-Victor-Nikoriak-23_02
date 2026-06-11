from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils import timezone


def create_demo_data(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")
    Category = apps.get_model("notes", "Category")
    Note = apps.get_model("notes", "Note")

    admin, _ = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@example.com",
            "password": make_password("admin12345"),
            "is_staff": True,
            "is_superuser": True,
        },
    )

    alice, _ = User.objects.get_or_create(
        username="alice",
        defaults={
            "email": "alice@example.com",
            "password": make_password("alice12345"),
        },
    )

    bob, _ = User.objects.get_or_create(
        username="bob",
        defaults={
            "email": "bob@example.com",
            "password": make_password("bob12345"),
        },
    )

    group, _ = Group.objects.get_or_create(name="Study group")
    alice.groups.add(group)
    bob.groups.add(group)

    work_category, _ = Category.objects.get_or_create(title="Work")
    study_category, _ = Category.objects.get_or_create(title="Study")
    personal_category, _ = Category.objects.get_or_create(title="Personal")

    Note.objects.get_or_create(
        title="Personal plan",
        owner=alice,
        defaults={
            "text": "This note is visible only for Alice.",
            "category": personal_category,
            "reminder": timezone.now() + timezone.timedelta(days=1),
        },
    )

    Note.objects.get_or_create(
        title="Group meeting",
        owner=alice,
        group=group,
        defaults={
            "text": "This note is visible for all users from Study group.",
            "category": study_category,
            "reminder": timezone.now() + timezone.timedelta(days=2),
        },
    )

    Note.objects.get_or_create(
        title="Bob personal task",
        owner=bob,
        defaults={
            "text": "This note is visible only for Bob.",
            "category": work_category,
            "reminder": None,
        },
    )


def remove_demo_data(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")
    Category = apps.get_model("notes", "Category")

    User.objects.filter(username__in=["admin", "alice", "bob"]).delete()
    Group.objects.filter(name="Study group").delete()
    Category.objects.filter(title__in=["Work", "Study", "Personal"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("notes", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_demo_data, remove_demo_data),
    ]
