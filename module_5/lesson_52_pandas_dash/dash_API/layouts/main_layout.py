# =============================================================================
# layouts/main_layout.py — Головний лейаут дашборду
# =============================================================================
# Цей файл відповідає за загальну структуру сторінки:
#   [Сайдбар] | [Заголовок + Вкладки + Контент вкладки]
#
# Дані для параметрів сайдбару завантажуються ТІЛЬКИ ОДИН РАЗ при запуску
# через registry (lru_cache). Це не призводить до повторного читання CSV.
# =============================================================================

from dash import html, dcc
from data_utils import get_dataset, get_units_for_commodity, get_debt_indicators
from layouts.sidebar import create_sidebar
from layouts.tabs import create_tabs


def create_layout() -> html.Div:
    """
    Будує та повертає повний лейаут застосунку Dash.

    Структура:
        ┌──────────────┬──────────────────────────────────────────────┐
        │  Сайдбар     │  Заголовок дашборду                          │
        │  (фільтри)   │  ────────────────────────────────────────    │
        │              │  Вкладки: Огляд | Ціни | Карта | ...         │
        │              │  ────────────────────────────────────────    │
        │              │  Контент активної вкладки (рендериться       │
        │              │  динамічно callback'ом у tabs_callbacks.py)  │
        └──────────────┴──────────────────────────────────────────────┘

    Примітка: все, що знаходиться в html.Div id="tab-content", рендериться
    динамічно. Тому в цьому файлі ми не будуємо графіків — тільки структуру.
    """

    # ── Завантажуємо дані для побудови фільтрів сайдбару ─────────────────────
    # Використовуємо get_dataset() — дані кешуються lru_cache, тому
    # наступні виклики (у callbacks) не будуть перечитувати CSV.

    food_df    = get_dataset("food")
    debt_df    = get_dataset("debt")

    # Список товарів — відсортований алфавітно для зручного вибору
    commodities = sorted(food_df["товар"].dropna().unique().tolist())

    # Стандартний товар за замовчуванням
    default_commodity = "Sugar"  # Цукор — присутній у всіх регіонах і датах

    # Одиниці виміру для товару за замовчуванням
    default_units = get_units_for_commodity(food_df, default_commodity)
    default_unit  = default_units[0] if default_units else "KG"

    # Список областей — виключаємо NaN (National Average не має області)
    oblasts = sorted(food_df["область"].dropna().unique().tolist())

    # Діапазон дат
    date_min = food_df["дата"].min()
    date_max = food_df["дата"].max()

    # Список макроіндикаторів для сайдбару
    debt_indicators = get_debt_indicators(debt_df)

    # Дефолтний індикатор — рахунок поточних операцій (BoP)
    # Це один з найбільш інформативних індикаторів платіжного балансу
    default_debt = next(
        (i for i in debt_indicators if "Current account balance" in i),
        debt_indicators[0] if debt_indicators else ""
    )

    # ── Будуємо лейаут ────────────────────────────────────────────────────────

    return html.Div(
        className="main",
        children=[

            # ── Бічна панель з фільтрами ──────────────────────────────────
            create_sidebar(
                commodities=commodities,
                oblasts=oblasts,
                default_commodity=default_commodity,
                default_unit=default_unit,
                default_oblast="Всі",
                debt_indicators=debt_indicators,
                default_debt_indicator=default_debt,
                date_min=date_min,
                date_max=date_max,
            ),

            # ── Основний контент ──────────────────────────────────────────
            html.Div(
                className="content",
                children=[

                    # Заголовок дашборду
                    html.H1(
                        "📊 Аналіз товарних цін в Україні",
                        style={
                            "marginTop": "0",
                            "marginBottom": "8px",
                            "fontSize": "24px",
                        },
                    ),

                    # Підзаголовок з поясненням
                    html.P(
                        "Дашборд для наукового аналізу динаміки цін, "
                        "регіональних відмінностей та макроекономічного контексту. "
                        "Джерела: WFP, FAO, Світовий банк.",
                        style={
                            "color": "#8b949e",
                            "fontSize": "13px",
                            "marginBottom": "20px",
                        },
                    ),

                    # Вкладки навігації
                    create_tabs(),

                    # Контейнер для контенту активної вкладки
                    # Заповнюється callback'ом render_tab у tabs_callbacks.py
                    html.Div(
                        id="tab-content",
                        style={"paddingTop": "20px"},
                    ),

                ],
            ),
        ],
    )
