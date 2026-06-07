# SIEM — Системи Управління Подіями Безпеки

> **SIEM** (Security Information and Event Management) — інструмент, який збирає логи з усього вашого серверу, аналізує їх у реальному часі та сповіщає адміністратора про підозрілу активність.
>
> **Аналогія:** Уяви, що у твоєму будинку 100 відеокамер. SIEM — це охоронець, який дивиться всі екрани одночасно та натискає кнопку тривоги, коли помічає щось підозріле.

---

## Що таке SIEM і навіщо він потрібен?

**Системи управління інформацією та подіями безпеки (SIEM)** призначені для:
- **Збору** логів з різних джерел (Django, nginx, PostgreSQL, системні логи)
- **Зберігання** та індексування великих обсягів даних
- **Аналізу та кореляції** — пошук підозрілих патернів
- **Виявлення загроз** у режимі реального часу

**Популярні SIEM-платформи:**
- **Splunk** — найпопулярніший комерційний SIEM
- **ELK Stack (Elasticsearch + Logstash + Kibana)** — безкоштовний open-source
- **IBM QRadar** — корпоративний рівень
- **LogRhythm** — для SOC-команд (Security Operations Center)

---

## Чому просто зберігати логи локально недостатньо?

```
Проблема 1: Атакер зламав сервер → видалив лог-файли → немає доказів
Проблема 2: Лог-файл на 10 ГБ → неможливо читати вручну
Проблема 3: Docker-контейнер перезапустився → всі логи зникли
Проблема 4: Потрібно порівняти логи Django + nginx + PostgreSQL → різні файли

Рішення: SIEM збирає все в одному місці та аналізує автоматично
```

---

## Архітектура передачі логів: Django → SIEM

```
[Django App]
    ↓ (Python logging → SysLogHandler)
[Syslog Daemon (rsyslog)] ← /dev/log socket
    ↓ (stunnel: шифрування SSL/TLS)
[SIEM Server (Splunk/ELK)]
    ↓
[Дашборди + Сповіщення]
```

---

## Крок 1: Налаштування логування Django (`settings.py`)

Замість запису в локальний файл — відправляємо до системного `syslog`:

```python
# settings.py

import logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'security': {
            # Формат: [рівень] [час] [модуль] повідомлення
            'format': '[%(levelname)s] %(asctime)s %(name)s: %(message)s',
        },
    },
    
    'handlers': {
        # Відправка в системний syslog (/dev/log)
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'address': '/dev/log',           # Linux syslog socket
            'facility': 'local7',            # категорія для SIEM-фільтрації
            'formatter': 'security',
        },
        # Додатково — в консоль під час розробки
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'security',
        },
    },
    
    'loggers': {
        # Django вбудований security logger
        'django.security': {
            'handlers': ['syslog', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Наш кастомний security logger
        'security': {
            'handlers': ['syslog', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

## Крок 2: Які події треба логувати?

### 2.1. Невдалі спроби входу (Brute-Force Detection)

```python
# views.py
import logging
security_log = logging.getLogger('security')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            security_log.info(
                f"LOGIN_SUCCESS user_id={user.pk} username={user.username} "
                f"ip={request.META.get('REMOTE_ADDR')}"
            )
        else:
            security_log.warning(
                f"LOGIN_FAILED username={request.POST.get('username', 'unknown')} "
                f"ip={request.META.get('REMOTE_ADDR')}"
            )
```

**Правило в SIEM:** Якщо `LOGIN_FAILED` > 5 разів за 1 хвилину з однієї IP → сповіщення!

### 2.2. Спроби несанкціонованого доступу (IDOR Detection)

```python
from django.core.exceptions import PermissionDenied

@login_required
def note_edit(request, pk):
    try:
        note = Note.objects.get(pk=pk)
    except Note.DoesNotExist:
        raise Http404
    
    # Фіксуємо спробу доступу до чужого ресурсу
    if note.user != request.user:
        security_log.warning(
            f"UNAUTHORIZED_ACCESS user_id={request.user.pk} "
            f"tried to access note_id={pk} owned_by={note.user_id} "
            f"ip={request.META.get('REMOTE_ADDR')}"
        )
        raise PermissionDenied

    # ... решта view
```

### 2.3. Привілейовані дії (Audit Trail)

```python
# Логуємо видалення, зміну прав, групові операції
@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        security_log.info(
            f"NOTE_DELETED user_id={request.user.pk} note_id={pk} "
            f"note_title={note.title[:50]!r}"
        )
        note.delete()
```

---

## Крок 3: Налаштування Syslog Daemon

`rsyslog` — системний демон, що збирає логи від додатків.

```bash
# /etc/rsyslog.conf або /etc/rsyslog.d/django.conf

# Отримати логи від Django (через /dev/log)
local7.*    /var/log/django-security.log

# Пересилати на SIEM-сервер (порт 514 UDP)
local7.*    @log.mycompany.com:514
```

```bash
# Перезапустити rsyslog після змін:
sudo systemctl restart rsyslog
```

---

## Крок 4: Шифрування передачі логів (stunnel)

Без шифрування логи летять через мережу у відкритому вигляді! Атакер всередині мережі може їх перехопити.

**stunnel** — створює SSL/TLS тунель для будь-якого TCP з'єднання:

```bash
# Встановлення:
sudo apt install stunnel4

# /etc/stunnel/siem.conf:
[siem-forward]
client = yes
accept = 127.0.0.1:514    # локальний порт (rsyslog пише сюди)
connect = siem.company.com:6514  # SIEM-сервер (TLS порт)
cert = /etc/ssl/certs/client.pem
```

```
Без stunnel:  Django → rsyslog → [відкрита мережа] → SIEM  ← НЕБЕЗПЕЧНО
З stunnel:    Django → rsyslog → stunnel (SSL) → [зашифровано] → SIEM
```

---

## Крок 5: Правила та Сповіщення в SIEM

Коли логи надходять до SIEM, налаштовуємо автоматичні правила:

| Правило | Умова | Дія |
|---------|-------|-----|
| Brute-Force | LOGIN_FAILED > 5 за 60 сек з однієї IP | Email адміністратору |
| IDOR Attack | UNAUTHORIZED_ACCESS > 3 за 5 хв | Заблокувати IP (через SOAR) |
| Privilege Escalation | GROUP_ADDED для нового admin | Негайне сповіщення |
| After-Hours Access | Вхід між 2:00-6:00 | Підозріла активність |
| Mass Deletion | NOTE_DELETED > 10 за 1 хв | Можливий витік даних |

**SOAR** (Security Orchestration, Automation, and Response) — автоматизована відповідь на інциденти:
```
SIEM виявив brute-force
    ↓
SOAR автоматично:
    1. Блокує IP на рівні nginx
    2. Надсилає SMS адміністратору
    3. Відкриває тікет в Jira
    4. Зберігає IP в blacklist
```

---

## ELK Stack — безкоштовна альтернатива для навчання

**ELK** = **E**lasticsearch + **L**ogstash + **K**ibana

```
Django → rsyslog → Logstash (парсинг) → Elasticsearch (зберігання) → Kibana (дашборди)
```

Kibana дозволяє будувати дашборди:
- Графік спроб входу за часом
- Карта IP-адрес атакерів
- Топ-10 найчастіших помилок авторизації

---

## Де це в нашому проєкті?

У `crispy_notes_project` SIEM поки не підключений. Для навчального проєкту достатньо:

```python
# settings.py — мінімальний security logging:
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}
```

Для production — підключай ELK або Splunk за схемою вище.
