# =============================================================================
# callbacks/tabs_callbacks.py — Усі callbacks дашборду (tabs-архітектура)
# =============================================================================
# Архітектурний принцип:
#   Тільки ДВА callbacks у цьому файлі:
#
#   1. update_unit_options — оновлює список одиниць виміру при зміні товару
#      Input:  commodity-filter
#      Output: unit-filter options + value
#
#   2. render_tab — рендерить повний контент активної вкладки
#      Input:  tabs (активна вкладка) + ВСІ фільтри
#      Output: tab-content (html.Div з графіками)
#
# Чому один великий callback для рендерингу вкладки?
#   - Уникаємо callbacks для компонентів, яких немає в DOM
#   - Кожна вкладка отримує тільки ті дані, які їй потрібні
#   - Код освітній: легко зрозуміти, що відбувається при кожному переключенні
#
# Обмеження:
#   - При зміні будь-якого фільтра вся вкладка перебудовується
#   - Для production-рівня варто використовувати патерн-matching callbacks,
#     але для навчальних цілей цей підхід достатньо прозорий
# =============================================================================

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, html, dcc, dash_table


def import_numpy_polyfit(x, y) -> np.ndarray:
    """
    Обчислює коефіцієнти лінійної регресії y = a*x + b через numpy.polyfit.
    Використовується замість statsmodels для побудови лінії тренду на scatter plot.
    Повертає: [a, b] — нахил та точка перетину з віссю Y.
    """
    return np.polyfit(x.astype(float), y.astype(float), deg=1)

from data_utils import (
    get_dataset,
    get_units_for_commodity,
    get_food_timeseries,
    get_oblast_prices,
    get_oblast_variability,
    get_top_oblasts,
    get_food_summary_stats,
    get_exchange_timeseries,
    get_debt_indicators,
    get_debt_timeseries,
    get_debt_indicator_code,
    prepare_point_map_data,
    prepare_oblast_agg_map,
    align_food_and_exchange,
    compute_correlation,
)
from config import PLOTLY_TEMPLATE, MAP_STYLE, COLOR_SCALE


# =============================================================================
# Головна функція реєстрації callbacks
# =============================================================================

def register_tab_callbacks(app):
    """
    Реєструє всі callbacks дашборду в об'єкті app.

    Виклик цієї функції відбувається ОДИН РАЗ при старті в app.py.
    Всі декоратори @app.callback визначаються всередині цієї функції,
    щоб мати доступ до об'єкта app.
    """

    # =========================================================================
    # CALLBACK 1: Динамічне оновлення одиниць виміру при зміні товару
    # =========================================================================
    # Пояснення:
    #   Коли користувач обирає інший товар, список доступних одиниць виміру
    #   змінюється. Наприклад:
    #     - Sugar → тільки 'KG'
    #     - Bread (rye) → 'KG' і 'Loaf'
    #     - Milk → 'KG' і 'L'
    #   Без цього callback'у користувач міг би обрати одиницю,
    #   яка відсутня для обраного товару, і отримати порожній графік.

    @app.callback(
        Output("unit-filter", "options"),
        Output("unit-filter", "value"),
        Input("commodity-filter", "value"),
    )
    def update_unit_options(commodity: str):
        """Оновлює список одиниць виміру при зміні товару."""
        food_df = get_dataset("food")

        units = get_units_for_commodity(food_df, commodity)

        if not units:
            # Якщо одиниць немає — щось пішло не так з фільтрацією
            return [], None

        options = [{"label": u, "value": u} for u in units]
        default = units[0]   # перша одиниця як значення за замовчуванням

        return options, default


    # =========================================================================
    # CALLBACK 2: Рендеринг контенту активної вкладки
    # =========================================================================
    # Цей callback — серце дашборду.
    # Він викликається при:
    #   - переключенні вкладки (tabs)
    #   - зміні будь-якого фільтра (commodity, unit, oblast, date, debt)
    # і повертає повний HTML-контент для відображення.

    @app.callback(
        Output("tab-content", "children"),
        Input("tabs", "value"),
        Input("commodity-filter", "value"),
        Input("unit-filter", "value"),
        Input("oblast-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("debt-indicator-filter", "value"),
    )
    def render_tab(tab, commodity, unit, oblast, start_date, end_date, debt_indicator):
        """
        Рендерить повний контент активної вкладки.

        Параметри відповідають всім фільтрам сайдбару.
        Кожна гілка if-elif обробляє окрему вкладку незалежно.
        """

        # ── Вкладка 1: Огляд даних ────────────────────────────────────────
        if tab == "overview":
            return _render_overview()

        # ── Вкладка 2: Ціни на товари ─────────────────────────────────────
        elif tab == "food":
            return _render_food(commodity, unit, oblast, start_date, end_date)

        # ── Вкладка 3: Просторовий аналіз ────────────────────────────────
        elif tab == "spatial":
            return _render_spatial(commodity, unit)

        # ── Вкладка 4: Валютний курс ──────────────────────────────────────
        elif tab == "exchange":
            return _render_exchange()

        # ── Вкладка 5: Зовнішній борг ─────────────────────────────────────
        elif tab == "debt":
            return _render_debt(debt_indicator)

        # ── Вкладка 6: Кореляція цін і курсу ─────────────────────────────
        elif tab == "correlation":
            return _render_correlation(commodity, unit, oblast, start_date, end_date)

        # ── Вкладка 7: Методологія ────────────────────────────────────────
        elif tab == "methodology":
            return _render_methodology()

        # Невідома вкладка — не повинно відбуватися, але захист обов'язковий
        return html.Div("Невідома вкладка")


# =============================================================================
# Рендер-функції для кожної вкладки
# (визначені поза register_tab_callbacks для читабельності)
# =============================================================================


# ─────────────────────────────────────────────────────────────────────────────
# Вкладка 1: Огляд даних
# ─────────────────────────────────────────────────────────────────────────────

def _render_overview() -> html.Div:
    """
    Відображає структурний огляд усіх 4 датасетів.

    Не потребує жодних фільтрів — показує загальну статистику.
    Корисно для розуміння обсягу та охоплення даних.
    """
    food_df     = get_dataset("food")
    markets_df  = get_dataset("markets")
    exchange_df = get_dataset("exchange")
    debt_df     = get_dataset("debt")

    # ── Статистика по кожному датасету ──
    cards = [
        _info_card(
            title="🍞 Ціни на продукти (WFP)",
            stats=[
                ("Рядків",               f"{len(food_df):,}"),
                ("Товарів",              food_df["товар"].nunique()),
                ("Ринків",               food_df["id_ринку"].nunique()),
                ("Областей",             food_df["область"].dropna().nunique()),
                ("Одиниць виміру",       food_df["одиниця"].nunique()),
                ("Діапазон дат",         f"{food_df['дата'].min().date()} — {food_df['дата'].max().date()}"),
                ("Мін. ціна (UAH)",      f"{food_df['ціна'].min():.2f}"),
                ("Макс. ціна (UAH)",     f"{food_df['ціна'].max():.2f}"),
            ],
        ),
        _info_card(
            title="🗺️ Довідник ринків (WFP)",
            stats=[
                ("Ринків",               len(markets_df)),
                ("Областей",             markets_df["область"].dropna().nunique()),
                ("З координатами",       markets_df.dropna(subset=["широта","довгота"]).shape[0]),
                ("Без координат",        markets_df[["широта","довгота"]].isnull().any(axis=1).sum()),
            ],
        ),
        _info_card(
            title="💱 Курс UAH/USD (FAO)",
            stats=[
                ("Місячних спостережень", len(exchange_df)),
                ("Діапазон",             f"{exchange_df['рік'].min()} — {exchange_df['рік'].max()}"),
                ("Мін. курс",            f"{exchange_df['курс'].min():.2f}"),
                ("Макс. курс",           f"{exchange_df['курс'].max():.2f}"),
                ("Остання дата",         str(exchange_df["дата"].max().date())),
            ],
        ),
        _info_card(
            title="📉 Макроіндикатори (Світовий банк)",
            stats=[
                ("Рядків",               f"{len(debt_df):,}"),
                ("Індикаторів",          debt_df["індикатор"].nunique()),
                ("Діапазон років",       f"{debt_df['рік'].min()} — {debt_df['рік'].max()}"),
            ],
        ),
    ]

    # ── Структура товарів і одиниць ──
    commodity_unit_df = (
        food_df.groupby(["товар", "одиниця"])
        .agg(n=("ціна", "count"))
        .reset_index()
        .rename(columns={"товар": "Товар", "одиниця": "Одиниця виміру", "n": "Спостережень"})
    )

    table = dash_table.DataTable(
        data=commodity_unit_df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in commodity_unit_df.columns],
        style_table={"overflowX": "auto", "maxHeight": "400px", "overflowY": "auto"},
        style_header={"backgroundColor": "#161b22", "color": "white", "fontWeight": "bold"},
        style_cell={"backgroundColor": "#0d1117", "color": "white",
                    "fontSize": "13px", "padding": "6px 12px"},
        sort_action="native",
        filter_action="native",
        page_action="none",
    )

    return html.Div([
        html.H3("Огляд датасетів"),
        html.P(
            "Нижче наведено структурну інформацію про всі 4 завантажені датасети. "
            "Перед початком аналізу важливо розуміти охоплення та обмеження кожного з них.",
            style={"color": "#8b949e"},
        ),

        # Картки з метаданими
        html.Div(cards, style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "32px"}),

        # Таблиця товар × одиниця
        html.H4("Товари та одиниці виміру в датасеті WFP"),
        html.P(
            "⚠️ ВАЖЛИВО: Один і той самий товар може мати РІЗНІ одиниці виміру. "
            "Ніколи не порівнюйте ціни з різними одиницями безпосередньо.",
            style={"color": "#f0883e", "fontSize": "13px"},
        ),
        table,
    ])


def _info_card(title: str, stats: list[tuple]) -> html.Div:
    """
    Допоміжна функція: будує картку з метаданими датасету.
    """
    rows = [
        html.Tr([
            html.Td(label, style={"color": "#8b949e", "paddingRight": "12px", "whiteSpace": "nowrap"}),
            html.Td(str(value), style={"fontWeight": "bold"}),
        ])
        for label, value in stats
    ]

    return html.Div(
        style={
            "background": "#161b22",
            "border": "1px solid #30363d",
            "borderRadius": "8px",
            "padding": "16px",
            "minWidth": "260px",
            "flex": "1",
        },
        children=[
            html.H4(title, style={"marginTop": "0", "marginBottom": "12px", "fontSize": "15px"}),
            html.Table(rows, style={"fontSize": "13px", "width": "100%"}),
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Вкладка 2: Ціни на товари
# ─────────────────────────────────────────────────────────────────────────────

def _render_food(
    commodity: str,
    unit: str,
    oblast: str,
    start_date,
    end_date,
) -> html.Div:
    """
    Аналіз динаміки та регіональної структури цін обраного товару.

    Графіки:
        1. Лінійний — медіанна ціна по місяцях
        2. Стовпчастий — медіана ціни по областях
        3. Box plot — розподіл цін по областях (варіативність)
        4. Таблиця описової статистики
    """
    food_df = get_dataset("food")

    # Заголовок секції — уточнюємо товар та одиницю для читача
    oblast_label = oblast if oblast and oblast != "Всі" else "всі регіони"
    header_note = (
        f"Товар: **{commodity}** | Одиниця: **{unit}** | Регіон: **{oblast_label}**"
    )

    # ── Графік 1: Часова динаміка цін ──────────────────────────────────────
    ts_df = get_food_timeseries(food_df, commodity=commodity, unit=unit,
                                oblast=oblast if oblast != "Всі" else None)

    if not ts_df.empty and start_date and end_date:
        ts_df = ts_df[
            (ts_df["дата"] >= pd.to_datetime(start_date)) &
            (ts_df["дата"] <= pd.to_datetime(end_date))
        ]

    if ts_df.empty:
        fig_ts = _empty_figure("Немає даних для обраного товару/регіону/дат")
    else:
        fig_ts = go.Figure()

        # Медіанна ціна — основна лінія
        fig_ts.add_trace(go.Scatter(
            x=ts_df["дата"], y=ts_df["медіана_ціни"],
            name="Медіана", mode="lines", line={"color": "#58a6ff", "width": 2},
            hovertemplate="Дата: %{x|%m.%Y}<br>Медіана: %{y:.2f} UAH<extra></extra>",
        ))

        # Середня ціна — пунктир
        fig_ts.add_trace(go.Scatter(
            x=ts_df["дата"], y=ts_df["середня_ціна"],
            name="Середнє", mode="lines",
            line={"color": "#f0883e", "width": 1.5, "dash": "dash"},
            hovertemplate="Дата: %{x|%m.%Y}<br>Середнє: %{y:.2f} UAH<extra></extra>",
        ))

        fig_ts.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(text=f"Динаміка ціни: {commodity} ({unit})", font={"size": 15}),
            xaxis_title="Дата",
            yaxis_title=f"Ціна (UAH / {unit})",
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
            margin={"t": 60, "b": 40, "l": 60, "r": 20},
            annotations=[{
                "text": "Агрегація по місяцях по всіх ринках обраного регіону",
                "xref": "paper", "yref": "paper",
                "x": 0, "y": -0.12, "showarrow": False,
                "font": {"size": 10, "color": "#8b949e"},
            }],
        )

    # ── Графік 2: Порівняння цін по областях ───────────────────────────────
    oblast_df = get_oblast_prices(food_df, commodity=commodity, unit=unit)

    if oblast_df.empty:
        fig_oblast = _empty_figure("Немає регіональних даних")
    else:
        fig_oblast = px.bar(
            oblast_df,
            x="медіана_ціни",
            y="область",
            orientation="h",
            color="медіана_ціни",
            color_continuous_scale=COLOR_SCALE,
            hover_data={"n": True, "середня_ціна": ":.2f", "медіана_ціни": ":.2f"},
            labels={
                "медіана_ціни": f"Медіана ціни (UAH/{unit})",
                "область": "Область",
                "n": "Спостережень",
            },
            title=f"Медіанна ціна по областях: {commodity} ({unit})",
        )
        fig_oblast.update_layout(
            template=PLOTLY_TEMPLATE,
            yaxis={"categoryorder": "total ascending"},
            margin={"t": 60, "b": 40, "l": 150, "r": 20},
            coloraxis_showscale=False,
            annotations=[{
                "text": "⚠️ Охоплення ринків різне по регіонах — перевіряйте n",
                "xref": "paper", "yref": "paper",
                "x": 0, "y": -0.08, "showarrow": False,
                "font": {"size": 10, "color": "#8b949e"},
            }],
        )

    # ── Графік 3: Box plot розподілу цін по областях ────────────────────────
    var_df = get_oblast_variability(food_df, commodity=commodity, unit=unit)

    if var_df.empty or var_df["область"].dropna().empty:
        fig_box = _empty_figure("Немає даних для аналізу варіативності")
    else:
        fig_box = px.box(
            var_df.dropna(subset=["область"]),
            x="область",
            y="ціна",
            color="область",
            title=f"Розподіл цін по областях: {commodity} ({unit})",
            labels={"ціна": f"Ціна (UAH/{unit})", "область": "Область"},
        )
        fig_box.update_layout(
            template=PLOTLY_TEMPLATE,
            showlegend=False,
            xaxis={"tickangle": -45},
            margin={"t": 60, "b": 100, "l": 60, "r": 20},
            annotations=[{
                "text": "Box: Q1–медіана–Q3 | Вуса: 1.5×IQR | Точки: викиди",
                "xref": "paper", "yref": "paper",
                "x": 0, "y": -0.22, "showarrow": False,
                "font": {"size": 10, "color": "#8b949e"},
            }],
        )

    # ── Таблиця: описова статистика ─────────────────────────────────────────
    stats_df = get_food_summary_stats(food_df, commodity=commodity, unit=unit)

    if stats_df.empty:
        stats_table = html.P("Дані відсутні")
    else:
        stats_table = dash_table.DataTable(
            data=stats_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in stats_df.columns],
            style_table={"maxWidth": "400px"},
            style_header={"backgroundColor": "#161b22", "color": "white", "fontWeight": "bold"},
            style_cell={"backgroundColor": "#0d1117", "color": "white",
                        "fontSize": "13px", "padding": "6px 12px"},
        )

    # ── Топ областей ────────────────────────────────────────────────────────
    expensive, cheap = get_top_oblasts(food_df, commodity=commodity, unit=unit, n=5)

    top_section = html.Div([
        html.Div([
            html.H5("🔴 Найдорожчі регіони (медіана)", style={"color": "#f85149"}),
            html.Ul([
                html.Li(f"{row['область']}: {row['медіана_ціни']:.2f} UAH (n={row['n']})")
                for _, row in expensive.iterrows()
            ]) if not expensive.empty else html.P("—"),
        ], style={"flex": "1"}),
        html.Div([
            html.H5("🟢 Найдешевші регіони (медіана)", style={"color": "#3fb950"}),
            html.Ul([
                html.Li(f"{row['область']}: {row['медіана_ціни']:.2f} UAH (n={row['n']})")
                for _, row in cheap.iterrows()
            ]) if not cheap.empty else html.P("—"),
        ], style={"flex": "1"}),
    ], style={"display": "flex", "gap": "32px"})

    return html.Div([
        html.H3("Аналіз цін на товари"),
        html.P(
            f"Товар: {commodity} ({unit}) | Регіон: {oblast_label}",
            style={"color": "#8b949e"},
        ),

        html.Div([
            dcc.Graph(figure=fig_ts, style={"marginBottom": "24px"}),
            dcc.Graph(figure=fig_oblast, style={"marginBottom": "24px"}),
        ]),

        html.Div([
            html.Div([
                dcc.Graph(figure=fig_box),
            ], style={"flex": "2"}),
            html.Div([
                html.H5("Описова статистика"),
                stats_table,
                html.Br(),
                top_section,
            ], style={"flex": "1", "paddingLeft": "24px"}),
        ], style={"display": "flex", "gap": "16px", "alignItems": "flex-start"}),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Вкладка 3: Просторовий аналіз
# ─────────────────────────────────────────────────────────────────────────────

def _render_spatial(commodity: str, unit: str) -> html.Div:
    """
    Геопросторова візуалізація цін на обраний товар.

    Карта 1 (точкова): кожен ринок — точка, колір = остання ціна.
    Карта 2 (агрегована): медіанна ціна по кожній ринку у вигляді кіл.

    МЕТОДОЛОГІЧНЕ ОБМЕЖЕННЯ:
        - Охоплення ринків нерівномірне по регіонах та в часі.
        - Відсутні координати у ~856 записів (National Average).
        - Не будуємо псевдонаукову теплову карту з інтерполяцією:
          для цього потрібна просторова модель (крігінг тощо),
          яка не обґрунтована для даного датасету.
    """
    food_df    = get_dataset("food")
    markets_df = get_dataset("markets")

    map_data = prepare_point_map_data(
        food_df=food_df,
        markets_df=markets_df,
        commodity=commodity,
        unit=unit,
    )

    if map_data.empty:
        return html.Div([
            html.H3("Просторовий аналіз цін"),
            html.P(
                f"Немає ринків з координатами для: {commodity} ({unit}). "
                "Спробуйте інший товар або одиницю виміру.",
                style={"color": "#f85149"},
            ),
        ])

    # Форматуємо дату для tooltip
    map_data = map_data.copy()
    map_data["дата_str"] = map_data["дата"].dt.strftime("%d.%m.%Y")

    # Точкова карта ринків
    fig_map = px.scatter_mapbox(
        map_data,
        lat="широта_карта",
        lon="довгота_карта",
        color="ціна",
        size="ціна",
        hover_name="ринок",
        hover_data={
            "область":    True,
            "ціна":       ":.2f",
            "дата_str":   True,
            "одиниця":    True,
            "широта_карта": False,
            "довгота_карта": False,
        },
        labels={
            "ціна":     f"Ціна (UAH/{unit})",
            "область":  "Область",
            "дата_str": "Дата",
            "одиниця":  "Одиниця",
        },
        color_continuous_scale=COLOR_SCALE,
        size_max=18,
        zoom=5.2,
        center={"lat": 49.0, "lon": 32.0},   # центр України
        title=f"Ціни на {commodity} ({unit}) по ринках — остання дата",
        mapbox_style=MAP_STYLE,
    )
    fig_map.update_layout(
        template=PLOTLY_TEMPLATE,
        height=500,
        margin={"t": 50, "b": 0, "l": 0, "r": 0},
        coloraxis_colorbar={"title": f"UAH/{unit}"},
    )

    # Статистика покриття
    n_markets  = len(map_data)
    n_oblasts  = map_data["область"].dropna().nunique()
    date_range = (
        f"{map_data['дата'].min().strftime('%d.%m.%Y')} — "
        f"{map_data['дата'].max().strftime('%d.%m.%Y')}"
    )

    return html.Div([
        html.H3("Просторовий аналіз цін"),
        html.P(
            f"Товар: {commodity} ({unit}) | "
            f"Ринків на карті: {n_markets} | Областей: {n_oblasts} | "
            f"Діапазон дат: {date_range}",
            style={"color": "#8b949e", "fontSize": "13px"},
        ),
        html.P(
            "⚠️ На карті показана ОСТАННЯ зафіксована ціна кожного ринку. "
            "Ринки з різними датами останнього спостереження можуть не бути "
            "порівнянними між собою.",
            style={"color": "#f0883e", "fontSize": "12px", "marginBottom": "16px"},
        ),
        dcc.Graph(figure=fig_map, style={"marginBottom": "24px"}),

        # Таблиця з даними карти
        html.H4("Деталізація по ринках"),
        dash_table.DataTable(
            data=map_data[["ринок", "область", "ціна", "дата_str"]].rename(columns={
                "ринок": "Ринок", "область": "Область",
                "ціна": f"Ціна (UAH/{unit})", "дата_str": "Дата"
            }).to_dict("records"),
            columns=[
                {"name": "Ринок",               "id": "Ринок"},
                {"name": "Область",             "id": "Область"},
                {"name": f"Ціна (UAH/{unit})",  "id": f"Ціна (UAH/{unit})"},
                {"name": "Дата",                "id": "Дата"},
            ],
            style_table={"maxHeight": "300px", "overflowY": "auto"},
            style_header={"backgroundColor": "#161b22", "color": "white", "fontWeight": "bold"},
            style_cell={"backgroundColor": "#0d1117", "color": "white",
                        "fontSize": "12px", "padding": "5px 10px"},
            sort_action="native",
            filter_action="native",
            page_action="none",
        ),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Вкладка 4: Валютний курс
# ─────────────────────────────────────────────────────────────────────────────

def _render_exchange() -> html.Div:
    """
    Відображає повний часовий ряд курсу UAH/USD з 1996 по 2026 рік.

    Фільтри сайдбару (товар, область тощо) до цієї вкладки не застосовуються.
    Курс показується для всього доступного діапазону.

    Ключові економічні події відзначені анотаціями для навчального контексту.
    """
    exchange_df = get_dataset("exchange")
    ts_df = get_exchange_timeseries(exchange_df)

    if ts_df.empty:
        return html.Div([html.H3("Валютний курс"), html.P("Дані відсутні")])

    # ── Основний графік: курс UAH/USD ──
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=ts_df["дата"],
        y=ts_df["курс"],
        name="UAH/USD",
        mode="lines",
        line={"color": "#58a6ff", "width": 2},
        fill="tozeroy",
        fillcolor="rgba(88, 166, 255, 0.08)",
        hovertemplate="Дата: %{x|%m.%Y}<br>Курс: %{y:.2f} UAH/USD<extra></extra>",
    ))

    # Анотації ключових подій — для навчального контексту
    events = [
        ("2008-10-01", "Криза 2008"),
        ("2014-03-01", "Початок\nконфлікту"),
        ("2015-02-01", "Піки\nдевальвації"),
        ("2022-02-01", "Повномасштабне\nвторгнення"),
    ]

    for date_str, label in events:
        date_ts = pd.Timestamp(date_str)
        if ts_df["дата"].min() <= date_ts <= ts_df["дата"].max():
            fig.add_vline(
                x=date_ts.timestamp() * 1000,
                line_dash="dash",
                line_color="#f0883e",
                opacity=0.6,
            )
            fig.add_annotation(
                x=date_ts,
                y=ts_df["курс"].max() * 0.95,
                text=label,
                showarrow=False,
                font={"size": 9, "color": "#f0883e"},
                align="center",
            )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Курс гривні до долара США (UAH/USD), місячні дані",
        xaxis_title="Дата",
        yaxis_title="Гривень за 1 USD",
        height=450,
        margin={"t": 60, "b": 50, "l": 70, "r": 20},
        annotations=[{
            "text": (
                "Серія: Local currency units per USD (FAO/FAOSTAT) | "
                "Валюта: UAH (гривня) | Кареляція ≠ причинність"
            ),
            "xref": "paper", "yref": "paper",
            "x": 0, "y": -0.12, "showarrow": False,
            "font": {"size": 10, "color": "#8b949e"},
        }] + [a for a in fig.layout.annotations],
    )

    # ── Статистика ──
    stats = ts_df["курс"].describe()
    stat_items = [
        ("Кількість спостережень", int(stats["count"])),
        ("Мінімальний курс", f"{stats['min']:.4f} UAH"),
        ("Максимальний курс", f"{stats['max']:.4f} UAH"),
        ("Середній курс", f"{stats['mean']:.2f} UAH"),
        ("Медіанний курс", f"{stats['50%']:.2f} UAH"),
    ]

    return html.Div([
        html.H3("Валютний курс UAH/USD"),
        html.P(
            "Місячна динаміка офіційного обмінного курсу гривні до долара США. "
            "Дані: FAO/FAOSTAT. Серія: 'Local currency units per USD'.",
            style={"color": "#8b949e"},
        ),
        dcc.Graph(figure=fig),

        html.Div([
            html.H4("Підсумкова статистика курсу"),
            html.Table([
                html.Tr([
                    html.Td(label, style={"color": "#8b949e", "paddingRight": "16px"}),
                    html.Td(str(value), style={"fontWeight": "bold"}),
                ])
                for label, value in stat_items
            ], style={"fontSize": "13px"}),
        ], style={
            "background": "#161b22",
            "border": "1px solid #30363d",
            "borderRadius": "8px",
            "padding": "16px",
            "marginTop": "16px",
            "display": "inline-block",
        }),

        html.P(
            "⚠️ Даний курс є ОРІЄНТОВНИМ і базується на даних FAO. "
            "Для точного фінансового аналізу використовуйте офіційні дані НБУ.",
            style={"color": "#f0883e", "fontSize": "12px", "marginTop": "16px"},
        ),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Вкладка 5: Зовнішній борг та макроіндикатори
# ─────────────────────────────────────────────────────────────────────────────

def _render_debt(indicator: str) -> html.Div:
    """
    Відображає часовий ряд обраного макроекономічного індикатора.

    Вибір індикатора здійснюється через sidebar (debt-indicator-filter).

    КРИТИЧНА МЕТОДОЛОГІЧНА ПРИМІТКА:
        Цей датасет містить 59 РІЗНИХ показників платіжного балансу.
        Вони мають різну природу і вимірюються в різних одиницях.
        НІКОЛИ не порівнюйте та не усереднюйте різні індикатори
        між собою — це позбавлене економічного сенсу.
    """
    debt_df = get_dataset("debt")

    if not indicator:
        return html.Div([
            html.H3("Зовнішній борг та макроіндикатори"),
            html.P("Оберіть індикатор у бічній панелі.", style={"color": "#8b949e"}),
        ])

    ts_df = get_debt_timeseries(debt_df, indicator=indicator)
    code  = get_debt_indicator_code(debt_df, indicator)

    if ts_df.empty:
        return html.Div([
            html.H3("Зовнішній борг та макроіндикатори"),
            html.P(f"Немає даних для: {indicator}", style={"color": "#f85149"}),
        ])

    # Визначаємо одиниці — більшість показників у current USD
    unit_note = "(поточні USD, якщо не зазначено інше)"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=ts_df["рік"],
        y=ts_df["значення"],
        marker_color="#58a6ff",
        name="Значення",
        hovertemplate="Рік: %{x}<br>Значення: %{y:,.0f}<extra></extra>",
    ))

    # Лінія тренду
    ts_clean = ts_df.dropna(subset=["значення"])
    if len(ts_clean) >= 3:
        fig.add_trace(go.Scatter(
            x=ts_clean["рік"],
            y=ts_clean["значення"].rolling(3, center=True).mean(),
            name="Тренд (3-річне середнє)",
            mode="lines",
            line={"color": "#f0883e", "width": 2, "dash": "dash"},
            hovertemplate="Рік: %{x}<br>Тренд: %{y:,.0f}<extra></extra>",
        ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=f"{indicator[:80]}{'...' if len(indicator) > 80 else ''}",
        xaxis_title="Рік",
        yaxis_title=unit_note,
        height=420,
        margin={"t": 80, "b": 50, "l": 80, "r": 20},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        annotations=[{
            "text": f"Код індикатора: {code} | Джерело: Світовий банк",
            "xref": "paper", "yref": "paper",
            "x": 0, "y": -0.12, "showarrow": False,
            "font": {"size": 10, "color": "#8b949e"},
        }],
    )

    # Всі доступні індикатори для довідки
    all_indicators = get_debt_indicators(debt_df)

    return html.Div([
        html.H3("Зовнішній борг та макроіндикатори"),
        html.Div(
            f"Обраний індикатор: {indicator}",
            style={
                "background": "#161b22",
                "border": "1px solid #30363d",
                "borderRadius": "6px",
                "padding": "8px 12px",
                "fontSize": "13px",
                "marginBottom": "16px",
                "wordBreak": "break-word",
            },
        ),

        html.P(
            "⚠️ МЕТОДОЛОГІЧНЕ ЗАСТЕРЕЖЕННЯ: Датасет містить 59 різних індикаторів "
            "платіжного балансу. Вони не підлягають порівнянню між собою. "
            "Інтерпретуйте кожен індикатор окремо відповідно до його визначення.",
            style={"color": "#f0883e", "fontSize": "12px", "marginBottom": "16px"},
        ),

        dcc.Graph(figure=fig),

        html.Details([
            html.Summary(
                f"📋 Усі доступні індикатори ({len(all_indicators)})",
                style={"cursor": "pointer", "color": "#58a6ff", "marginTop": "16px"},
            ),
            html.Ul([
                html.Li(ind, style={"fontSize": "12px", "color": "#8b949e", "marginBottom": "2px"})
                for ind in all_indicators
            ], style={"marginTop": "8px", "columns": "2"}),
        ]),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Вкладка 6: Зв'язок цін і валютного курсу
# ─────────────────────────────────────────────────────────────────────────────

def _render_correlation(
    commodity: str,
    unit: str,
    oblast: str,
    start_date,
    end_date,
) -> html.Div:
    """
    Аналіз спільного руху ціни обраного товару та курсу UAH/USD.

    Методологія:
        1. Агрегуємо ціни по місяцях (медіана)
        2. Вирівнюємо з курсом UAH/USD по місяцях (inner join)
        3. Будуємо scatter plot та порівняльний лінійний графік
        4. Обчислюємо кореляцію Пірсона

    КРИТИЧНЕ ЗАСТЕРЕЖЕННЯ:
        Кореляція вимірює СПІЛЬНИЙ РУХ двох рядів.
        Вона НЕ ДОВОДИТЬ, що курс валюти СПРИЧИНЯЄ зміну цін
        або навпаки. Обидва показники можуть реагувати
        на спільний третій чинник (наприклад, воєнний конфлікт).
    """
    food_df     = get_dataset("food")
    exchange_df = get_dataset("exchange")

    oblast_label = oblast if oblast and oblast != "Всі" else None

    # Вирівнюємо ряди по місяцях
    aligned = align_food_and_exchange(
        food_df=food_df,
        exchange_df=exchange_df,
        commodity=commodity,
        unit=unit,
        oblast=oblast_label,
    )

    # Обрізаємо за діапазоном дат, якщо задано
    if not aligned.empty and start_date and end_date:
        aligned = aligned[
            (aligned["дата"] >= pd.to_datetime(start_date)) &
            (aligned["дата"] <= pd.to_datetime(end_date))
        ]

    if aligned.empty:
        return html.Div([
            html.H3("Зв'язок цін і валютного курсу"),
            html.P(
                f"Не вдалося вирівняти дані для {commodity} ({unit}). "
                "Можливо, часові ряди не перетинаються для обраного фільтру.",
                style={"color": "#f85149"},
            ),
        ])

    # Кореляція
    corr = compute_correlation(aligned)

    # ── Графік 1: Порівняльний часовий ряд (подвійна вісь Y) ──
    fig_ts = go.Figure()

    fig_ts.add_trace(go.Scatter(
        x=aligned["дата"], y=aligned["медіана_ціни"],
        name=f"Ціна {commodity} ({unit}), UAH",
        mode="lines",
        line={"color": "#58a6ff", "width": 2},
        yaxis="y1",
        hovertemplate="Дата: %{x|%m.%Y}<br>Ціна: %{y:.2f} UAH<extra></extra>",
    ))

    fig_ts.add_trace(go.Scatter(
        x=aligned["дата"], y=aligned["курс"],
        name="Курс UAH/USD",
        mode="lines",
        line={"color": "#f0883e", "width": 2},
        yaxis="y2",
        hovertemplate="Дата: %{x|%m.%Y}<br>Курс: %{y:.2f} UAH/USD<extra></extra>",
    ))

    fig_ts.update_layout(
        template=PLOTLY_TEMPLATE,
        title=f"Ціна {commodity} ({unit}) vs Курс UAH/USD по місяцях",
        xaxis_title="Дата",
        yaxis=dict(title=f"Ціна (UAH/{unit})", side="left", color="#58a6ff"),
        yaxis2=dict(title="Курс (UAH/USD)", side="right", overlaying="y", color="#f0883e"),
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        margin={"t": 70, "b": 50, "l": 70, "r": 70},
        height=400,
    )

    # ── Графік 2: Scatter plot ціна vs курс ──
    # Будуємо scatter plot із ручною лінією тренду (OLS без statsmodels)
    # Використовуємо numpy.polyfit — це базова лінійна регресія y = ax + b
    scatter_clean = aligned.dropna(subset=["медіана_ціни", "курс"])

    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(
        x=scatter_clean["курс"],
        y=scatter_clean["медіана_ціни"],
        mode="markers",
        name="Спостереження",
        marker={"color": "#58a6ff", "size": 6, "opacity": 0.7},
        customdata=scatter_clean["дата"].dt.strftime("%m.%Y"),
        hovertemplate=(
            "Курс: %{x:.2f} UAH/USD<br>"
            f"Ціна: %{{y:.2f}} UAH/{unit}<br>"
            "Дата: %{customdata}<extra></extra>"
        ),
    ))

    # Лінія тренду через numpy.polyfit (лінійна регресія)
    if len(scatter_clean) >= 2:
        coeffs = import_numpy_polyfit(scatter_clean["курс"], scatter_clean["медіана_ціни"])
        x_line = pd.Series([scatter_clean["курс"].min(), scatter_clean["курс"].max()])
        y_line = coeffs[0] * x_line + coeffs[1]
        fig_scatter.add_trace(go.Scatter(
            x=x_line, y=y_line,
            mode="lines",
            name="Лінійний тренд (OLS)",
            line={"color": "#f0883e", "width": 2, "dash": "dash"},
            hoverinfo="skip",
        ))

    fig_scatter.update_layout(
        template=PLOTLY_TEMPLATE,
        title=f"Scatter: {commodity} ({unit}) vs Курс UAH/USD | r = {corr['pearson_r']}",
        xaxis_title="Курс UAH/USD",
        yaxis_title=f"Медіана ціни (UAH/{unit})",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
    )

    fig_scatter.update_layout(
        template=PLOTLY_TEMPLATE,
        height=380,
        margin={"t": 60, "b": 50, "l": 70, "r": 20},
    )

    # ── Блок з результатом кореляції ──
    r_color = "#3fb950" if abs(corr["pearson_r"] or 0) > 0.5 else "#8b949e"

    return html.Div([
        html.H3("Зв'язок ціни товару та валютного курсу"),
        html.P(
            f"Товар: {commodity} ({unit}) | Вирівняних місячних спостережень: {corr['n']}",
            style={"color": "#8b949e"},
        ),

        # Результат кореляції — виділений блок
        html.Div([
            html.P(
                corr["interpretation"],
                style={"color": r_color, "fontSize": "14px", "fontWeight": "bold", "margin": "0"},
            ),
            html.P(
                "⚠️ ВАЖЛИВО: Кореляція описує спільний рух двох показників, "
                "але НЕ ДОВОДИТЬ причинно-наслідковий зв'язок між ними. "
                "Для встановлення причинності потрібен спеціальний економетричний аналіз "
                "(наприклад, тест Грейнджера на причинність).",
                style={"color": "#8b949e", "fontSize": "12px", "marginTop": "8px", "margin": "8px 0 0 0"},
            ),
        ], style={
            "background": "#161b22",
            "border": "1px solid #30363d",
            "borderRadius": "8px",
            "padding": "16px",
            "marginBottom": "24px",
        }),

        dcc.Graph(figure=fig_ts, style={"marginBottom": "16px"}),
        dcc.Graph(figure=fig_scatter),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Вкладка 7: Методологія та пояснення
# ─────────────────────────────────────────────────────────────────────────────

def _render_methodology() -> html.Div:
    """
    Методологічна довідка — статичний текст.

    Ця вкладка не потребує жодних даних.
    Вона пояснює методологічні рішення та обмеження дашборду.
    """

    def _section(title, content_items):
        return html.Div([
            html.H4(title, style={"color": "#58a6ff", "borderBottom": "1px solid #30363d", "paddingBottom": "8px"}),
            html.Ul([
                html.Li(item, style={"marginBottom": "6px", "fontSize": "13px"})
                for item in content_items
            ]),
        ], style={"marginBottom": "24px"})

    return html.Div([
        html.H3("Методологія та пояснення"),

        html.P(
            "Цей дашборд побудований на основі 4 реальних датасетів. "
            "Нижче викладено методологічні рішення, обмеження та застереження, "
            "які необхідно враховувати при інтерпретації результатів.",
            style={"color": "#8b949e", "marginBottom": "24px"},
        ),

        _section("Джерела даних", [
            "WFP (World Food Programme): wfp_food_prices_ukr.csv — роздрібні ціни на 45 товарів по ринках України, 2014–2025",
            "WFP: wfp_markets_ukr.csv — довідник 268 ринків з координатами та адміністративними одиницями",
            "FAO/FAOSTAT: exchange-rates_ukr.csv — місячний курс UAH/USD, 1990–2026",
            "Світовий банк: external-debt_ukr.csv — 59 макроекономічних індикаторів платіжного балансу, 1989–2024",
        ]),

        _section("Ціни на продукти — методологічні рішення", [
            "Агрегація тільки після фільтрації за товаром І одиницею виміру (ніколи не змішуємо kg, L, Loaf тощо)",
            "Використовується медіана, а не середнє — стійкіша до викидів і нерівномірного охоплення ринків",
            "Рядки 'National Average' (попередньо обчислені WFP) виключаються з регіонального аналізу",
            "Пусті значення (NaN) для координат і областей у рядках 'National Average' є очікуваними, не помилкою",
            "Топ-регіони відображаються тільки для регіонів з ≥5 спостережень",
        ]),

        _section("Обмеження продуктових цін", [
            "Охоплення ринків суттєво відрізняється між областями та в часі — менш представлені регіони можуть давати менш надійні оцінки",
            "Деякі товари мають кілька одиниць виміру (kg/L, loaf/kg) — обов'язково обирайте конкретну одиницю перед аналізом",
            "Всі ціни є роздрібними (pricetype='Retail') — оптові, сільськогосподарські ціни не включені",
            "Середнє та медіана перетинаються з часом — значна різниця між ними сигналізує про асиметричний розподіл",
        ]),

        _section("Курс обміну валюти — методологічні рішення", [
            "Використовується тільки серія 'Local currency units per USD' для гривні (UAH)",
            "Старий карбованець (UAK) виключено — не сумісний з гривнею без перерахунку",
            "Річні підсумки ('Annual value') виключені — використовуються тільки місячні спостереження",
            "Дата будується з колонки StartDate — перший день місяця спостереження",
        ]),

        _section("Обмеження курсу обміну", [
            "Дані FAO є орієнтовними — для точного фінансового аналізу використовуйте дані НБУ",
            "Між різними джерелами (НБУ, МВФ, FAO) можуть бути незначні розбіжності в методології",
        ]),

        _section("Макроіндикатори — методологічні рішення", [
            "59 індикаторів мають РІЗНУ економічну природу та одиниці виміру",
            "Дозволено вибір тільки ОДНОГО індикатора для аналізу — це принципово",
            "Тренд обчислюється як 3-річне ковзне середнє (center=True) — згладжує циклічні коливання",
        ]),

        _section("Обмеження макроіндикаторів", [
            "Більшість показників у поточних USD — для міжчасових порівнянь потрібна дефляція до постійних цін",
            "Деякі роки мають пропуски — особливо 1989–1994 (відсутність даних для нової країни)",
            "Різні індикатори не підлягають порівнянню між собою без методологічного обґрунтування",
        ]),

        _section("Кореляційний аналіз — методологічні рішення", [
            "Ряди вирівнюються по місяцях через inner join — без інтерполяції відсутніх значень",
            "Обчислюється кореляція Пірсона (r) та p-значення",
            "Тренд-лінія на scatter plot — OLS (метод найменших квадратів)",
        ]),

        _section("Критичні застереження щодо кореляції", [
            "⚠️ КОРЕЛЯЦІЯ НЕ ОЗНАЧАЄ ПРИЧИННІСТЬ. Спільний рух двох показників може бути зумовлений третім чинником",
            "Наприклад, і ціни, і курс одночасно реагують на воєнний конфлікт — це не означає, що одне спричиняє інше",
            "Для перевірки причинності потрібен тест Грейнджера або інші економетричні методи",
            "Кореляція чутлива до трендів — обидва ряди можуть зростати без прямого зв'язку",
        ]),

        _section("Просторовий аналіз — методологічні рішення", [
            "Точкова карта показує ОСТАННЮ зафіксовану ціну кожного ринку — дати останньої звітності можуть відрізнятися",
            "Ринки об'єднуються з довідником через market_id (100% збіг за ключем)",
            "1 ринок без координат у довіднику виключається з карти",
        ]),

        _section("Обмеження просторового аналізу", [
            "НЕ будується теплова карта з інтерполяцією — для цього потрібна обґрунтована просторова модель (крігінг тощо)",
            "Нерівномірна густота ринків по регіонах може візуально спотворювати сприйняття",
            "Ринки на захоплених чи прикордонних територіях можуть мати нерегулярне звітування",
        ]),
    ])


# =============================================================================
# Допоміжна функція: порожній графік із повідомленням
# =============================================================================

def _empty_figure(message: str) -> go.Figure:
    """
    Повертає порожній графік із текстовим повідомленням.
    Використовується замість помилки, коли дані відсутні.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font={"size": 14, "color": "#8b949e"},
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        xaxis={"visible": False},
        yaxis={"visible": False},
        height=300,
    )
    return fig
