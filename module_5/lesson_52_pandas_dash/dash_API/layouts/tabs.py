# =============================================================================
# layouts/tabs.py — Визначення вкладок дашборду
# =============================================================================
# Кожна вкладка відповідає окремому аналітичному питанню.
# Дані та callbacks підключаються лише для активної вкладки.
# =============================================================================

from dash import dcc


def create_tabs() -> dcc.Tabs:
    """
    Створює компонент вкладок із 7 аналітичними розділами.

    Структура вкладок:
        overview    — Огляд даних (статистика, структура)
        food        — Ціни на товари (часові ряди, регіони)
        spatial     — Просторовий аналіз (карти ринків)
        exchange    — Валютний курс UAH/USD
        debt        — Зовнішній борг та макроіндикатори
        correlation — Зв'язок цін і валютного курсу
        methodology — Методологія та пояснення
    """
    return dcc.Tabs(
        id="tabs",
        value="overview",            # вкладка за замовчуванням при відкритті
        persistence=True,            # зберігає активну вкладку при перезавантаженні
        persistence_type="session",
        children=[
            dcc.Tab(
                label="📋 Огляд даних",
                value="overview",
                className="tab-item",
                selected_className="tab-item--selected",
            ),
            dcc.Tab(
                label="🍞 Ціни на товари",
                value="food",
                className="tab-item",
                selected_className="tab-item--selected",
            ),
            dcc.Tab(
                label="🗺️ Просторовий аналіз",
                value="spatial",
                className="tab-item",
                selected_className="tab-item--selected",
            ),
            dcc.Tab(
                label="💱 Валютний курс",
                value="exchange",
                className="tab-item",
                selected_className="tab-item--selected",
            ),
            dcc.Tab(
                label="📉 Зовнішній борг",
                value="debt",
                className="tab-item",
                selected_className="tab-item--selected",
            ),
            dcc.Tab(
                label="🔗 Ціни та курс валюти",
                value="correlation",
                className="tab-item",
                selected_className="tab-item--selected",
            ),
            dcc.Tab(
                label="📖 Методологія",
                value="methodology",
                className="tab-item",
                selected_className="tab-item--selected",
            ),
        ],
    )
