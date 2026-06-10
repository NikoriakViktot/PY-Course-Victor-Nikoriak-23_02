"""
forms.py — Django Forms з Crispy Bootstrap5

════════════════════════════════════════════════════════════════════
ПІДХІД ЦЬОГО ПРОЄКТУ: Crispy Forms (Рівень 3)
════════════════════════════════════════════════════════════════════

  forms.py:   FormHelper + Layout (Python tree) ← ЦЕЙ ФАЙЛ
  Template:   {% crispy form %} — 1 рядок!
  Результат:  Bootstrap5 styled + custom layout + автоматичні errors

  Порівняння Рівень 1/2/3 — дивись note_form.html коментарі та README.md §03.

════════════════════════════════════════════════════════════════════
ЩО ТАКЕ FormHelper?
════════════════════════════════════════════════════════════════════

FormHelper — об'єкт що описує:
  1. Атрибути <form> тегу (method, id, class, action)
  2. Layout форми (структуру полів у Bootstrap Grid)
  3. Поведінку рендерингу (form_tag=True, include_media=True)

FormHelper НЕ впливає на:
  - Валідацію (is_valid() працює так само)
  - cleaned_data (не змінюється)
  - Бізнес-логіку

Layout — Python-дерево що описує візуальну структуру:
  Layout(
      Fieldset('заголовок секції',
          Row(Column('поле1', col), Column('поле2', col)),
          Field('поле3', placeholder='...'),
      ),
      Submit('submit', 'Зберегти'),
  )
  → crispy рендерить відповідний Bootstrap5 HTML автоматично
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout, Submit, Row, Column, Fieldset, HTML, Div, Field
)
from .models import Note, Notebook, Tag, TodoList, ShoppingList, Reminder


# ─────────────────────────────────────────────────────────────────────────────
# NOTE FORM — Crispy Bootstrap5 Version
# ─────────────────────────────────────────────────────────────────────────────

class NoteForm(forms.ModelForm):
    """
    NoteForm з FormHelper та Layout.

    Використовується в: note_create, note_edit.
    FormHelper + Layout описує структуру форми у Python — шаблон містить лише {% crispy form %}.

    BEFORE (notes_project): виглядало так:
      class Meta:
          widgets = {
              'title': forms.TextInput(attrs={'class': 'form-control', ...}),
              'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
              'priority': forms.Select(attrs={'class': 'form-select'}),
              ...  # кожне поле вручну!
          }
      # Шаблон: 60+ рядків Bootstrap HTML

    AFTER (цей файл): FormHelper + Layout
      self.helper.layout = Layout(...)  # Python, не HTML
      # Шаблон: {% crispy form %}  → 1 рядок!
    """

    class Meta:
        model = Note
        # user, created_at, updated_at, is_archived — НЕ тут (security!)
        fields = ['title', 'content', 'priority', 'notebook', 'tags', 'is_pinned']
        labels = {
            'title': 'Заголовок',
            'content': 'Зміст',
            'priority': 'Пріоритет',
            'notebook': 'Записник',
            'tags': 'Теги',
            'is_pinned': 'Закріпити нотатку',
        }
        help_texts = {
            'notebook': 'Залиш порожнім — нотатка буде без записника.',
            'tags': 'Можна обрати кілька тегів.',
            'is_pinned': 'Закріплені нотатки відображаються першими.',
        }
        # NOTE: No widgets.attrs here!
        # crispy handles Bootstrap classes automatically via CRISPY_TEMPLATE_PACK = "bootstrap5"

    def __init__(self, *args, user=None, **kwargs):
        """
        Security + crispy FormHelper setup.

        user= parameter filters notebook/tags queryset to THIS user only.
        Alice не побачить записники Bob'а у своєму dropdown.
        """
        super().__init__(*args, **kwargs)

        # ── Security: filter FK/M:N by user ─────────────────────────────────
        if user is not None:
            self.fields['notebook'].queryset = Notebook.objects.filter(user=user)
            self.fields['tags'].queryset = Tag.objects.filter(user=user)
        else:
            self.fields['notebook'].queryset = Notebook.objects.none()
            self.fields['tags'].queryset = Tag.objects.none()

        self.fields['notebook'].empty_label = '── Без записника ──'
        self.fields['notebook'].required = False

        # ── Crispy FormHelper ────────────────────────────────────────────────
        # This replaces ALL widget attrs AND all Bootstrap HTML in the template
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'note-form'

        # Layout = Python tree → crispy renders Bootstrap5 HTML
        self.helper.layout = Layout(
            # Fieldset → <fieldset><legend>Основна інформація</legend>...</fieldset>
            Fieldset(
                'Основна інформація',
                # Field with extra HTML attrs (replaces widget attrs)
                Field('title', placeholder='Назва нотатки...', autofocus=True),
                # Row + Column → Bootstrap .row .col-md-4 .col-md-8
                Row(
                    Column('priority', css_class='col-md-4'),
                    Column('notebook', css_class='col-md-8'),
                ),
            ),
            Fieldset(
                'Зміст нотатки',
                Field('content', rows=4, placeholder='Текст нотатки...'),
            ),
            Fieldset(
                'Теги та параметри',
                Field('tags', size=3),  # size=3 обмежує висоту multi-select
                Div(
                    Field('is_pinned'),
                    css_class='form-check mt-2',
                ),
            ),
            # HTML — вставляє довільний HTML (без escaping!)
            HTML('<hr class="my-4">'),
            # Submit → <button type="submit" class="btn btn-primary me-2">
            Submit('submit', 'Зберегти нотатку', css_class='btn btn-primary me-2'),
            HTML('<a href="javascript:history.back()" class="btn btn-outline-secondary">Скасувати</a>'),
        )


# ─────────────────────────────────────────────────────────────────────────────
# NOTEBOOK FORM — Crispy Bootstrap5 Version
# ─────────────────────────────────────────────────────────────────────────────

class NotebookForm(forms.ModelForm):
    """
    NotebookForm з FormHelper.

    Демонструє color picker та is_default checkbox з crispy layout.
    """

    class Meta:
        model = Notebook
        fields = ['title', 'description', 'color', 'is_default']
        labels = {
            'title': 'Назва записника',
            'description': 'Опис',
            'color': 'Колір записника',
            'is_default': 'Записник за замовчуванням',
        }
        help_texts = {
            'is_default': 'Нові нотатки автоматично потраплятимуть у цей записник.',
            'color': 'Виберіть колір для візуальної ідентифікації записника.',
        }
        widgets = {
            # HTML5 color picker — crispy respects widget type but adds Bootstrap classes
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('title', placeholder='Назва записника...', autofocus=True),
            Row(
                Column(Field('color'), css_class='col-md-3'),
                Column('description', css_class='col-md-9'),
            ),
            Div(
                Field('is_default'),
                css_class='form-check my-2',
            ),
            HTML('<hr class="my-4">'),
            Submit('submit', 'Зберегти', css_class='btn btn-primary me-2'),
            HTML('<a href="javascript:history.back()" class="btn btn-outline-secondary">Скасувати</a>'),
        )


# ─────────────────────────────────────────────────────────────────────────────
# TAG FORM — Crispy Bootstrap5 Version
# ─────────────────────────────────────────────────────────────────────────────

class TagForm(forms.ModelForm):
    """
    TagForm з FormHelper та кастомною валідацією clean_name().
    """

    class Meta:
        model = Tag
        fields = ['name', 'color']
        labels = {'name': 'Назва тегу', 'color': 'Колір'}
        help_texts = {
            'name': 'Маленькі літери без пробілів. Наприклад: python, важливе, робота',
        }
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column(Field('name', placeholder='python, django, work...', autofocus=True),
                       css_class='col-md-9'),
                Column(Field('color'), css_class='col-md-3'),
            ),
            HTML('<hr class="my-4">'),
            Submit('submit', 'Створити тег', css_class='btn btn-primary me-2'),
            HTML('<a href="javascript:history.back()" class="btn btn-outline-secondary">Скасувати</a>'),
        )

    def clean_name(self):
        """Normalize: '  Python  ' → 'python'"""
        name = self.cleaned_data['name']
        normalized = name.lower().strip()
        if not normalized:
            raise forms.ValidationError("Назва тегу не може бути порожньою.")
        return normalized




class TodoListForm(forms.ModelForm):
    class Meta:
        model = TodoList
        fields = ['title', 'description']
        labels = {'title': 'Назва списку', 'description': 'Опис'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('title', placeholder='Список справ на тиждень...', autofocus=True),
            Field('description', rows=2, placeholder="Необов'язковий опис..."),
            HTML('<hr class="my-3">'),
            Submit('submit', 'Зберегти', css_class='btn btn-primary me-2'),
            HTML('<a href="javascript:history.back()" class="btn btn-outline-secondary">Скасувати</a>'),
        )


class TodoItemForm(forms.Form):
    text = forms.CharField(
        max_length=500,
        label='Завдання',
        widget=forms.TextInput(attrs={'placeholder': 'Нове завдання...', 'autofocus': True}),
    )
    due_date = forms.DateField(
        required=False,
        label='Термін',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Row(
                Column(Field('text', placeholder='Нове завдання...'),
                       css_class='col-md-7'),
                Column(Field('due_date'), css_class='col-md-3'),
                Column(
                    HTML('<label class="form-label">&nbsp;</label>'),
                    Submit('submit', '+ Додати', css_class='btn btn-primary w-100'),
                    css_class='col-md-2',
                ),
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
# SHOPPING FORMS
# ─────────────────────────────────────────────────────────────────────────────

class ShoppingListForm(forms.ModelForm):
    class Meta:
        model = ShoppingList
        fields = ['title', 'store_name']
        labels = {'title': 'Назва списку', 'store_name': 'Магазин'}
        help_texts = {'store_name': "Наприклад: АТБ, Сільпо (необов'язково)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('title', placeholder='Список на вихідні...', autofocus=True),
            Field('store_name', placeholder='АТБ, Сільпо...'),
            HTML('<hr class="my-3">'),
            Submit('submit', 'Зберегти', css_class='btn btn-primary me-2'),
            HTML('<a href="javascript:history.back()" class="btn btn-outline-secondary">Скасувати</a>'),
        )


class ShopItemForm(forms.Form):
    name = forms.CharField(max_length=200, label='Товар')
    quantity = forms.DecimalField(
        max_digits=8, decimal_places=2, initial=1, min_value=0.01,
        label='Кількість',
    )
    unit = forms.ChoiceField(
        choices=[('шт', 'шт'), ('кг', 'кг'), ('л', 'л'), ('г', 'г')],
        initial='шт', label='Од.',
    )
    estimated_price = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        label='Ціна ₴',
        min_value=0,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Row(
                Column(Field('name', placeholder='Молоко...'), css_class='col-md-4'),
                Column(Field('quantity'), css_class='col-md-2'),
                Column(Field('unit'), css_class='col-md-2'),
                Column(Field('estimated_price', placeholder='₴'), css_class='col-md-2'),
                Column(
                    HTML('<label class="form-label">&nbsp;</label>'),
                    Submit('submit', '+ Додати', css_class='btn btn-primary w-100'),
                    css_class='col-md-2',
                ),
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
# REMINDER FORM
# ─────────────────────────────────────────────────────────────────────────────

class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ['remind_at', 'message', 'repeat_pattern']
        labels = {
            'remind_at': 'Дата і час',
            'message': 'Повідомлення',
            'repeat_pattern': 'Повторення',
        }
        widgets = {
            'remind_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column(Field('remind_at'), css_class='col-md-4'),
                Column(Field('repeat_pattern'), css_class='col-md-3'),
                Column(Field('message', placeholder='Текст нагадування...'),
                       css_class='col-md-5'),
            ),
            Submit('submit', '+ Додати нагадування', css_class='btn btn-outline-primary btn-sm'),
        )


# ─────────────────────────────────────────────────────────────────────────────
# SHARE FORM
# ─────────────────────────────────────────────────────────────────────────────

class ShareForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Ім'я користувача",
        widget=forms.TextInput(attrs={'placeholder': 'username...', 'autofocus': True}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column(Field('username'), css_class='col-md-8'),
                Column(
                    HTML('<label class="form-label">&nbsp;</label>'),
                    Submit('submit', 'Поділитись', css_class='btn btn-primary w-100'),
                    css_class='col-md-4',
                ),
            ),
        )
