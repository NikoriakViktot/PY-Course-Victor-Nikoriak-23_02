"""
urls.py — Головний маршрутизатор (Root URLconf) проєкту.

РОЛЬ У АРХІТЕКТУРІ:
    Це перший файл маршрутів який Django читає при кожному запиті.
    Він не обробляє самі запити — лише перенаправляє їх до потрібного додатку.

ЯК ЦЕ ПРАЦЮЄ:
    1. Django отримує запит: GET /news/5/
    2. Читає ROOT_URLCONF = 'news_portal.urls' з settings.py
    3. Перебирає urlpatterns зверху вниз
    4. Знаходить перший збіг → передає запит далі
    5. include('news.urls') → Django читає urls.py додатку 'news'

АНАЛОГІЯ: Ресепшн готелю — не обслуговує гостей сам,
          а направляє їх у відповідний відділ.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # ── Адмін-панель ──────────────────────────────────────────────────────────
    # URL: /admin/
    # Django автоматично генерує CRUD інтерфейс для всіх зареєстрованих моделей
    path('admin/', admin.site.urls),

    # ── Додаток новин ──────────────────────────────────────────────────────────
    # URL: / (корінь сайту)
    # include('news.urls') → Django читає news/urls.py і додає ті маршрути
    # Приклад: path('') в news/urls.py → фінальний URL = /
    #          path('<int:pk>/') в news/urls.py → фінальний URL = /5/
    path('', include('news.urls')),
]
