from django import forms
from .models import Note, NoteGroup
class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'text', 'reminder', 'category', 'group']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 text-sm p-2.5 border'}),
            'text': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 text-sm p-2.5 border', 'rows': 3}),
            'reminder': forms.DateTimeInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 text-sm p-2.5 border', 'type': 'datetime-local'}),
            'category': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 text-sm p-2.5 border bg-white'}),
            'group': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 text-sm p-2.5 border bg-white'}),
        }
    def __init__(self, *args, **kwargs):
        # Обмежуємо список груп лише тими, де користувач є учасником
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['group'].queryset = NoteGroup.objects.filter(members=user)
            self.fields['group'].required = False
            self.fields['group'].empty_label = "Тільки особиста нотатка"