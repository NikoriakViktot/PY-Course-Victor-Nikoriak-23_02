from django.shortcuts import render


def notes_list(request):
    notes = [
        {
            'title': 'Купити продукти',
            'content': 'Молоко, хліб, яйця, фрукти.',
            'created_at': '2026-05-21',
        },
        {
            'title': 'Підготувати домашнє',
            'content': 'Повторити Django templates та static files.',
            'created_at': '2026-05-20',
        },
        {
            'title': 'Ідея проєкту',
            'content': 'Зробити маленький нотатник з пошуком і фільтрами',
            'created_at': '2026-05-19',
        }
    ]

    context = {'notes': notes}
    return render(request, 'notes/index.html', context)