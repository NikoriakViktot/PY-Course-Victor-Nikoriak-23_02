"""
forms.py — Django Forms для Notes Platform

════════════════════════════════════════════════════════════════════
ЩО ТАКЕ ФОРМА DJANGO? (Trust Boundary)
════════════════════════════════════════════════════════════════════

Форма Django — це клас що виконує роль кордону довіри між:

  🔴 НЕБЕЗПЕЧНА ЗОНА               🟢 БЕЗПЕЧНА ЗОНА
  request.POST (рядки)     →      form.cleaned_data (Python-об'єкти)
  request.POST['priority'] = '2'  form.cleaned_data['priority'] = 2 (int!)
  request.POST['title'] = ''      → ValidationError (required!)
  request.POST['price'] = 'abc'   → ValidationError (not a number!)

Все що надходить від браузера = потенційно небезпечне.
Все що пройшло через is_valid() = типізовано та перевірено.

════════════════════════════════════════════════════════════════════
forms.ModelForm vs forms.Form:
════════════════════════════════════════════════════════════════════

  ModelForm — поля генеруються АВТОМАТИЧНО з моделі:
    class NoteForm(forms.ModelForm):
        class Meta:
            model = Note
            fields = ['title', 'priority']
    → Django читає Note.title (CharField) → forms.CharField
    → Django читає Note.priority (choices) → forms.TypedChoiceField
    → Вся валідація з моделі успадковується автоматично!

  Form — поля описуються ВРУЧНУ:
    class SearchForm(forms.Form):
        q = forms.CharField(max_length=200, required=False)
    → Для форм що не прив'язані до конкретної моделі

════════════════════════════════════════════════════════════════════
БЕЗПЕКА: Чому user не входить у fields?
════════════════════════════════════════════════════════════════════

  class NoteForm(ModelForm):
      class Meta:
          fields = ['title', 'content', ...]
          # user НЕ в полях! Якби був:
          # → Alice могла б підставити user_id=2 (Bob!)
          # → POST: title=Test&user=2 → нотатка від імені Bob!

  Правило: поля що виставляє сервер (user, created_by, ip_address)
           НІКОЛИ не повинні бути у формі.
           Їх встановлюємо в services.py через аргумент.

Теорія: DJANGO_FORMS.md
"""

from django import forms
from .models import Note, Notebook, Tag


# ─────────────────────────────────────────────────────────────────────────────
# NOTE FORM
# ─────────────────────────────────────────────────────────────────────────────

class NoteForm(forms.ModelForm):
    """
    Форма для створення та редагування нотатки.

    ════════════════════════════════════════════════════════════════
    АРХІТЕКТУРА ФОРМИ:
    ════════════════════════════════════════════════════════════════

    Поля та їх відображення:
      title    → CharField(max_length=200)   → TextInput
      content  → TextField(blank=True)       → Textarea
      priority → PositiveSmallIntegerField(choices) → Select
      notebook → ForeignKey(Notebook)        → ModelChoiceField → Select
      tags     → ManyToManyField(Tag)        → ModelMultipleChoiceField → CheckboxSelectMultiple
      is_pinned → BooleanField               → CheckboxInput

    Ключова особливість: __init__(user=None)
      Форма отримує user щоб фільтрувати FK/M:N queryset.
      Без цього Alice побачила б записники Bob'а у своєму dropdown!

    ════════════════════════════════════════════════════════════════
    ЯК ВИКЛИКАТИ ФОРМУ:
    ════════════════════════════════════════════════════════════════

      # GET запит — порожня форма:
      form = NoteForm(user=request.user)

      # GET запит — форма для редагування:
      form = NoteForm(instance=note, user=request.user)

      # POST запит — валідація даних:
      form = NoteForm(request.POST, user=request.user)

      # POST запит — редагування існуючої:
      form = NoteForm(request.POST, instance=note, user=request.user)
    """

    class Meta:
        """
        Meta клас визначає:
          model  → яку модель Django ORM використовувати
          fields → які поля включати (явне краще неявного!)
          widgets → як рендерити кожне поле в HTML

        Чому не fields = '__all__'?
          '__all__' включає ВСЕ включно з user, created_at, updated_at тощо.
          Це небезпечно! Завжди вказуй поля явно.
        """
        model = Note
        # Явний список полів — тільки те що користувач може змінити!
        # user, created_at, updated_at, is_archived — НЕ тут (їх встановлюємо в services)
        fields = ['title', 'content', 'priority', 'notebook', 'tags', 'is_pinned']

        widgets = {
            # TextInput: звичайний <input type="text">
            # attrs → словник HTML атрибутів що будуть додані до тегу
            'title': forms.TextInput(attrs={
                'class': 'form-control',            # Bootstrap 5: повна ширина + стиль
                'placeholder': 'Назва нотатки...',  # HTML placeholder
                'autofocus': True,                  # фокус автоматично при відкритті
            }),

            # Textarea: <textarea rows="8" class="form-control">
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,              # висота текстового поля (рядки)
                'placeholder': 'Текст нотатки...',
            }),

            # Select: <select class="form-select">
            # choices беруться автоматично з Note.PRIORITY_CHOICES
            'priority': forms.Select(attrs={
                'class': 'form-select',  # Bootstrap 5 стиль для select
            }),

            # Select для FK (ModelChoiceField):
            # queryset фільтрується в __init__ по user!
            'notebook': forms.Select(attrs={
                'class': 'form-select',
            }),

            # CheckboxSelectMultiple: для M:N тегів
            # Рендерить кожен тег як окремий <input type="checkbox">
            # Набагато зручніший UX ніж стандартний <select multiple>
            'tags': forms.CheckboxSelectMultiple(attrs={
                'class': 'list-unstyled',  # Bootstrap: прибрати bullet points
            }),

            # CheckboxInput: <input type="checkbox">
            'is_pinned': forms.CheckboxInput(attrs={
                'class': 'form-check-input',  # Bootstrap 5 стиль для чекбоксу
            }),
        }

        labels = {
            # Людські назви полів для <label> тегів
            # Без labels: Django використовує назву поля з великої літери
            'title': 'Заголовок',
            'content': 'Зміст',
            'priority': 'Пріоритет',
            'notebook': 'Записник',
            'tags': 'Теги',
            'is_pinned': 'Закріпити нотатку',
        }

        help_texts = {
            # Підказки під полями (рендеряться як <small class="form-text">)
            'notebook': 'Залиш порожнім — нотатка буде без записника.',
            'tags': 'Можна обрати кілька тегів.',
            'is_pinned': 'Закріплені нотатки завжди відображаються першими.',
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Ініціалізація форми з фільтрацією queryset по user.

        ════════════════════════════════════════════════════════════════
        НАВІЩО ПЕРЕВИЗНАЧАТИ __init__?
        ════════════════════════════════════════════════════════════════

        За замовчуванням ModelForm для ForeignKey та M:N генерує:
          self.fields['notebook'].queryset = Notebook.objects.all()
          self.fields['tags'].queryset = Tag.objects.all()

        Проблема: ALL() → всі записники і теги ВСІХ юзерів!
          - Alice відкриє форму і побачить записники Bob'а у dropdown
          - Alice може вибрати тег Bob'а для своєї нотатки

        Рішення: фільтрувати по user:
          self.fields['notebook'].queryset = Notebook.objects.filter(user=user)
          self.fields['tags'].queryset = Tag.objects.filter(user=user)
          → Alice бачить ТІЛЬКИ свої записники і теги!

        ════════════════════════════════════════════════════════════════
        ЧОМУ KEYWORD-ONLY ARGUMENT?  (user=None у визначенні)
        ════════════════════════════════════════════════════════════════

          Виклик: NoteForm(request.POST, user=request.user)
          ← user передається ЯВНО як keyword argument

          Якби user був позиційним: NoteForm(request.POST, request.user)
          ← незрозуміло для читача що це user!

          *args і **kwargs передаються до батьківського ModelForm.__init__:
          → super().__init__(*args, **kwargs) ← ОБОВ'ЯЗКОВО!
          → Без super().__init__() форма не ініціалізується!

        ════════════════════════════════════════════════════════════════
        ЩО ВІДБУВАЄТЬСЯ ВСЕРЕДИНІ:
        ════════════════════════════════════════════════════════════════

        Крок 1: super().__init__(*args, **kwargs)
          Django ModelForm ініціалізує:
          - bound/unbound стан (чи є request.POST?)
          - initial values (з instance або initial=)
          - поля форми з Meta.model
          - віджети з Meta.widgets

        Крок 2: if user is not None
          Фільтруємо queryset ПІСЛЯ ініціалізації (поля вже існують)
          self.fields — словник {field_name: Field instance}

        Крок 3: empty_label для notebook
          ModelChoiceField показує "--------" за замовчуванням.
          Змінюємо на більш зрозумілий текст.

        Args:
            *args: передаються до ModelForm (request.POST, request.FILES)
            user: auth.User instance для фільтрації queryset (keyword-only!)
            **kwargs: передаються до ModelForm (instance=, initial=, prefix=)
        """
        # ── Крок 1: ініціалізація батьківського ModelForm ───────────────────
        super().__init__(*args, **kwargs)
        # Після super().__init__: self.fields = {'title': CharField, 'notebook': ModelChoiceField, ...}

        # ── Крок 2: фільтрація queryset по user ────────────────────────────
        if user is not None:
            # Показуємо ТІЛЬКИ записники та теги цього конкретного юзера!
            self.fields['notebook'].queryset = Notebook.objects.filter(user=user)
            self.fields['tags'].queryset = Tag.objects.filter(user=user)
        else:
            # Якщо user не передано (помилка виклику або тести без user)
            # → порожні QuerySet: форма не покаже жодного запису
            self.fields['notebook'].queryset = Notebook.objects.none()
            self.fields['tags'].queryset = Tag.objects.none()

        # ── Крок 3: кастомний empty label для notebook ──────────────────────
        # empty_label: текст для порожнього варіанту (notebook=None)
        # Цей текст з'явиться першим у <select>
        self.fields['notebook'].empty_label = '── Без записника ──'
        # required=False дозволяє надіслати форму без вибору записника
        self.fields['notebook'].required = False


# ─────────────────────────────────────────────────────────────────────────────
# NOTEBOOK FORM
# ─────────────────────────────────────────────────────────────────────────────

class NotebookForm(forms.ModelForm):
    """
    Форма для створення та редагування записника.

    ════════════════════════════════════════════════════════════════
    ЦІКАВЕ ПОЛЕ: color (HTML5 Color Picker)
    ════════════════════════════════════════════════════════════════

    Стандартний TextInput рендерить <input type="text">.
    Якщо додати type="color" → браузер показує color picker:
      <input type="color" value="#4A90E2">
      → Клік → з'являється palitra вибору кольору
      → Повертає HEX рядок: "#FF5733"

    form-control-color — Bootstrap 5 клас спеціально для color input!
    Без нього color input буде виглядати некоректно.
    """

    class Meta:
        model = Notebook
        # user НЕ в полях! Встановлюється в services.create_notebook(user=request.user)
        fields = ['title', 'description', 'color', 'is_default']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва записника...',
                'autofocus': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опис (необов\'язково)...',
            }),
            # HTML5 color picker → <input type="color">
            # Значення: HEX рядок "#RRGGBB"
            'color': forms.TextInput(attrs={
                'type': 'color',                    # ключовий атрибут!
                'class': 'form-control form-control-color',  # Bootstrap 5
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
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


# ─────────────────────────────────────────────────────────────────────────────
# TAG FORM
# ─────────────────────────────────────────────────────────────────────────────

class TagForm(forms.ModelForm):
    """
    Форма для створення та редагування тегу.

    ════════════════════════════════════════════════════════════════
    ВАЛІДАЦІЯ НА РІВНІ ФОРМИ: clean_name()
    ════════════════════════════════════════════════════════════════

    clean_name() — викликається після to_python() + validate() для поля 'name'.
    Повертає нормалізоване значення яке потрапить у cleaned_data['name'].

    Нормалізація: "  Python  " → "python"
    Відповідає логіці в services.create_or_get_tag(name=name.lower().strip())
    """

    class Meta:
        model = Tag
        # user НЕ в полях! Встановлюється в services.create_or_get_tag(user=)
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'python, django, work...',
                'autofocus': True,
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color',
            }),
        }
        labels = {
            'name': 'Назва тегу',
            'color': 'Колір',
        }
        help_texts = {
            'name': 'Маленькі літери без пробілів. Наприклад: python, важливе, робота',
        }

    def clean_name(self):
        """
        Кастомна очистка поля name.

        ════════════════════════════════════════════════════════════════
        ПОРЯДОК ВИКОНАННЯ VALIDATION PIPELINE:
        ════════════════════════════════════════════════════════════════

        При виклику form.is_valid() для поля 'name':
          1. CharField.to_python(raw_value) → str
          2. CharField.validate(str) → перевірка required, max_length
          3. CharField.run_validators(str) → кастомні validators
          4. clean_name(self) ← ми тут! self.cleaned_data['name'] вже str
          5. (після всіх полів) clean() → крос-валідація

        self.cleaned_data['name'] вже:
          - є рядком (to_python гарантує)
          - пройшов required та max_length перевірки

        Наше завдання: нормалізувати (lowercase + strip)

        ВАЖЛИВО: завжди повертати значення!
          Якщо не return → cleaned_data['name'] = None!

        Returns:
            str: нормалізована назва (lowercase, stripped)
        """
        # self.cleaned_data['name'] — вже str після to_python() і validate()
        name = self.cleaned_data['name']

        # Нормалізація: видаляємо пробіли + приводимо до нижнього регістру
        # "  Python  " → "python"
        # "DJANGO" → "django"
        normalized = name.lower().strip()

        # Перевіряємо що після нормалізації не порожній рядок
        if not normalized:
            raise forms.ValidationError("Назва тегу не може бути порожньою.")

        return normalized  # ← ОБОВ'ЯЗКОВО повертати!
