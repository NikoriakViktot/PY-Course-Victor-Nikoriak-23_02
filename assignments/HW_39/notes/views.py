from django.shortcuts import render


def notes_index(request):
    notes_list = [
        {
            "id": 1,
            "title": "Теги розмітки HTML",
            "content": "HTML — це скелет сайту. Головне запам'ятати блочні теги (div, h1, p) та рядкові (span, a).",
            "date": "04.06.2026"
        },
        {
            "id": 2,
            "title": "Стилізація через CSS",
            "content": "CSS — це краса сайту. Вчимося міняти кольори, додавати тіні (box-shadow) та будувати гнучку сітку Grid.",
            "date": "04.06.2026"
        },
        {
            "id": 3,
            "title": "Статика в Django",
            "content": "Для підключення CSS-файлів обов'язково використовуємо тег {% load static %} на самому початку HTML-документа.",
            "date": "04.06.2026"
        }
    ]

    return render(request, 'notes/index.html', {'notes': notes_list})
