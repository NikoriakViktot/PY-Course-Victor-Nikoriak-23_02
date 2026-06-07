"""
urls.py — Маршрутизатор додатку 'news'.

РОЛЬ У АРХІТЕКТУРІ:
    Цей файл визначає URL-патерни конкретно для додатку новин.
    Головний urls.py (news_portal/urls.py) підключає його через include().

АЛГОРИТМ:
    Django перебирає urlpatterns ЗВЕРХУ ВНИЗ і зупиняється на ПЕРШОМУ збігу.
    Тому статичні маршрути ('', 'category/') мають стояти ВИЩЕ динамічних.

URL-СХЕМА ЦЬОГО ДОДАТКУ:
    GET /                        → ArticleListView  (список всіх новин)
    GET /article/<int:pk>/       → ArticleDetailView (одна стаття)
    GET /category/<slug:slug>/   → CategoryArticleListView (фільтр по категорії)

PATH CONVERTERS:
    <int:pk>   → захоплює ціле число: /article/5/ → pk=5
    <slug:slug>→ захоплює slug (a-z, 0-9, -): /category/ekonomika/ → slug='ekonomika'

АНАЛОГІЯ: Сортувальник пошти — читає адресу і направляє в потрібне місце.
"""

from django.urls import path, re_path
from . import views

# app_name — простір імен додатку.
# Дозволяє використовувати іменовані URL з namespace:
# {% url 'news:article_list' %}  замість  {% url 'article_list' %}
# → уникає конфліктів якщо кілька додатків мають однакові назви маршрутів
app_name = 'news'

urlpatterns = [
    # ── Головна сторінка — список новин ───────────────────────────────────────
    # URL: /
    # path('') → пустий рядок = корінь сайту
    path(
        '',
        views.ArticleListView.as_view(),  # .as_view() перетворює клас CBV у функцію
        name='article_list',             # Іменований маршрут: {% url 'news:article_list' %}
    ),

    # ── Детальна сторінка статті ───────────────────────────────────────────────
    # URL: /article/42/
    # <int:pk> → захоплює число і передає як параметр pk у view
    path(
        'article/<int:pk>/',
        views.ArticleDetailView.as_view(),
        name='article_detail',           # {% url 'news:article_detail' pk=article.pk %}
    ),

    # ── Список статей за категорією ────────────────────────────────────────────
    # URL: /category/ekonomika/
    # <slug:slug> → захоплює slug і передає як параметр slug у view
    re_path(
        r'^category/(?P<slug>[\w-]+)/$',
        views.CategoryArticleListView.as_view(),
        name='category_detail',
    ),
]
