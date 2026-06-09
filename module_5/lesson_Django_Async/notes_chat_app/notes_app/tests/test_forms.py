"""
════════════════════════════════════════════════════════════════════════════════
test_forms.py — Unit тести для forms.py

Запуск:
    python manage.py test notes_app.tests.test_forms -v 2
════════════════════════════════════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
НАВІЩО ТЕСТУВАТИ ФОРМИ?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Форма в Django — це не просто HTML. Це:
  • Рівень валідації вхідних даних (перший захист від сміттю)
  • Нормалізація даних (clean_name: 'Python' → 'python')
  • Security бар'єр (queryset filtering: Alice не бачить дані Bob'а)

Форми тестують БЕЗ HTTP-запиту:
    form = TagForm(data={'name': 'Python', 'color': '#ff0000'})
    form.is_valid()   ← повертає True/False
    form.cleaned_data ← нормалізовані дані після валідації
    form.errors       ← словник помилок {field_name: [errors]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ТРИ КАТЕГОРІЇ ТЕСТІВ ДЛЯ ФОРМ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. ВАЛІДАЦІЯ: форма приймає валідні дані та відхиляє невалідні
     → test_valid_form, test_empty_name_is_invalid, test_invalid_priority

  2. НОРМАЛІЗАЦІЯ: clean_* методи перетворюють дані на стандартний формат
     → test_clean_name_lowercases, test_clean_name_strips_whitespace

  3. SECURITY FILTERING: queryset'и відфільтровані по user
     → test_notebook_queryset_excludes_other_user_notebooks
     → test_tag_queryset_excludes_other_user_tags

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЯК ВИГЛЯДАЄ АТАКА БЕЗ QUERYSET FILTERING?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Без фільтрації:
    NoteForm(user=alice).fields['notebook'].queryset = Notebook.objects.all()
    → Alice бачить у dropdown і власні, і чужі записники!
    → Вибирає Bob's Private Notebook → нотатка Alice зберігається у Bob's notebook
    → Bob бачить нотатки Alice у своєму записнику. DATA LEAK!

  З фільтрацією (наш код):
    NoteForm(user=alice).fields['notebook'].queryset = Notebook.objects.filter(user=alice)
    → Alice бачить тільки свої записники — SAFE ✓
"""

from django.contrib.auth.models import Group, User
from django.test import TestCase

from notes_app.forms import GroupCreateForm, NoteForm, TagForm
from notes_app.models import Notebook, Tag


# ─────────────────────────────────────────────────────────────────────────────
# Базовий клас
# ─────────────────────────────────────────────────────────────────────────────

class BaseFormTest(TestCase):
    """
    Базовий клас для всіх тестів форм.
    Два користувачі потрібні для тестування security filtering:
    перевіряємо що форма alice НЕ бачить дані bob'а.
    """

    def setUp(self):
        self.alice = User.objects.create_user('alice', password='pass123')
        self.bob = User.objects.create_user('bob', password='pass123')


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ: TagForm — clean_name() нормалізація
# ═════════════════════════════════════════════════════════════════════════════

class TagFormTest(BaseFormTest):
    """
    TagForm.clean_name() нормалізує назву тегу: lowercase + strip.

    КОД у forms.py:
        def clean_name(self):
            name = self.cleaned_data['name']
            normalized = name.lower().strip()
            if not normalized:
                raise forms.ValidationError("Назва тегу не може бути порожньою.")
            return normalized
    """

    def test_clean_name_lowercases(self):
        """
        ЩО ПЕРЕВІРЯЄМО: 'Python' перетворюється на 'python' після валідації.

        НАВІЩО: без нормалізації 'Python' і 'python' були б РІЗНИМИ тегами.
        Юзер міг би створити:
          'python', 'Python', 'PYTHON' — три різні теги з однаковим змістом.
        Це засмічує список тегів і ламає unique_together constraint.

        ЯК ПЕРЕВІРИТИ ОЧИЩЕНІ ДАНІ:
            form.is_valid() → True  (спочатку перевіряємо що форма валідна)
            form.cleaned_data['name'] → 'python'  (потім беремо нормалізоване)

        cleaned_data доступний ТІЛЬКИ після успішного is_valid().
        """
        form = TagForm(data={'name': 'Python', 'color': '#ff0000'})
        self.assertTrue(form.is_valid())  # спочатку переконуємось що форма валідна
        self.assertEqual(form.cleaned_data['name'], 'python')  # потім перевіряємо нормалізацію

    def test_clean_name_strips_whitespace(self):
        """
        ЩО ПЕРЕВІРЯЄМО: '  work  ' (пробіли по краях) → 'work'.

        НАВІЩО: якщо юзер вставить назву тегу з копіювання і лишить пробіли —
        без .strip() збережеться '  work  '. Потім:
          • Tag.objects.get(name='work') — НЕ знайде (бо там '  work  ')
          • unique_together з 'work' і '  work  ' — два різні теги
          • Пошук по тегах не спрацює коректно

        ПРОБІЛИ — часта пастка при обробці user input.
        """
        form = TagForm(data={'name': '  work  ', 'color': '#ff0000'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'work')

    def test_clean_name_lowercases_and_strips(self):
        """
        ЩО ПЕРЕВІРЯЄМО: '  Django  ' → 'django' (обидві нормалізації разом).

        НАВІЩО: комбінований тест. Перші два тести перевірили їх окремо,
        цей — разом. Якщо операції виконуються в неправильному порядку
        (спочатку strip потім lower — ok, але lower потім strip — теж ok),
        або якщо одна з операцій відсутня — цей тест це виявить.
        """
        form = TagForm(data={'name': '  Django  ', 'color': '#ff0000'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'django')

    def test_clean_name_empty_after_strip_is_invalid(self):
        """
        ЩО ПЕРЕВІРЯЄМО: '   ' (тільки пробіли) → після strip = '' → ValidationError.

        НАВІЩО: без явної перевірки на порожній рядок після strip:
          '   '.lower().strip() == ''
          Tag.objects.create(name='') → тег з порожньою назвою у БД.
          Це некоректні дані що відображаються у UI як '#' (порожній тег).

        КОД у clean_name():
            if not normalized:
                raise forms.ValidationError(...)

        ПЕРЕВІРЯЄМО form.errors['name']: переконуємось що помилка
        знаходиться саме у полі name, а не загальна помилка форми.
        """
        form = TagForm(data={'name': '   ', 'color': '#ff0000'})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)  # помилка саме у полі name

    def test_valid_tag_form(self):
        """
        ЩО ПЕРЕВІРЯЄМО: коректні дані (нормальна назва + колір) → форма валідна.

        НАВІЩО: після тестів що перевіряють відхилення некоректних даних,
        треба переконатись що ПРАВИЛЬНІ дані не відхиляються "зайвим" кодом.
        "Overcautious validation" — коли валідація відхиляє занадто багато.
        """
        form = TagForm(data={'name': 'python', 'color': '#3776ab'})
        self.assertTrue(form.is_valid())

    def test_empty_name_is_invalid(self):
        """
        ЩО ПЕРЕВІРЯЄМО: порожня назва '' відхиляється.

        НАВІЩО: поле name в моделі required=True (за замовчуванням).
        Django автоматично відхиляє порожній рядок для required полів.
        Але ми ЯВНО тестуємо це бо clean_name() додає додаткову логіку.
        Хочемо впевнитись що стандартна required валідація не "зламана".
        """
        form = TagForm(data={'name': '', 'color': '#ff0000'})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ: NoteForm — Security queryset filtering
# ═════════════════════════════════════════════════════════════════════════════

class NoteFormSecurityTest(BaseFormTest):
    """
    Це найважливіший security тест у всьому проєкті.

    NoteForm(user=alice) має показувати у dropdown полях ТІЛЬКИ:
      • Записники Alice (не Bob'а)
      • Теги Alice (не Bob'а)
      • Групи де Alice є членом (не групи тільки Bob'а)

    КОД у forms.py (захист):
        def __init__(self, *args, user=None, **kwargs):
            ...
            if user is not None:
                self.fields['notebook'].queryset = Notebook.objects.filter(user=user)
                self.fields['tags'].queryset = Tag.objects.filter(user=user)
                self.fields['group'].queryset = user.groups.all()
            else:
                # безпечний fallback — порожні queryset
                self.fields['notebook'].queryset = Notebook.objects.none()
    """

    def setUp(self):
        super().setUp()
        # Кожен юзер має свій записник
        self.alice_notebook = Notebook.objects.create(
            user=self.alice, title="Alice's Notebook"
        )
        self.bob_notebook = Notebook.objects.create(
            user=self.bob, title="Bob's Notebook"
        )

    def test_notebook_queryset_contains_user_notebooks(self):
        """
        ЩО ПЕРЕВІРЯЄМО: NoteForm(user=alice) показує записники ALICE у dropdown.

        НАВІЩО: базова перевірка що фільтрація взагалі працює.
        Якщо queryset порожній через зайву фільтрацію — Alice не зможе
        вибрати записник навіть для своїх нотаток.
        """
        form = NoteForm(user=self.alice)
        queryset = form.fields['notebook'].queryset

        self.assertIn(self.alice_notebook, queryset)

    def test_notebook_queryset_excludes_other_user_notebooks(self):
        """
        ЩО ПЕРЕВІРЯЄМО: NoteForm(user=alice) НЕ показує записники BOB'А.

        НАВІЩО: це ГОЛОВНИЙ security тест цього класу.

        Атака без фільтрації (IDOR через форму):
          1. Зловмисник Alice відкриває /notes/new/
          2. У developer tools бачить id записника Bob'а у HTML
          3. Надсилає POST з notebook=bob_notebook_id
          4. Нотатка зберігається у ЧУЖОМУ записнику
          5. Bob бачить нотатку Alice у своєму записнику → DATA LEAK

        З фільтрацією:
          notebook.queryset = Notebook.objects.filter(user=alice)
          → bob_notebook не в queryset → форма відхилить bob's notebook id
          → Навіть якщо зловмисник надішле боб'ський id — форма каже "invalid choice"

        assertNotIn — ключовий assert: записник Bob'а НЕ ПОВИНЕН бути у queryset.
        """
        form = NoteForm(user=self.alice)
        queryset = form.fields['notebook'].queryset

        self.assertNotIn(self.bob_notebook, queryset)

    def test_tag_queryset_contains_user_tags(self):
        """
        ЩО ПЕРЕВІРЯЄМО: NoteForm(user=alice) показує ТЕГИ ALICE у полі tags.

        НАВІЩО: теги теж фільтруються per-user. Якщо фільтрацію прибрати —
        в select box Alice з'являться теги 'bob-secret', 'private-finance' і тп.
        Це data leak: Alice дізнається назви тегів Bob'а.
        """
        alice_tag = Tag.objects.create(user=self.alice, name='work')
        form = NoteForm(user=self.alice)

        self.assertIn(alice_tag, form.fields['tags'].queryset)

    def test_tag_queryset_excludes_other_user_tags(self):
        """
        ЩО ПЕРЕВІРЯЄМО: NoteForm(user=alice) НЕ показує ТЕГИ BOB'А.

        НАВІЩО: без фільтрації Alice могла б призначити нотатці тег Bob'а.
        Це може виглядати нешкідливо, але:
          1. Тег з'являється у "мої теги" у Bob'а як "використовується"
          2. Bob при видаленні тегу видаляє і "нотатки Alice" з ним → data corruption
          3. Статистика тегів (кількість нотаток) некоректна
        """
        bob_tag = Tag.objects.create(user=self.bob, name='bob-work')
        form = NoteForm(user=self.alice)

        self.assertNotIn(bob_tag, form.fields['tags'].queryset)

    def test_form_without_user_has_empty_querysets(self):
        """
        ЩО ПЕРЕВІРЯЄМО: NoteForm() без user= → ПОРОЖНІ queryset'и для всіх полів.

        НАВІЩО: це перевірка "безпечного дефолту" (fail-safe design).
        Якщо через баг у view форму створять без user=:
            form = NoteForm(data=request.POST)  ← забули user=request.user

        З безпечним дефолтом → queryset.none() → форма не покаже НІЧОГО.
        Краще показати порожній dropdown ніж показати ВСІ записники/теги всіх юзерів.

        КОД у forms.py:
            else:
                self.fields['notebook'].queryset = Notebook.objects.none()
                self.fields['tags'].queryset = Tag.objects.none()

        .exists() → False: перевіряємо що queryset справді порожній.
        """
        form = NoteForm()  # user не переданий

        self.assertFalse(form.fields['notebook'].queryset.exists())
        self.assertFalse(form.fields['tags'].queryset.exists())

    def test_group_queryset_contains_user_groups(self):
        """
        ЩО ПЕРЕВІРЯЄМО: NoteForm(user=alice) показує ГРУПИ де alice є членом.

        НАВІЩО: група для шерінгу нотаток. Якщо user.groups.all() не
        фільтрується правильно — Alice не зможе вибрати свою групу,
        або побачить чужі групи.

        Зверни увагу: групи фільтруються через user.groups.all() —
        тобто тільки ті групи де user є ЧЛЕНОМ, а не всі групи у системі.
        """
        group = Group.objects.create(name='Family')
        self.alice.groups.add(group)  # Alice є членом групи

        form = NoteForm(user=self.alice)

        self.assertIn(group, form.fields['group'].queryset)

    def test_group_queryset_excludes_groups_user_not_in(self):
        """
        ЩО ПЕРЕВІРЯЄМО: NoteForm(user=alice) НЕ показує групи де alice НЕ є членом.

        НАВІЩО: Group — це групи доступу. Alice не є членом "Bob's Work Team".
        Якщо вона побачить цю групу у dropdown і вибере її — її нотатка
        стане видимою для всієї команди Bob'а. PRIVACY VIOLATION.

        СЦЕНАРІЙ АТАКИ (без фільтрації):
          1. Alice бачить 'Bob's Work Team' у dropdown
          2. Вибирає її при створенні нотатки
          3. Всі члени Bob's Work Team бачать нотатку Alice
          4. Alice думала що нотатка особиста

        КЛЮЧОВИЙ РЯДОК у forms.py:
            self.fields['group'].queryset = user.groups.all()
            # user.groups.all() → тільки групи де user є членом
            # Group.objects.all() → ВСІ групи (небезпечно!)
        """
        group = Group.objects.create(name='Bob Only Group')
        self.bob.groups.add(group)  # тільки Bob є членом

        form = NoteForm(user=self.alice)

        # Alice не є членом цієї групи — вона не повинна бачити її
        self.assertNotIn(group, form.fields['group'].queryset)


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ: NoteForm — Валідація полів
# ═════════════════════════════════════════════════════════════════════════════

class NoteFormValidationTest(BaseFormTest):
    """
    Перевіряємо що форма правильно валідує дані перед збереженням.
    Форма — перший рубіж захисту від некоректних даних.
    """

    def test_valid_note_form(self):
        """
        ЩО ПЕРЕВІРЯЄМО: мінімально коректна форма (title + priority) → валідна.

        НАВІЩО: smoke test. Якщо навіть базова валідна форма не проходить —
        щось фундаментально зламано у формі (required поля, неправильні defaults).

        msg=form.errors: якщо тест провалиться — побачимо ЧОМУ форма невалідна.
        Це зручна підказка при дебагу без додаткового print().
        """
        form = NoteForm(
            data={'title': 'My Note', 'priority': 1},
            user=self.alice,
        )
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_empty_title_is_invalid(self):
        """
        ЩО ПЕРЕВІРЯЄМО: порожній title → форма невалідна, помилка у полі title.

        НАВІЩО: title — обов'язкове поле (required=True). Нотатка без заголовку
        не має сенсу. Якщо empty title проходить — у БД збережеться Note(title='')
        і воно буде відображатись у списку як порожній рядок.
        """
        form = NoteForm(
            data={'title': '', 'priority': 1},
            user=self.alice,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)  # помилка саме у полі title

    def test_title_missing_is_invalid(self):
        """
        ЩО ПЕРЕВІРЯЄМО: відсутній title (поле взагалі не передане) → невалідно.

        НАВІЩО: відрізняється від порожнього title. Може статись якщо:
          • Хтось надсилає API запит без поля title
          • JavaScript видаляє поле перед відправкою

        Django обробляє обидва випадки однаково (required field missing),
        але тест явно документує цю поведінку.
        """
        form = NoteForm(
            data={'priority': 1},  # title відсутній
            user=self.alice,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_priority_choices_are_valid(self):
        """
        ЩО ПЕРЕВІРЯЄМО: всі чотири допустимих значення priority (1, 2, 3, 4) → валідні.

        НАВІЩО: у форми є поле priority з choices. Django перевіряє що
        value ∈ choices. Якщо PRIORITY_CHOICES у моделі зміниться (наприклад
        прибрати priority=3), цей тест виявить що 3 стало невалідним у формі.

        msg=f"priority={priority}: {form.errors}": якщо тест провалиться
        для якогось конкретного пріоритету — повідомлення покаже якого саме.
        """
        for priority in [1, 2, 3, 4]:
            form = NoteForm(
                data={'title': 'Test', 'priority': priority},
                user=self.alice,
            )
            self.assertTrue(
                form.is_valid(),
                msg=f"priority={priority} має бути валідним, але форма відхилила: {form.errors}"
            )

    def test_invalid_priority_is_rejected(self):
        """
        ЩО ПЕРЕВІРЯЄМО: priority=99 відхиляється формою.

        НАВІЩО: форма має обмежені choices [1, 2, 3, 4]. Value 99 не є у
        choices → Django відхиляє з "Select a valid choice. 99 is not..."

        РЕАЛЬНИЙ СЦЕНАРІЙ: зловмисник надсилає POST з priority=99 намагаючись
        обійти форму. Без цієї перевірки у choices — value 99 потрапить у БД.
        """
        form = NoteForm(
            data={'title': 'Test', 'priority': 99},
            user=self.alice,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('priority', form.errors)


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТИ: GroupCreateForm — clean_name() унікальність
# ═════════════════════════════════════════════════════════════════════════════

class GroupCreateFormTest(BaseFormTest):
    """
    GroupCreateForm перевіряє що назва групи унікальна ПЕРЕД збереженням.

    Чому перевірка у формі, а не тільки у БД?
      • Group.name має unique=True у Django → дублікат дасть IntegrityError у БД
      • Але IntegrityError — це 500 Server Error, а не красива форма з помилкою
      • clean_name() перехоплює дублікат ДО збереження → показує ValidationError
        з зрозумілим повідомленням у формі

    КОД у forms.py:
        def clean_name(self):
            name = self.cleaned_data['name'].strip()
            if Group.objects.filter(name=name).exists():
                raise forms.ValidationError(f'Група з назвою «{name}» вже існує.')
            return name
    """

    def test_valid_new_group_name(self):
        """
        ЩО ПЕРЕВІРЯЄМО: нова унікальна назва групи → форма валідна.

        НАВІЩО: базовий happy path. Якщо навіть нова назва відхиляється —
        щось фундаментально зламано у clean_name().
        """
        form = GroupCreateForm(data={'name': 'Family'})
        self.assertTrue(form.is_valid())

    def test_clean_name_strips_whitespace(self):
        """
        ЩО ПЕРЕВІРЯЄМО: '  Family  ' → 'Family' (strip, але не lowercase).

        НАВІЩО: назви груп залишають регістр ('Family', 'Work Team').
        Але зайві пробіли треба прибрати.

        ВАЖЛИВА РІЗНИЦЯ від TagForm:
          TagForm.clean_name: lowercase + strip ('Python' → 'python')
          GroupCreateForm.clean_name: тільки strip ('Family' → 'Family', не 'family')
        Групи мають "красиві" назви з великої літери, теги — маленькими.
        """
        form = GroupCreateForm(data={'name': '  Family  '})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Family')  # тільки strip, не lowercase

    def test_existing_group_name_raises_validation_error(self):
        """
        ЩО ПЕРЕВІРЯЄМО: спроба створити групу з назвою що вже існує →
        форма невалідна, помилка у полі name, помилка містить назву групи.

        НАВІЩО: без цієї перевірки:
          1. Дві групи з назвою 'Family' у БД (якщо unique не увімкнено)
          2. Або IntegrityError 500 (якщо unique увімкнено)

        У ОБОХ ВИПАДКАХ — поганий UX. Наша форма показує чітке повідомлення:
        "Група з назвою «Existing Group» вже існує."

        ТЕСТУЄМО ТРИ РЕЧІ:
          1. form.is_valid() == False — форма відхилена
          2. 'name' in form.errors — помилка у правильному полі
          3. 'Existing Group' in str(errors['name']) — помилка містить назву групи
             (щоб юзер розумів ЩО конкретно є дублікатом)
        """
        # Arrange — група вже існує в БД
        Group.objects.create(name='Existing Group')

        # Act — намагаємось створити групу з тією ж назвою
        form = GroupCreateForm(data={'name': 'Existing Group'})

        # Assert
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('Existing Group', str(form.errors['name']))

    def test_empty_name_is_invalid(self):
        """
        ЩО ПЕРЕВІРЯЄМО: порожня назва групи '' → форма невалідна.

        НАВІЩО: Group з name='' — некоректний стан. У UI виглядатиме як
        безіменна група. Пошук по name не знайде її. Django Admin покаже '' у списку.

        СТАНДАРТНА ВАЛІДАЦІЯ: CharField з required=True відхиляє '' без будь-якого
        clean_name(). Але ми тестуємо це явно щоб документувати поведінку.
        """
        form = GroupCreateForm(data={'name': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
