# Lesson 45

## Запуск сайту

```bash
cd lesson_45/notes_app
python manage.py migrate
python manage.py runserver
```

Відкрити:

```text
http://127.0.0.1:8000/
```

Демо-користувач:

```text
alice / alice12345
```

## Benchmark views

У другому терміналі:

```bash
cd lesson_45/notes_app
python benchmark_views.py
```

Скрипт послідовно викликає кілька endpoints, показує час кожного view, сумарний час і зберігає результат у `benchmark_results.json`.

## Висновок

Async-підхід для такого маленького локального Django app не завжди швидший, бо запити виконуються послідовно, а основна робота йде через ORM і render templates. Async краще проявляється, коли view очікує зовнішні API або багато одночасних підключень.
