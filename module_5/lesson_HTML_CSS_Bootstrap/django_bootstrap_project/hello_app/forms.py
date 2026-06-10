from django import forms
from .models import Note


class NoteForm(forms.ModelForm):
    """
    ModelForm — автоматично генерує поля форми з моделі Note.
    Django бере field types з моделі і генерує відповідні HTML inputs.
    CharField(max_length=200) → <input type="text" maxlength="200">
    TextField → <textarea>

    Теорія: DJANGO_TEMPLATES_BOOTSTRAP.md §7 — ModelForm internals.
    """

    class Meta:
        model = Note
        fields = ['title', 'content']  # які поля включати у форму
        widgets = {
            # Додаємо Bootstrap class='form-control' до кожного поля
            # Без цього Django рендерить bare HTML без Bootstrap стилів
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть назву нотатки...',
                'autofocus': True,
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Текст нотатки...',
            }),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Зміст',
        }