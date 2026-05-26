from django import forms
from .models import Category, Note


class NoteForm(forms.ModelForm):
    reminder = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = Note
        fields = ['title', 'text', 'reminder', 'category']


class NoteFilterForm(forms.Form):
    query = forms.CharField(required=False, label='Пошук за назвою')
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label='Категорія',
    )
    reminder_from = forms.DateTimeField(
        required=False,
        label='Нагадування від',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    reminder_to = forms.DateTimeField(
        required=False,
        label='Нагадування до',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )