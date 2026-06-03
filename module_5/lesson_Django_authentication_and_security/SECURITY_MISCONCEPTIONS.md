# Типові помилки безпеки — Security Misconceptions

> **Мета:** Розвіяти поширені хибні уявлення про безпеку вебзастосунків.
> Ці помилки роблять НАВІТЬ досвідчені розробники!

---

## Помилка 1: "Я приховав кнопку — значить захистив"

**Що роблять:** Ховають кнопку "Видалити" в шаблоні для юзерів без прав.

```html
<!-- шаблон: ховаємо кнопку — BUT це тільки UX, НЕ безпека! -->
{% if note.user == request.user %}
  <a href="/notes/{{ note.pk }}/delete/">Видалити</a>
{% endif %}
```

**Проблема:** Атакер відкриває інструменти розробника (F12), бачить ID нотатки і надсилає запит напряму:

```bash
# Атакер знає URL: /notes/42/delete/
# Він надсилає POST-запит напряму через curl або Postman:
curl -X POST http://mysite.com/notes/42/delete/ \
     -H "Cookie: sessionid=attacker_session"
# Результат: нотатка Боба видалена!
```

**Правильне рішення — захист у VIEW:**
```python
# views.py:
@login_required
def note_delete(request, pk):
    # Перевірка ЗАВЖДИ у view, не тільки у шаблоні:
    note = get_object_or_404(Note, pk=pk, user=request.user)
    # ↑ Якщо note.user != request.user → Django поверне 404
    if request.method == 'POST':
        note.delete()
        return redirect('note_list')
```

---

## Помилка 2: "Якщо юзер залогінений — він може все"

**Що думають:** `@login_required` захищає від всього.

**Проблема:** `@login_required` перевіряє лише **факт входу**, але НЕ перевіряє **право власності** на конкретний об'єкт.

```python
# НЕБЕЗПЕЧНО — IDOR (Insecure Direct Object Reference):
@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk)   # pk=42 належить Бобу
    # Аліса залогінена → @login_required OK
    # Але Аліса редагує нотатку БОБА!

# БЕЗПЕЧНО — додай user= фільтр:
@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    # pk=42 належить Бобу, user=Alice → 404 ✓
```

**Правило:**
> `@login_required` + `get_object_or_404(Model, pk=pk, user=request.user)` = правильний захист

---

## Помилка 3: "Суперюзер — це нормальний адмін"

**Що роблять:** Тестують весь функціонал від суперюзера.

**Проблема:**
```python
# Суперюзер:
user.has_perm('hello_app.delete_note')  # True — ЗАВЖДИ, навіть без явного права

# Звичайний staff-юзер:
user.has_perm('hello_app.delete_note')  # False — якщо право не призначено

# Якщо ти тестуєш від superuser і бачиш що все ОК →
# НЕ ФАКТ, що звичайний юзер теж матиме доступ!
```

**Правило:**
> Тестуй кожну роль з **правильним типом акаунту**: звичайний юзер, staff, superuser — окремо.

---

## Помилка 4: "Глобальний queryset — це нормально"

**Що роблять:** `Note.objects.get(id=note_id)` без фільтру по юзеру.

```python
# НЕБЕЗПЕЧНО — Аліса може отримати будь-яку нотатку:
note = Note.objects.get(id=note_id)

# Атакер перебирає ID: /notes/1/, /notes/2/, /notes/3/...
# → знаходить конфіденційні нотатки інших юзерів!

# БЕЗПЕЧНО:
note = get_object_or_404(Note, id=note_id, user=request.user)
# або
note = Note.objects.get(id=note_id, user=request.user)
```

---

## Помилка 5: "Client-side валідація захищає"

**Що роблять:** Перевіряють дані тільки в HTML-формі або JavaScript.

```html
<!-- HTML форма: -->
<input type="number" name="priority" min="1" max="4">
<!-- Атакер відкриває F12 → змінює min/max → надсилає priority=999 -->
```

**Правило:**
> Клієнтська валідація — тільки для UX (зручність).
> **Серверна валідація** — обов'язкова для безпеки.

```python
# Django ModelForm — server-side валідація:
class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'priority']
    
    def clean_priority(self):
        priority = self.cleaned_data['priority']
        if priority not in [1, 2, 3, 4]:
            raise forms.ValidationError("Невірний пріоритет")
        return priority
```

---

## Помилка 6: "DEBUG=True в production — тимчасово"

**Що роблять:** Залишають `DEBUG=True` на сервері "поки не знайдуть баг".

**Що отримує атакер від DEBUG=True:**
```
- Повний стектрейс помилки (назви файлів, рядки коду)
- Значення всіх локальних змінних у момент помилки
- SECRET_KEY (витік = повний злам сесій!)
- Всі SQL-запити зберігаються у пам'яті → memory leak!
```

**Правило:**
> `DEBUG = False` **завжди** в production. Без виключень.
> Для відлагодження в production — використовуй логи (`logging`).

---

## Підсумок: Чек-ліст безпеки View

Перед кожним новим view перевіряй:

```python
@login_required                                    # ✓ чи залогінений?
def my_view(request, pk):
    obj = get_object_or_404(Model, pk=pk,          # ✓ чи є право на цей об'єкт?
                             user=request.user)
    
    if request.method == 'POST':
        form = MyForm(request.POST)                # ✓ форма з POST-даними
        if form.is_valid():                        # ✓ серверна валідація
            # ... логіка
    
    # Шаблон: ховай кнопки для UX, але захист у view ✓
    return render(request, 'template.html', {'obj': obj})
```
