from django.shortcuts import render
def notes_list_view(request):
    """view для відображення головної сторінки зі списком тестових нотаток."""
    # масив тестових даних (нотаток)
    test_notes = [
        {
            "title": "купити продукти",
            "content": "молоко, хліб, сир, куряче філе, яблука.",
            "created_at": "08.06.2026",
        },
        {
            "title": "дз звонок",
            "content": "зателефонувати ментору по django о 15:00.",
            "created_at": "08.06.2026",
        },
        {
            "title": "ідея проекту",
            "content": "створити асинхронний чат-бот для замовлення піци через django.",
            "created_at": "07.06.2026",
        },
    ]
    # передаємо дані у контекст шаблону
    context = {
        "test_notes": test_notes,
    }
    return render(request, "notes_list.html", context)
from django.shortcuts import render
from .models import Note

def main_page(request):
    # Отримуємо всі нотатки разом з їхніми категоріями
    notes = Note.objects.select_related('category').all()
    return render(request, 'index.html', {'notes': notes})