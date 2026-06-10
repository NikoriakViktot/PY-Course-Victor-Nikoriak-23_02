# Django Crispy Forms — від нуля до практики

> Джерело: [django-crispy-forms.readthedocs.io](https://django-crispy-forms.readthedocs.io/en/latest/)
> Версія: crispy-forms ≥ 2.x + crispy-bootstrap5

---

## Як читати цей файл

Цей довідник побудований **від простого до складного**:

| Рівень | Що тут | Для кого |
|--------|--------|----------|
| [🟢 Старт](#-старт-перша-crispy-форма-за-5-хвилин) | Встановлення + перша форма за 5 хвилин | Повний початківець |
| [🟡 Практика](#-практика-formhelper--layout) | FormHelper, Layout, всі компоненти | Вже знаєш базу |
| [🔵 Довідник](#-довідник-повний-api) | Formsets, Dynamic API, template packs | Повний контроль |

> **Рекомендація:** якщо ти вперше бачиш crispy-forms — читай зверху вниз, не перестрибуй.
> Якщо шукаєш конкретний компонент — використовуй [таблицю Layout об'єктів](#таблиця-layout-обєктів).

---

## 🟢 Старт: Перша Crispy Форма за 5 хвилин

### Проблема: чому виникає "HTML-спагетті"?

Уяви що тобі треба відобразити форму з Bootstrap 5. Без crispy ти пишеш:

```html
<!-- ❌ Без crispy: 18 рядків HTML для ОДНОГО поля -->
<div class="mb-3">
  <label for="id_title" class="form-label fw-semibold">
    Заголовок
    <span class="text-danger">*</span>
  </label>
  <input type="text"
         name="title"
         id="id_title"
         class="form-control {% if form.title.errors %}is-invalid{% endif %}"
         required>
  {% if form.title.errors %}
    {% for error in form.title.errors %}
    <div class="invalid-feedback">{{ error }}</div>
    {% endfor %}
  {% endif %}
</div>
<!-- повторити для КОЖНОГО поля... -->
```

І так для кожного поля. 5 полів = ~90 рядків HTML.
При зміні форми — правиш HTML у шаблоні.
При зміні Bootstrap — правиш кожен шаблон.

З crispy:
```html
<!-- ✅ З crispy: 1 рядок — і Bootstrap, і валідація, і структура -->
{% crispy form %}
```

> **🧠 Ментальна модель:** crispy-forms переміщує Bootstrap-розмітку з шаблону у Python-код.
> Шаблон стає тонким (`{% crispy form %}`), а форма описує саму себе (FormHelper + Layout).

---

### Крок 1: Встановлення

```bash
pip install django-crispy-forms crispy-bootstrap5
```

```python
# settings.py — додай ДВА пакети в INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'crispy_forms',       # ← 1. базовий пакет
    'crispy_bootstrap5',  # ← 2. template pack для Bootstrap 5
]

# Вкажи який CSS-фреймворк використовуєш
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
```

> **Чому два пакети?** З версії 2.0 crispy розділив: `crispy_forms` — ядро, а Bootstrap-шаблони —
> окремий `crispy_bootstrap5`. Це дозволяє підключити інший фреймворк (Tailwind, Bulma) без зміни ядра.

---

### Крок 2: Підключи у шаблоні

```html
<!-- У верхній частині шаблону — одного разу на файл -->
{% load crispy_forms_tags %}

<!-- І де потрібно показати форму -->
{% crispy form %}
```

Ось і все! Форма рендериться з Bootstrap 5: `form-control`, `form-label`, `invalid-feedback` — все автоматично.

---

### Крок 3: FormHelper — описуємо форму з Python

Без FormHelper crispy просто додає Bootstrap-класи. З FormHelper — ти описуєш:
- метод форми (`POST`/`GET`)
- порядок і структуру полів (Layout)
- кнопку Submit

```python
# forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit

class ContactForm(forms.Form):
    name    = forms.CharField(label='Ваше ім\'я')
    email   = forms.EmailField(label='Email')
    message = forms.CharField(widget=forms.Textarea, label='Повідомлення')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # FormHelper — прикріплюємо до форми через self.helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'          # <form method="post">
        self.helper.layout = Layout(
            'name',                               # поле за іменем
            'email',
            'message',
            Submit('submit', 'Надіслати'),         # кнопка submit
        )
```

```python
# views.py — нічого особливого
def contact(request):
    form = ContactForm()
    return render(request, 'contact.html', {'form': form})
```

```html
<!-- contact.html -->
{% load crispy_forms_tags %}
{% crispy form %}
```

> **🧠 Що відбувається:** `{% crispy form %}` знаходить `form.helper`, дивиться на `form.helper.layout`,
> і рендерить кожен `Layout` об'єкт через Bootstrap 5 шаблони. Це і є увесь "магія".

---

### Крок 4: Перевір що все працює

Після першого запуску переконайся:
- Форма виглядає як Bootstrap (label + input + кнопка)
- Червоні помилки валідації з'являються автоматично при порожньому submit
- Немає `ModuleNotFoundError: No module named 'crispy_forms'`

---

## 🟡 Практика: FormHelper + Layout

### FormHelper — що він контролює

```python
self.helper = FormHelper()

# Атрибути <form> тегу
self.helper.form_method = 'post'          # POST або GET
self.helper.form_id = 'my-form'           # id="my-form"
self.helper.form_class = 'my-class'       # class="my-class"
self.helper.form_action = '/submit/'      # action="/submit/"

# Поведінка
self.helper.form_tag = True               # True = рендерить <form>...</form>
                                          # False = тільки поля (корисно для AJAX)
self.helper.disable_csrf = False          # True = прибрати CSRF (рідко потрібно)
self.helper.include_media = True          # Вставляти form.media автоматично
self.helper.form_show_errors = True       # Показувати помилки
self.helper.form_show_labels = True       # Показувати label
```

> **💡 Найчастіше використовують:** `form_method`, `form_tag`, `form_id`. Решта — за потребою.

### FormHelper з прив'язаною формою

Якщо форма велика і ти не хочеш вручну перераховувати всі поля — передай `self` у FormHelper:

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.helper = FormHelper(self)   # ← crispy сам знайде всі поля
    # Тепер можна не писати Layout() — Django автоматично побудує дефолтний
```

---

### Layout — як описати структуру форми

`Layout` — це дерево об'єктів що описує порядок і структуру полів.

```python
from crispy_forms.layout import Layout, Fieldset, Row, Column, Field, Submit, HTML, Div

self.helper.layout = Layout(
    'simple_field',                              # просто ім'я поля — рядок
    Field('title', placeholder='Підказка'),      # поле з атрибутами
    Row(                                         # горизонтальний рядок (Bootstrap row)
        Column('first_name', css_class='col-md-6'),
        Column('last_name',  css_class='col-md-6'),
    ),
    Fieldset('Назва секції',                     # <fieldset><legend>
        'field_1',
        'field_2',
    ),
    HTML('<hr>'),                                # довільний HTML
    Submit('submit', 'Зберегти'),               # кнопка
)
```

> **🧠 Правило:** поля вказуєш як рядки (`'title'`) або через `Field('title', ...)`.
> `Field` дозволяє задати додаткові HTML-атрибути.

---

### Таблиця Layout об'єктів

#### Базові (з `crispy_forms.layout`)

| Об'єкт | HTML що генерується | Коли використовувати |
|--------|---------------------|----------------------|
| `'field_name'` | стандартне поле | просто вказати поле |
| `Field('field', placeholder='...')` | поле + атрибути | потрібен `placeholder`, `rows`, `autofocus` |
| `Field('field', type='hidden')` | `<input type="hidden">` | приховане поле |
| `Row(Column('f', css_class='col-md-6'), ...)` | `<div class="row">` | кілька полів в один рядок |
| `Fieldset('Назва', 'f1', 'f2')` | `<fieldset><legend>Назва` | групування полів у секції |
| `Div('field', css_class='my-class')` | `<div class="my-class">` | обгортка для кастомного стилю |
| `HTML('<hr>')` | довільний HTML | розділювачі, підказки, посилання |
| `Submit('name', 'Текст')` | `<input type="submit">` | кнопка відправки |
| `Button('name', 'Текст')` | `<button type="button">` | звичайна кнопка |
| `Reset('name', 'Текст')` | `<input type="reset">` | кнопка скидання |
| `Hidden('name', 'value')` | `<input type="hidden">` | прихована константа |
| `ButtonHolder(Submit(...), Button(...))` | `<div class="buttonHolder">` | група кнопок |
| `MultiField('label', 'f1', 'f2')` | кілька полів під одним label | рідкісний випадок |

#### Bootstrap-специфічні (з `crispy_forms.bootstrap`)

| Об'єкт | Що показує | Приклад |
|--------|-----------|---------|
| `AppendedText('field', '$')` | Input з суфіксом | Ціни, одиниці |
| `PrependedText('field', '@')` | Input з префіксом | Username, символи |
| `PrependedAppendedText('f', '$', '.00')` | Обидва разом | Ціна з центами |
| `InlineCheckboxes('field')` | Чекбокси в рядок | MultipleChoiceField |
| `InlineRadios('field')` | RadioSelect в рядок | ChoiceField з RadioSelect |
| `StrictButton('Текст', css_class='btn-success')` | `<button>` (не `<input>`) | Кнопки з довільним CSS |
| `FieldWithButtons('field', StrictButton("Go!"))` | Input + кнопка поряд | Пошук, submit-in-group |
| `Tab('Назва', ...)` всередині `TabHolder` | Bootstrap tabs | Форма з вкладками |
| `AccordionGroup('Назва', ...)` в `Accordion` | Bootstrap accordion | Великі форми |
| `Modal(Field(...), css_id='my-id', title='T')` | Bootstrap modal | Форми у модалках |
| `Alert(content='Попередження')` | Bootstrap alert | Інфо-повідомлення у формі |
| `UneditableField('field')` | Поле тільки для читання | Показати але не редагувати |

---

### Атрибути Layout об'єктів

```python
# kwargs → стають HTML атрибутами
Field('title', placeholder='Підказка')       # placeholder="Підказка"
Field('title', autofocus=True)               # autofocus
Field('title', rows=8)                       # rows="8" (textarea)
Field('title', type='hidden')                # type="hidden"
Field('title', data_custom="val")            # data-custom="val" (підкреслення → дефіс!)

# Спеціальні kwargs
Field('title', css_class="extra-class")      # додатковий CSS клас
Field('title', css_id="my-id")              # HTML id
Field('title', wrapper_class="mt-3")        # клас для обгортаючого <div>
Field('title', template="custom.html")      # кастомний шаблон для цього поля
```

> **💡 Підкреслення → дефіс:** у Python kwargs підкреслення `_` у HTML стає `-`.
> `data_name="val"` → `data-name="val"`. Виняток: `css_class`, `css_id`, `wrapper_class`.

---

### Практичні приклади

#### Двоколонковий Layout

```python
self.helper.layout = Layout(
    Row(
        Column('first_name', css_class='col-md-6'),
        Column('last_name',  css_class='col-md-6'),
    ),
    Row(
        Column('email', css_class='col-md-8'),
        Column('phone', css_class='col-md-4'),
    ),
    Submit('submit', 'Зберегти'),
)
```

#### Форма з секціями (Fieldset)

```python
self.helper.layout = Layout(
    Fieldset('Персональні дані',
        'first_name', 'last_name', 'email',
    ),
    Fieldset('Адреса',
        Row(
            Column('city',    css_class='col-md-6'),
            Column('country', css_class='col-md-6'),
        ),
    ),
    HTML('<hr>'),
    Submit('submit', 'Зберегти', css_class='btn btn-primary me-2'),
    HTML('<a href="#" class="btn btn-outline-secondary">Скасувати</a>'),
)
```

#### Форма з вкладками

```python
from crispy_forms.bootstrap import TabHolder, Tab

self.helper.layout = Layout(
    TabHolder(
        Tab('Основне',    'title', 'content'),
        Tab('Параметри',  'priority', 'tags'),
        Tab('Нагадування', 'remind_at'),
    ),
    Submit('submit', 'Зберегти'),
)
```

#### Input з префіксом / суфіксом

```python
from crispy_forms.bootstrap import PrependedText, AppendedText

self.helper.layout = Layout(
    PrependedText('username', '@'),
    AppendedText('discount', '%'),
    PrependedText('price', '$', placeholder='0.00'),
)
```

#### Кнопки у рядок через HTML

```python
HTML('<hr class="my-4">'),
Submit('submit', 'Зберегти', css_class='btn btn-primary me-2'),
HTML('<a href="{% url \'note_list\' %}" class="btn btn-outline-secondary">Скасувати</a>'),
```

---

### Template Tags та Фільтри

```html
{% load crispy_forms_tags %}

{# Основний тег — повний рендеринг з FormHelper #}
{% crispy form %}

{# З явним helper (якщо helper не прив'язаний до форми) #}
{% crispy form my_helper %}

{# Фільтр — швидкий Bootstrap-стиль без FormHelper #}
{{ form|crispy }}

{# Formset — передаємо helper явно #}
{% crispy formset helper %}

{# Одне поле окремо #}
{{ form.title|as_crispy_field }}
```

**Коли `{% crispy %}` vs `|crispy`:**

| | `{% crispy form %}` | `{{ form\|crispy }}` |
|--|--------------------|--------------------|
| FormHelper + Layout | Так — повний контроль | Ні — тільки Bootstrap-класи |
| `<form>` тег + CSRF | Так (за замовч.) | Ні |
| Кнопка Submit | Через Layout | Не включається |
| Коли | Production | Швидкий прогляд |

> **💡 Правило:** для будь-якої реальної форми — завжди `{% crispy form %}` з FormHelper.
> `|crispy` — тільки для швидкого перегляду під час розробки.

---

### Типові помилки початківців

#### ❌ Забув `{% load crispy_forms_tags %}`

```html
<!-- ❌ Помилка: TemplateSyntaxError: Invalid block tag 'crispy' -->
{% crispy form %}

<!-- ✅ Правильно: load обов'язково на початку шаблону -->
{% load crispy_forms_tags %}
{% crispy form %}
```

#### ❌ Не встановив `crispy_bootstrap5` в INSTALLED_APPS

```python
# ❌ Помилка: TemplateDoesNotExist: bootstrap5/uni_form.html
INSTALLED_APPS = ['crispy_forms']   # тільки ядро, немає template pack!

# ✅ Потрібні обидва
INSTALLED_APPS = ['crispy_forms', 'crispy_bootstrap5']
```

#### ❌ Забув `form_method` — форма відправляється GET

```python
# ❌ Без form_method — за замовч. POST, але явний код краще
self.helper = FormHelper()
# форма рендериться але метод невідомий

# ✅ Завжди вказуй явно
self.helper.form_method = 'post'
```

#### ❌ `{% crispy %}` без аргументу → IndexError

```html
<!-- ❌ Помилка: IndexError: pop index out of range -->
{% crispy %}

<!-- ✅ Правильно: обов'язково передати форму -->
{% crispy form %}
```

#### ❌ `{% crispy form %}` всередині HTML-коментара

```html
<!-- ❌ HTML коментар НЕ ховає Django теги — crispy ВИКОНАЄТЬСЯ! -->
<!-- {% crispy form %} -->

<!-- ✅ Для відображення тегу як тексту: HTML entities -->
&#123;% crispy form %&#125;

<!-- ✅ Або verbatim блок -->
{% verbatim %}{% crispy form %}{% endverbatim %}
```

> **🧠 Чому:** Django template engine обробляє `{% %}` теги ДО того як браузер побачить HTML-коментар.
> HTML-коментар — це просто текст для браузера. Django його не розуміє.

#### ❌ Забуває FilterQuery для FK поля

```python
# ❌ Безпечність: user може прив'язати чужій notebook!
class NoteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

# ✅ Завжди фільтруй FK поля по поточному user
class NoteForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['notebook'].queryset = Notebook.objects.filter(user=user)
        self.helper = FormHelper()
```

---

## 🔵 Довідник: Повний API

### Всі атрибути FormHelper

| Атрибут | За замовч. | Опис |
|---------|------------|------|
| `form_method` | `'POST'` | HTTP-метод: `'POST'` або `'GET'` |
| `form_action` | `''` | URL для `action=""` |
| `form_id` | `''` | HTML `id="..."` |
| `form_class` | `''` | CSS-класи для `<form>` |
| `attrs` | `{}` | Довільні атрибути: `{'data_id': '/url'}` |
| `form_tag` | `True` | `False` = рендерить без `<form>` тегів |
| `disable_csrf` | `False` | Вимкнути CSRF (для `form_tag=False`) |
| `include_media` | `True` | Вставляти `{{ form.media }}` |
| `render_unmentioned_fields` | `False` | Рендерити поля не з Layout |
| `render_hidden_fields` | `False` | Рендерити всі hidden-поля |
| `render_required_fields` | `False` | Рендерити всі required-поля |
| `form_show_errors` | `True` | Показувати помилки |
| `form_show_labels` | `True` | Показувати labels |
| `form_error_title` | `None` | Заголовок блоку non-field помилок |
| `template` | (авто) | Кастомний шаблон форми |
| `field_template` | (авто) | Кастомний шаблон поля |
| `template_pack` | `settings` | Перевизначити template pack |

---

### Formsets

```python
from django.forms.models import formset_factory
from crispy_forms.helper import FormHelper

ExampleFormSet = formset_factory(ExampleForm, extra=3)

class ExampleFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.layout = Layout('favorite_color', 'favorite_food')
        self.render_required_fields = True
        self.add_input(Submit('submit', 'Зберегти'))
```

```python
# views.py
formset = ExampleFormSet()
helper  = ExampleFormSetHelper()
return render(request, 'template.html', {'formset': formset, 'helper': helper})
```

```html
{% load crispy_forms_tags %}
{% crispy formset helper %}   {# helper передається явно! #}
```

#### Formset без зовнішнього `<form>`

```html
<form method="POST">
    {% csrf_token %}
    {% crispy formset helper %}
    <button class="btn btn-primary">Зберегти</button>
</form>
```

#### Extra Context у formset layout

```python
self.layout = Layout(
    HTML('{% if forloop.first %}<h5>Перший елемент</h5>{% endif %}'),
    Fieldset('Елемент {{ forloop.counter }}', 'field'),
)
```

#### Таблична форма формсету

```python
helper.template = 'bootstrap5/table_inline_formset.html'
```

---

### Динамічний Layout API

> Змінювати Layout у view — корисно для умовних форм (різний layout для різних user roles, etc.)

#### Вибір за slice

```python
form.helper[1:3]       # елементи 1 і 2
form.helper[2]         # третій елемент
form.helper[:-1]       # всі крім останнього
form.helper[0][0]      # перший у першому вкладеному
```

#### `wrap` — обгорнути кожен елемент

```python
# БУЛО: Layout('f1', 'f2', 'f3')
form.helper[1:3].wrap(Field, css_class="highlighted")
# СТАЛО: Layout('f1', Field('f2', css_class='highlighted'), Field('f3', ...))
```

#### `wrap_together` — обгорнути весь slice разом

```python
# БУЛО: Layout('f1', 'f2', 'f3')
form.helper[0:3].wrap_together(Div, css_class="form-block")
# СТАЛО: Layout(Div('f1', 'f2', 'f3', css_class='form-block'))
```

#### `update_attributes` — оновити атрибути

```python
form.helper[0:3].update_attributes(css_class="my-class")
form.helper['password'].update_attributes(css_class="hero")
```

#### `filter` — пошук за типом

```python
form.helper.filter(str).wrap(Field, css_class="hello")       # всі рядки першого рівня
form.helper.filter(str, max_level=2).wrap(Field, ...)        # два рівні вглиб
form.helper.filter(str, greedy=True).wrap(Div, ...)          # необмежено вглиб
form.helper.filter(str, Div).wrap(Div, css_class="hello")    # кілька типів
```

#### `filter_by_widget` / `exclude_by_widget`

```python
# Потрібно FormHelper(self) — helper з прив'язаною формою
form.helper.filter_by_widget(forms.PasswordInput).wrap(Field, css_class="secure")
form.helper.exclude_by_widget(forms.PasswordInput).wrap(Field, css_class="normal")
```

#### Прямі маніпуляції з Layout

```python
layout = form.helper.layout
layout.append(HTML("<p>Підказка</p>"))             # додати в кінець
layout.insert(1, HTML("<p>На другу позицію</p>"))  # вставити на позицію
layout.pop(2)                                       # видалити третій
layout[0][1] = Field('title', css_class="new")     # замінити елемент
```

---

### Composing Layouts (повторне використання)

```python
# Спільний блок — визначаємо один раз
class UserBlock(Layout):
    def __init__(self):
        super().__init__(
            Fieldset('Дані користувача', 'username', 'email')
        )

# Використовуємо у різних формах
class RegisterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            UserBlock(),                        # ← вбудовуємо
            'phone',
            Submit('submit', 'Зареєструватись'),
        )
```

---

### Перевизначення шаблонів

```python
# Глобально для всіх екземплярів класу
from crispy_forms.layout import Div
Div.template = 'my_div_template.html'

# Для конкретного об'єкту в Layout
Layout(
    Div('field1', template='custom_div.html')
)

# Через FormHelper
self.helper.template = 'my_form.html'
self.helper.field_template = 'my_field.html'
```

---

### Створення власного Template Pack

Мінімальна структура (`templates/chocolate/`):

```
chocolate/               ← назва pack = значення CRISPY_TEMPLATE_PACK
├── whole_uni_form.html  ← ОБОВ'ЯЗКОВО: шаблон форми для {% crispy %}
├── field.html           ← ОБОВ'ЯЗКОВО: шаблон одного поля
├── uni_form.html        ← для |crispy фільтру
└── layout/
    ├── baseinput.html   ← для Submit/Button
    └── div.html         ← для Div
```

```python
# settings.py
CRISPY_TEMPLATE_PACK = 'chocolate'
CRISPY_ALLOWED_TEMPLATE_PACKS = ('bootstrap5', 'chocolate')
```

> **Порада:** копіюй шаблони з `crispy_bootstrap5`, потім адаптуй HTML/CSS під свій framework.
> З версії 1.5.0 template packs ізольовані — шаблони одного pack не можуть посилатись на інший.

---

## Пов'язані файли

| Файл | Що показує |
|------|-----------|
| [DESIGN_FOUNDATIONS.md §14](DESIGN_FOUNDATIONS.md#14-детальна-архітектура-crispy-forms) | Архітектура, конвеєри, before/after порівняння |
| [crispy_notes_project/hello_app/forms.py](crispy_notes_project/hello_app/forms.py) | **Реальний код** — NoteForm, NotebookForm, TagForm з FormHelper + Layout |
| [crispy_notes_project/README.md](crispy_notes_project/README.md) | Покроковий туторіал по crispy з 3-рівневим порівнянням |
