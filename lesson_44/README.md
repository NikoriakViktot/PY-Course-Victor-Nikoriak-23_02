# Lesson 44

## Запуск

```bash
cd lesson_44/notes_app
python manage.py migrate
python manage.py runserver
```

Відкрити:

```text
http://127.0.0.1:8000/
```

## Демо-користувачі після migrate

```text
admin / admin12345
alice / alice12345
bob / bob12345
```

`admin` має доступ до адмінки:

```text
http://127.0.0.1:8000/admin/
```

## Що додано

- login page
- logout button
- superuser для адмінки
- нотатка має owner
- користувач бачить/редагує/видаляє тільки свої персональні нотатки
- group notes доступні для перегляду учасникам групи
- перемикач Personal / Group notes
- додаткове extra: сторінка реєстрації нового користувача
