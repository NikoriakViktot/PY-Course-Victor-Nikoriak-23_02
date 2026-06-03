# =============================================================================
# layouts/sidebar.py — Бічна панель з фільтрами
# =============================================================================
# Сайдбар містить ВСІ фільтри проєкту.
# Вони завжди присутні в DOM (Document Object Model), тому callbacks
# можуть безпечно посилатися на їхні ID без помилок "Component not found".
#
# Які фільтри використовує яка вкладка:
#   food        → commodity-filter, unit-filter, oblast-filter, date-range
#   spatial     → commodity-filter, unit-filter
#   correlation → commodity-filter, unit-filter, oblast-filter, date-range
#   exchange    → (не використовує — показує весь ряд)
#   debt        → debt-indicator-filter
#   overview    → (не використовує)
#   methodology → (не використовує)
#
# Для наочності кожна секція підписана.
# =============================================================================

from dash import html, dcc
import pandas as pd


def create_sidebar(
    commodities: list[str],
    oblasts: list[str],
    default_commodity: str,
    default_unit: str,
    default_oblast: str,
    debt_indicators: list[str],
    default_debt_indicator: str,
    date_min: pd.Timestamp,
    date_max: pd.Timestamp,
) -> html.Div:
    """
    Будує бічну панель з фільтрами дашборду.

    Параметри приймаються явно (не зчитуються з глобального стану),
    що робить функцію чистою та легко тестованою.

    Повертає html.Div з усіма фільтрами.
    """

    return html.Div(
        className="sidebar",
        children=[

            # ── Заголовок бічної панелі ───────────────────────────────────
            html.H2("Фільтри", style={"marginTop": "0", "marginBottom": "20px"}),

            # ─────────────────────────────────────────────────────────────
            # СЕКЦІЯ: Аналіз продуктових цін
            # Використовується: вкладки "Ціни", "Просторовий", "Кореляція"
            # ─────────────────────────────────────────────────────────────
            html.Div(
                className="sidebar-section",
                children=[
                    html.H4("Продуктові ціни", className="sidebar-section-title"),

                    # Вибір товару
                    html.Label("Товар:", className="filter-label"),
                    dcc.Dropdown(
                        id="commodity-filter",
                        options=[{"label": c, "value": c} for c in commodities],
                        value=default_commodity,
                        clearable=False,
                        className="dropdown-dark",
                    ),

                    html.Br(),

                    # Вибір одиниці виміру — динамічно оновлюється
                    # callback'ом залежно від обраного товару
                    html.Label("Одиниця виміру:", className="filter-label"),
                    dcc.Dropdown(
                        id="unit-filter",
                        options=[{"label": default_unit, "value": default_unit}],
                        value=default_unit,
                        clearable=False,
                        className="dropdown-dark",
                    ),

                    html.Br(),

                    # Вибір області (регіону)
                    # "Всі" = агрегація по всій країні
                    html.Label("Область:", className="filter-label"),
                    dcc.Dropdown(
                        id="oblast-filter",
                        options=[{"label": "Всі області", "value": "Всі"}]
                               + [{"label": o, "value": o} for o in oblasts],
                        value=default_oblast,
                        clearable=False,
                        className="dropdown-dark",
                    ),

                    html.Br(),

                    # Діапазон дат
                    html.Label("Діапазон дат:", className="filter-label"),
                    dcc.DatePickerRange(
                        id="date-range",
                        min_date_allowed=date_min.date(),
                        max_date_allowed=date_max.date(),
                        start_date=date_min.date(),
                        end_date=date_max.date(),
                        display_format="DD.MM.YYYY",
                        className="date-picker-dark",
                        style={"width": "100%"},
                    ),
                ],
            ),

            html.Hr(style={"borderColor": "#30363d", "margin": "20px 0"}),

            # ─────────────────────────────────────────────────────────────
            # СЕКЦІЯ: Макроекономічні індикатори
            # Використовується: вкладка "Зовнішній борг"
            # ─────────────────────────────────────────────────────────────
            html.Div(
                className="sidebar-section",
                children=[
                    html.H4("Макроіндикатори", className="sidebar-section-title"),

                    html.Label("Індикатор:", className="filter-label"),
                    dcc.Dropdown(
                        id="debt-indicator-filter",
                        options=[
                            {"label": ind[:60] + ("..." if len(ind) > 60 else ""),
                             "value": ind}
                            for ind in debt_indicators
                        ],
                        value=default_debt_indicator,
                        clearable=False,
                        className="dropdown-dark",
                        # Підказка — повна назва при наведенні реалізована через tooltip
                    ),
                    # Пояснення, що кожен індикатор — окрема концепція
                    html.P(
                        "⚠️ Кожен індикатор вимірює окремий макроекономічний показник "
                        "та не підлягає порівнянню з іншими.",
                        style={"fontSize": "11px", "color": "#8b949e", "marginTop": "8px"},
                    ),
                ],
            ),

            html.Hr(style={"borderColor": "#30363d", "margin": "20px 0"}),

            # ─────────────────────────────────────────────────────────────
            # Інформаційна секція
            # ─────────────────────────────────────────────────────────────
            html.Div(
                className="sidebar-section",
                children=[
                    html.P(
                        "Джерела даних:",
                        style={"fontWeight": "bold", "fontSize": "12px", "marginBottom": "4px"},
                    ),
                    html.P("• WFP — ціни та ринки", style={"fontSize": "11px", "color": "#8b949e"}),
                    html.P("• FAO — курс UAH/USD", style={"fontSize": "11px", "color": "#8b949e"}),
                    html.P("• Світовий банк — макро", style={"fontSize": "11px", "color": "#8b949e"}),
                ],
            ),
        ],
    )
