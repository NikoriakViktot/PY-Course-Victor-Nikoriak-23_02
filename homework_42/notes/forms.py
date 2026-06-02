from django import forms
from django.core.exceptions import ValidationError
from .models import Category, Note

DATETIME_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


class NoteForm(forms.ModelForm):
    reminder = forms.DateTimeField(
        required=False,
        label="Нагадування",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format=DATETIME_LOCAL_FORMAT,
        ),
        input_formats=[DATETIME_LOCAL_FORMAT],
    )

    class Meta:
        model = Note
        fields = ["title", "text", "reminder", "category"]
        labels = {
            "title": "Назва",
            "text": "Текст",
            "category": "Категорія",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Наприклад: Ідеї для проєкту",
                }
            ),
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Коротко занотуй думку, план або нагадування...",
                }
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["title"]
        labels = {"title": "Назва категорії"}
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Наприклад: Робота"}
            ),
        }


class NoteFilterForm(forms.Form):
    query = forms.CharField(
        required=False,
        label="Пошук",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Назва або текст"}
        ),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        label="Категорія",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    reminder_from = forms.DateTimeField(
        required=False,
        label="Нагадування від",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format=DATETIME_LOCAL_FORMAT,
        ),
        input_formats=[DATETIME_LOCAL_FORMAT],
    )
    reminder_to = forms.DateTimeField(
        required=False,
        label="Нагадування до",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format=DATETIME_LOCAL_FORMAT,
        ),
        input_formats=[DATETIME_LOCAL_FORMAT],
    )
    ordering = forms.ChoiceField(
        required=False,
        label="Сортування",
        widget=forms.Select(attrs={"class": "form-select"}),
        choices=(
            ("-created_at", "Нові спочатку"),
            ("created_at", "Старі спочатку"),
            ("reminder", "Найближчі нагадування"),
            ("category__title", "За категорією"),
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        reminder_from = cleaned_data.get("reminder_from")
        reminder_to = cleaned_data.get("reminder_to")

        if reminder_from and reminder_to and reminder_from > reminder_to:
            raise ValidationError('Дата "від" не може бути пізніше дати "до".')

        return cleaned_data