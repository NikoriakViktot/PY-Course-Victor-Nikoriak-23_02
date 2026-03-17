# ============================================================
#  🍽️  Bistro Analytics — Система аналітики ресторану
#  Урок 8: Функціональне програмування — реальний міні-проєкт
# ============================================================
#
#  ЗВ'ЯЗОК З КОНСПЕКТАМИ:
#
#  ← lessons/07.../restaurant_analysis.ipynb
#       Order(NamedTuple) + List[Order] + for-loop patterns
#
#  ← lessons/08.../notes_functions.ipynb
#       Pure Functions · Predicate · Transformer · Reducer
#       Functional Decomposition · Pipeline
#
#  PIPELINE:
#
#  seaborn tips
#      │
#      ▼  load_orders()           ← DataFrame → List[Order]  (Transformer)
#  List[Order]
#      │
#      ▼  apply_filters()         ← Predicates (фейсконтроль)
#  List[Order]  (відфільтрований)
#      │
#      ├─► enrich_order()         ← Transformer (збагачення кожного чека)
#      │   → List[RichOrder]
#      │
#      ├─► calc_kpis()            ← Reducer  (KPI картки)
#      ├─► group_by_day()         ← Reducer  (графік по днях)
#      ├─► group_by_time()        ← Reducer  (Lunch vs Dinner)
#      ├─► group_by_size()        ← Reducer  (розмір столу)
#      ├─► top_by_tip_pct()       ← Predicate + Reducer (топ чеки)
#      └─► to_table_rows()        ← Transformer (таблиця)
#
# ============================================================

from typing import NamedTuple
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, dash_table

# ─────────────────────────────────────────────────────────────────────────────
#  БЛОК 1: СТРУКТУРА ДАНИХ
#  (те саме що в restaurant_analysis.ipynb — Частина 3)
# ─────────────────────────────────────────────────────────────────────────────
class Order(NamedTuple):
    """
    Один чек ресторану.
    NamedTuple = tuple з іменами полів (незмінний, читабельний).
    З notebooks/restaurant_analysis.ipynb, Частина 3.
    """
    total_bill: float
    tip:        float
    sex:        str
    smoker:     str
    day:        str
    time:       str
    size:       int


class RichOrder(NamedTuple):
    """
    Збагачений чек — Order + обчислені поля.
    Трансформер enrich_order() повертає RichOrder.
    """
    total_bill:      float
    tip:             float
    sex:             str
    smoker:          str
    day:             str
    time:            str
    size:            int
    tip_pct:         float   # ← нове поле: % чайових
    bill_per_person: float   # ← нове поле: $ на людину
    day_ua:          str     # ← нове поле: день українською
    time_ua:         str     # ← нове поле: зміна українською


# ─────────────────────────────────────────────────────────────────────────────
#  БЛОК 2: ЗАВАНТАЖЕННЯ ДАНИХ
#  DataFrame → List[Order]  (Transformer)
#  (патерн з restaurant_analysis.ipynb — Частина 4)
# ─────────────────────────────────────────────────────────────────────────────
_DAY_UA  = {"Thur": "Четвер", "Fri": "П'ятниця", "Sat": "Субота", "Sun": "Неділя"}
_TIME_UA = {"Lunch": "Обід", "Dinner": "Вечеря"}

DAY_COLORS = {
    "Thur": "#3b82f6",
    "Fri":  "#8b5cf6",
    "Sat":  "#f5a623",
    "Sun":  "#2ecc71",
}

COLORS = {
    "bg":     "#0f1117",
    "card":   "#1a1d27",
    "card2":  "#1e2130",
    "gold":   "#f5a623",
    "green":  "#2ecc71",
    "blue":   "#3b82f6",
    "purple": "#8b5cf6",
    "red":    "#ef4444",
    "text":   "#e2e8f0",
    "muted":  "#94a3b8",
    "border": "#2d3748",
}


def load_orders() -> list[Order]:
    """
    Transformer: завантажує seaborn tips і перетворює кожен рядок
    DataFrame на Order (NamedTuple).

    Це той самий патерн що в restaurant_analysis.ipynb — Частина 4:
      orders = [Order(...) for _, row in tips_df.iterrows()]
    """
    tips_df = sns.load_dataset("tips")
    return [
        Order(
            total_bill = float(row["total_bill"]),
            tip        = float(row["tip"]),
            sex        = str(row["sex"]),
            smoker     = str(row["smoker"]),
            day        = str(row["day"]),
            time       = str(row["time"]),
            size       = int(row["size"]),
        )
        for _, row in tips_df.iterrows()
    ]


# Один раз при старті — завантажуємо всі 244 чеки
ALL_ORDERS: list[Order] = load_orders()


# ─────────────────────────────────────────────────────────────────────────────
#  БЛОК 3: ПРЕДИКАТИ (Predicates)
#  notes_functions.ipynb — Частина 7: «Фейсконтроль»
#  Чиста функція → True / False
# ─────────────────────────────────────────────────────────────────────────────
def pred_day(order: Order, days: list[str]) -> bool:
    """Предикат: чи входить день чека до вибраних днів."""
    return order.day in days


def pred_time(order: Order, times: list[str]) -> bool:
    """Предикат: обід / вечеря / обидва."""
    return order.time in times


def pred_smoker(order: Order, smoker: list[str]) -> bool:
    """Предикат: курці / некурці / всі."""
    return order.smoker in smoker


def pred_size(order: Order, lo: int, hi: int) -> bool:
    """Предикат: розмір столу в діапазоні [lo, hi]."""
    return lo <= order.size <= hi


def pred_bill(order: Order, lo: float, hi: float) -> bool:
    """Предикат: сума рахунку в діапазоні [lo, hi]."""
    return lo <= order.total_bill <= hi


def pred_sex(order: Order, sexes: list[str]) -> bool:
    """Предикат: чи входить стать клієнта до вибраних."""
    return order.sex in sexes


def apply_filters(
    orders:     list[Order],
    days:       list[str],
    times:      list[str],
    smoker:     list[str],
    size_range: list[int],
    bill_range: list[float],
    sexes:      list[str],
) -> list[Order]:
    """
    Комбінує всі предикати через AND — залишає тільки потрібні чеки.
    Патерн: [x for x in data if predicate(x)]  (notes_functions.ipynb — Ч.7)
    """
    lo_s, hi_s = size_range
    lo_b, hi_b = bill_range
    return [
        o for o in orders
        if pred_day(o, days)
        and pred_time(o, times)
        and pred_smoker(o, smoker)
        and pred_size(o, lo_s, hi_s)
        and pred_bill(o, lo_b, hi_b)
        and pred_sex(o, sexes)
    ]


# ─────────────────────────────────────────────────────────────────────────────
#  БЛОК 4: ТРАНСФОРМЕРИ (Transformers)
#  notes_functions.ipynb — Частина 8: «Конвеєр фарбування»
#  len(вхід) == len(вихід), лише форма змінюється
# ─────────────────────────────────────────────────────────────────────────────
def enrich_order(o: Order) -> RichOrder:
    """
    Transformer: Order → RichOrder.
    Додає обчислені поля. Оригінал не змінюється (чиста функція).
    Патерн: [transform(x) for x in data]  (notes_functions.ipynb — Ч.8)
    """
    return RichOrder(
        total_bill      = o.total_bill,
        tip             = o.tip,
        sex             = o.sex,
        smoker          = o.smoker,
        day             = o.day,
        time            = o.time,
        size            = o.size,
        tip_pct         = round((o.tip / o.total_bill) * 100, 1),
        bill_per_person = round(o.total_bill / o.size, 2),
        day_ua          = _DAY_UA.get(o.day, o.day),
        time_ua         = _TIME_UA.get(o.time, o.time),
    )


def enrich_all(orders: list[Order]) -> list[RichOrder]:
    """Застосовує enrich_order до кожного чека — map pattern."""
    return [enrich_order(o) for o in orders]


# ─────────────────────────────────────────────────────────────────────────────
#  БЛОК 5: РЕДЬЮСЕРИ (Reducers)
#  notes_functions.ipynb — Частина 9: «Снігова куля»
#  Багато елементів → одне значення / агрегат
# ─────────────────────────────────────────────────────────────────────────────
def calc_kpis(orders: list[RichOrder]) -> dict:
    """
    Reducer: обчислює ключові показники.
    Використовує вбудовані редьюсери: sum(), max(), len()
    (notes_functions.ipynb — Ч.9)
    """
    if not orders:
        return {"revenue": 0, "tips": 0, "avg_bill": 0,
                "avg_tip_pct": 0, "count": 0, "avg_size": 0}
    bills = [o.total_bill for o in orders]   # ← Transformer (extract)
    tips  = [o.tip        for o in orders]
    sizes = [o.size       for o in orders]
    pcts  = [o.tip_pct    for o in orders]
    return {
        "revenue":     round(sum(bills), 2),        # ← Reducer: sum
        "tips":        round(sum(tips), 2),
        "avg_bill":    round(sum(bills) / len(bills), 2),
        "avg_tip_pct": round(sum(pcts)  / len(pcts),  1),
        "count":       len(orders),
        "avg_size":    round(sum(sizes) / len(sizes), 1),
    }


def group_by_day(orders: list[RichOrder]) -> list[dict]:
    """
    Reducer: групує виручку по днях.
    Patерн Counting+Grouping з restaurant_analysis.ipynb — Ч.6/10.
    """
    from collections import defaultdict
    rev   = defaultdict(float)
    tips  = defaultdict(float)
    cnt   = defaultdict(int)
    for o in orders:
        rev[o.day]  += o.total_bill   # ← d[key] += value
        tips[o.day] += o.tip
        cnt[o.day]  += 1
    return sorted([
        {"day": d, "day_ua": _DAY_UA.get(d, d),
         "revenue": round(rev[d], 2),
         "tips":    round(tips[d], 2),
         "orders":  cnt[d],
         "avg_bill": round(rev[d] / cnt[d], 2) if cnt[d] else 0}
        for d in rev
    ], key=lambda x: x["revenue"], reverse=True)


def group_by_time(orders: list[RichOrder]) -> list[dict]:
    """Reducer: середній tip% і avg чек по Lunch/Dinner."""
    from collections import defaultdict
    tip_pcts = defaultdict(list)
    bills    = defaultdict(list)
    for o in orders:
        tip_pcts[o.time].append(o.tip_pct)
        bills[o.time].append(o.total_bill)
    result = []
    for t in tip_pcts:
        p = tip_pcts[t]
        b = bills[t]
        result.append({
            "time":        t,
            "time_ua":     _TIME_UA.get(t, t),
            "avg_tip_pct": round(sum(p) / len(p), 1),
            "avg_bill":    round(sum(b) / len(b), 2),
            "orders":      len(p),
        })
    return sorted(result, key=lambda x: x["avg_tip_pct"], reverse=True)


def group_by_size(orders: list[RichOrder]) -> list[dict]:
    """Reducer: виручка і avg tip% по розміру столу."""
    from collections import defaultdict
    rev  = defaultdict(float)
    pcts = defaultdict(list)
    cnt  = defaultdict(int)
    for o in orders:
        rev[o.size]  += o.total_bill
        pcts[o.size].append(o.tip_pct)
        cnt[o.size]  += 1
    return sorted([
        {"size":        s,
         "size_label":  f"{s} {'особа' if s == 1 else 'особи' if s <= 4 else 'осіб'}",
         "revenue":     round(rev[s], 2),
         "avg_tip_pct": round(sum(pcts[s]) / len(pcts[s]), 1),
         "orders":      cnt[s]}
        for s in rev
    ], key=lambda x: x["size"])


def group_by_sex(orders: list[RichOrder]) -> list[dict]:
    """Reducer: середній чек і tip% по статі — для pie chart."""
    from collections import defaultdict
    rev  = defaultdict(float)
    pcts = defaultdict(list)
    cnt  = defaultdict(int)
    for o in orders:
        rev[o.sex]  += o.total_bill
        pcts[o.sex].append(o.tip_pct)
        cnt[o.sex]  += 1
    return [
        {"sex":        s,
         "revenue":    round(rev[s], 2),
         "avg_tip_pct": round(sum(pcts[s]) / len(pcts[s]), 1),
         "orders":     cnt[s]}
        for s in rev
    ]


def top_by_tip_pct(orders: list[RichOrder], n: int = 5) -> list[RichOrder]:
    """
    Predicate + Reducer: топ-N чеків за % чайових.
    sorted() → [:n]  (notes_functions.ipynb — Ч.7+9)
    """
    return sorted(orders, key=lambda o: o.tip_pct, reverse=True)[:n]


# ─────────────────────────────────────────────────────────────────────────────
#  БЛОК 6: ПОВНИЙ PIPELINE (Functional Decomposition)
#  notes_functions.ipynb — Частина 10+11
#  Маленькі чисті функції складаються в один оркестратор
# ─────────────────────────────────────────────────────────────────────────────
def run_pipeline(
    days:       list[str],
    times:      list[str],
    smoker:     list[str],
    size_range: list[int],
    bill_range: list[float],
    sexes:      list[str],
) -> dict:
    """
    Головний пайплайн:
      Step 1: Filter   (Predicates)  → List[Order]
      Step 2: Enrich   (Transformer) → List[RichOrder]
      Step 3: Reduce   (Reducers)    → аналітика
    """
    # Step 1: FILTER ─────────────────────────────────────────────────────────
    filtered: list[Order] = apply_filters(
        ALL_ORDERS, days, times, smoker, size_range, bill_range, sexes
    )

    # Step 2: TRANSFORM (enrich) ─────────────────────────────────────────────
    enriched: list[RichOrder] = enrich_all(filtered)   # ← чиста функція

    # Step 3: REDUCE ─────────────────────────────────────────────────────────
    return {
        "count":    len(enriched),
        "enriched": enriched,
        "kpis":     calc_kpis(enriched),
        "by_day":   group_by_day(enriched),
        "by_time":  group_by_time(enriched),
        "by_size":  group_by_size(enriched),
        "by_sex":   group_by_sex(enriched),
        "top_tips": top_by_tip_pct(enriched, n=5),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  БЛОК 7: DASH UI
# ─────────────────────────────────────────────────────────────────────────────
def _label(text: str) -> html.P:
    return html.P(text, style={
        "color": COLORS["muted"], "fontSize": "0.68rem",
        "margin": "0.6rem 0 0.2rem",
        "textTransform": "uppercase", "letterSpacing": "0.07em",
    })


def kpi_card(card_id: str, icon: str, title: str, color: str) -> dbc.Card:
    return dbc.Card(dbc.CardBody([
        html.Div([
            html.Span(icon, style={"fontSize": "1.5rem"}),
            html.Div([
                html.P(title, style={"color": COLORS["muted"], "fontSize": "0.65rem",
                                     "margin": 0, "textTransform": "uppercase",
                                     "letterSpacing": "0.07em"}),
                html.H4("—", id=card_id, style={
                    "color": color, "margin": "0.1rem 0",
                    "fontWeight": 700, "fontSize": "1.45rem",
                }),
            ], style={"marginLeft": "0.5rem"}),
        ], style={"display": "flex", "alignItems": "center"}),
    ]), style={
        "background": COLORS["card"],
        "border": f"1px solid {COLORS['border']}",
        "borderLeft": f"3px solid {color}",
        "borderRadius": "8px",
    })


sidebar = dbc.Card([
    html.Div([
        html.Span("🍽️", style={"fontSize": "1.3rem"}),
        html.H6("ФІЛЬТРИ", style={
            "color": COLORS["gold"], "margin": "0 0 0 0.5rem",
            "fontWeight": 700, "letterSpacing": "0.1em", "fontSize": "0.85rem",
        }),
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "1rem"}),

    _label("📅 День тижня"),
    dcc.Checklist(
        id="f-day",
        options=[{"label": f"  {v}", "value": k}
                 for k, v in _DAY_UA.items()],
        value=list(_DAY_UA.keys()),
        labelStyle={"display": "block", "color": COLORS["text"],
                    "fontSize": "0.82rem", "marginBottom": "0.25rem"},
        inputStyle={"marginRight": "0.4rem", "accentColor": COLORS["gold"]},
    ),
    html.Hr(style={"borderColor": COLORS["border"], "margin": "0.7rem 0"}),

    _label("🕐 Зміна"),
    dcc.Checklist(
        id="f-time",
        options=[{"label": "  Обід (Lunch)",    "value": "Lunch"},
                 {"label": "  Вечеря (Dinner)", "value": "Dinner"}],
        value=["Lunch", "Dinner"],
        labelStyle={"display": "block", "color": COLORS["text"],
                    "fontSize": "0.82rem", "marginBottom": "0.25rem"},
        inputStyle={"marginRight": "0.4rem", "accentColor": COLORS["gold"]},
    ),
    html.Hr(style={"borderColor": COLORS["border"], "margin": "0.7rem 0"}),

    _label("🚬 Курці"),
    dcc.Checklist(
        id="f-smoker",
        options=[{"label": "  Некурці", "value": "No"},
                 {"label": "  Курці",   "value": "Yes"}],
        value=["No", "Yes"],
        labelStyle={"display": "block", "color": COLORS["text"],
                    "fontSize": "0.82rem", "marginBottom": "0.25rem"},
        inputStyle={"marginRight": "0.4rem", "accentColor": COLORS["gold"]},
    ),
    html.Hr(style={"borderColor": COLORS["border"], "margin": "0.7rem 0"}),

    _label("👤 Стать клієнта"),
    dcc.Checklist(
        id="f-sex",
        options=[{"label": "  Чоловік (Male)",   "value": "Male"},
                 {"label": "  Жінка (Female)",   "value": "Female"}],
        value=["Male", "Female"],
        labelStyle={"display": "block", "color": COLORS["text"],
                    "fontSize": "0.82rem", "marginBottom": "0.25rem"},
        inputStyle={"marginRight": "0.4rem", "accentColor": COLORS["gold"]},
    ),
    html.Hr(style={"borderColor": COLORS["border"], "margin": "0.7rem 0"}),

    _label("👥 Кількість гостей"),
    dcc.RangeSlider(
        id="f-size", min=1, max=6, step=1, value=[1, 6],
        marks={i: {"label": str(i), "style": {"color": COLORS["muted"], "fontSize": "0.72rem"}}
               for i in range(1, 7)},
        tooltip={"placement": "bottom", "always_visible": False},
    ),
    html.Hr(style={"borderColor": COLORS["border"], "margin": "0.7rem 0"}),

    _label("💵 Сума рахунку ($)"),
    dcc.RangeSlider(
        id="f-bill", min=0, max=55, step=1, value=[0, 55],
        marks={i: {"label": f"${i}", "style": {"color": COLORS["muted"], "fontSize": "0.72rem"}}
               for i in [0, 15, 30, 45, 55]},
        tooltip={"placement": "bottom", "always_visible": False},
    ),
    html.Hr(style={"borderColor": COLORS["border"], "margin": "0.7rem 0"}),

    dbc.Button("↺ Скинути", id="btn-reset", color="warning",
               outline=True, size="sm", className="w-100"),

    html.P([
        html.Span("List[Order]  ", style={"color": COLORS["gold"], "fontWeight": 600}),
        html.Span("· 244 чеки · seaborn tips", style={"color": COLORS["muted"]}),
    ], style={"fontSize": "0.62rem", "textAlign": "center", "marginTop": "0.9rem"}),

], body=True, style={
    "background": COLORS["card"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "10px",
})

CARD_STYLE = {
    "background": COLORS["card"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "8px",
}
HEADER_STYLE = {
    "background": COLORS["card2"],
    "color": COLORS["gold"],
    "fontSize": "0.78rem",
    "fontWeight": 600,
    "border": "none",
    "padding": "0.5rem 0.9rem",
}


def chart_card(title: str, chart_id: str, height: int = 270) -> dbc.Card:
    return dbc.Card([
        dbc.CardHeader(title, style=HEADER_STYLE),
        dcc.Graph(id=chart_id, config={"displayModeBar": False},
                  style={"height": f"{height}px"}),
    ], style=CARD_STYLE)


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP],
    title="🍽️ Bistro Analytics",
)

app.layout = dbc.Container(fluid=True, style={
    "background": COLORS["bg"], "minHeight": "100vh", "padding": "1rem 1.5rem",
}, children=[

    # ── Шапка ────────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            html.H3("🍽️ Bistro Analytics",
                    style={"color": COLORS["gold"], "margin": 0, "fontWeight": 700}),
            html.P([
                "Система аналітики ресторану · Урок 8 · ",
                html.Code("List[Order]", style={"color": COLORS["blue"],
                                                "fontSize": "0.78rem"}),
                " · Pure Functions · Filter → Map → Reduce",
            ], style={"color": COLORS["muted"], "margin": 0, "fontSize": "0.78rem"}),
        ], width=9),
        dbc.Col(html.Div(id="badge", style={
            "textAlign": "right", "color": COLORS["gold"],
            "fontWeight": 700, "paddingTop": "0.3rem", "fontSize": "0.9rem",
        }), width=3),
    ], className="mb-3 align-items-center",
       style={"borderBottom": f"1px solid {COLORS['border']}", "paddingBottom": "0.8rem"}),

    # ── Основний layout ───────────────────────────────────────────────────────
    dbc.Row([

        # Sidebar
        dbc.Col(sidebar, width=2),

        # Головна панель
        dbc.Col([

            # KPI
            dbc.Row([
                dbc.Col(kpi_card("kpi-revenue", "💰", "Виручка",   COLORS["green"]),  width=3),
                dbc.Col(kpi_card("kpi-tips",    "✨", "Чайові",    COLORS["gold"]),   width=3),
                dbc.Col(kpi_card("kpi-avg",     "🧾", "Avg чек",   COLORS["blue"]),   width=3),
                dbc.Col(kpi_card("kpi-pct",     "📊", "Avg Tip %", COLORS["purple"]), width=3),
            ], className="mb-3"),

            # Ряд 1: Виручка по днях + Lunch vs Dinner
            dbc.Row([
                dbc.Col(chart_card("💹 Виручка по днях тижня",  "ch-day",  270), width=7),
                dbc.Col(chart_card("☕ Обід vs Вечеря · Tip %", "ch-time", 270), width=5),
            ], className="mb-3"),

            # Ряд 2: Scatter + Розмір столу
            dbc.Row([
                dbc.Col(chart_card("🔵 Рахунок vs Чайові (кожен Order)",   "ch-scatter", 280), width=7),
                dbc.Col(chart_card("👥 Розмір столу → Виручка + Avg Tip%", "ch-size",    280), width=5),
            ], className="mb-3"),

            # Ряд 3: Топ + Tip% розподіл + Pie стать
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🏆 Топ-5 за Tip %", style=HEADER_STYLE),
                        html.Div(id="top-table", style={"padding": "0.4rem"}),
                    ], style=CARD_STYLE),
                ], width=4),
                dbc.Col(chart_card("📈 Розподіл Tip % по всіх чеках", "ch-dist",  240), width=5),
                dbc.Col(chart_card("👤 Стать клієнтів",                "ch-sex",   240), width=3),
            ], className="mb-3"),

            # Ряд 4: Таблиця
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Span("📋 Всі чеки · List[RichOrder]",
                                      style={"color": COLORS["gold"],
                                             "fontWeight": 600, "fontSize": "0.78rem"}),
                            html.Span(id="tbl-count",
                                      style={"color": COLORS["muted"],
                                             "fontSize": "0.72rem", "marginLeft": "0.5rem"}),
                        ], style=HEADER_STYLE),
                        html.Div(id="orders-table", style={"padding": "0.4rem"}),
                    ], style=CARD_STYLE),
                ]),
            ]),

        ], width=10),
    ]),
])


# ─────────────────────────────────────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────────────────────────────────────
def _theme(fig: go.Figure) -> go.Figure:
    """Застосовує темну тему до всіх графіків."""
    fig.update_layout(
        paper_bgcolor=COLORS["card"], plot_bgcolor=COLORS["card"],
        font={"color": COLORS["text"], "size": 11},
        xaxis={"gridcolor": COLORS["border"], "linecolor": COLORS["border"],
               "tickfont": {"color": COLORS["muted"]}},
        yaxis={"gridcolor": COLORS["border"], "linecolor": COLORS["border"],
               "tickfont": {"color": COLORS["muted"]}},
        legend={"bgcolor": COLORS["card"], "bordercolor": COLORS["border"],
                "font": {"color": COLORS["text"]}},
        margin={"t": 10, "b": 35, "l": 45, "r": 10},
        hoverlabel={"bgcolor": COLORS["card2"], "font_color": COLORS["text"]},
    )
    return fig


def _empty(msg: str = "Немає чеків для вибраних фільтрів") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5,
                       xref="paper", yref="paper",
                       showarrow=False, font={"color": COLORS["muted"], "size": 12})
    fig.update_layout(
        paper_bgcolor=COLORS["card"], plot_bgcolor=COLORS["card"],
        xaxis={"visible": False}, yaxis={"visible": False},
        margin={"t": 0, "b": 0, "l": 0, "r": 0},
    )
    return fig


def _table(rows: list[dict], columns: list[str],
           conditional: list | None = None) -> dash_table.DataTable:
    return dash_table.DataTable(
        data=[{c: r[c] for c in columns} for r in rows],
        columns=[{"name": c, "id": c} for c in columns],
        style_table={"overflowX": "auto"},
        style_cell={
            "backgroundColor": COLORS["card"], "color": COLORS["text"],
            "border": f"1px solid {COLORS['border']}",
            "fontSize": "0.76rem", "padding": "5px 9px", "textAlign": "center",
        },
        style_header={
            "backgroundColor": COLORS["card2"], "color": COLORS["gold"],
            "fontWeight": 600, "fontSize": "0.7rem",
            "border": f"1px solid {COLORS['border']}",
        },
        style_data_conditional=conditional or [],
        page_size=10, sort_action="native",
        filter_action="native",
        filter_options={"placeholder_text": "Фільтр..."},
    )


@app.callback(
    Output("badge",       "children"),
    Output("kpi-revenue", "children"),
    Output("kpi-tips",    "children"),
    Output("kpi-avg",     "children"),
    Output("kpi-pct",     "children"),
    Output("ch-day",      "figure"),
    Output("ch-time",     "figure"),
    Output("ch-scatter",  "figure"),
    Output("ch-size",     "figure"),
    Output("ch-dist",     "figure"),
    Output("ch-sex",      "figure"),
    Output("top-table",   "children"),
    Output("orders-table","children"),
    Output("tbl-count",   "children"),
    Input("f-day",    "value"),
    Input("f-time",   "value"),
    Input("f-smoker", "value"),
    Input("f-sex",    "value"),
    Input("f-size",   "value"),
    Input("f-bill",   "value"),
)
def update(days, times, smoker, sexes, size_range, bill_range):
    """
    Callback — запускає повний пайплайн при зміні будь-якого фільтра.
    run_pipeline() = Filter → Transform → Reduce.
    """
    data = run_pipeline(
        days       = days       or [],
        times      = times      or [],
        smoker     = smoker     or [],
        size_range = size_range or [1, 6],
        bill_range = bill_range or [0, 55],
        sexes      = sexes      or [],
    )
    enriched: list[RichOrder] = data["enriched"]
    kpis = data["kpis"]
    emp  = not enriched

    badge = f"📋 {kpis['count']} / {len(ALL_ORDERS)} чеків · avg {kpis['avg_size']} ос./стіл"

    if emp:
        e = _empty()
        return (badge, "—", "—", "—", "—",
                e, e, e, e, e, e, "—", "—", "")

    # ── KPI ──────────────────────────────────────────────────────────────────
    kpi_rev = f"${kpis['revenue']:,.0f}"
    kpi_tip = f"${kpis['tips']:,.0f}"
    kpi_avg = f"${kpis['avg_bill']:.2f}"
    kpi_pct = f"{kpis['avg_tip_pct']:.1f}%"

    # ── Chart 1: Виручка по днях (горизонтальний бар) ─────────────────────
    fig_day = go.Figure()
    for row in data["by_day"]:
        fig_day.add_trace(go.Bar(
            y=[row["day_ua"]], x=[row["revenue"]],
            orientation="h",
            marker_color=DAY_COLORS.get(row["day"], COLORS["blue"]),
            name=row["day_ua"],
            hovertemplate=(
                f"<b>{row['day_ua']}</b><br>"
                f"Виручка: ${row['revenue']:.2f}<br>"
                f"Чайові:  ${row['tips']:.2f}<br>"
                f"Чеків:   {row['orders']}<br>"
                f"Avg чек: ${row['avg_bill']:.2f}<extra></extra>"
            ),
        ))
        fig_day.add_annotation(
            y=row["day_ua"], x=row["revenue"] + 3,
            text=f"${row['revenue']:.0f}",
            showarrow=False, xanchor="left",
            font={"color": COLORS["muted"], "size": 10},
        )
    fig_day.update_layout(showlegend=False, barmode="group",
                          xaxis_title="Виручка ($)")
    _theme(fig_day)

    # ── Chart 2: Lunch vs Dinner ─────────────────────────────────────────────
    fig_time = go.Figure()
    tc = {"Lunch": COLORS["blue"], "Dinner": COLORS["gold"]}
    for row in data["by_time"]:
        fig_time.add_trace(go.Bar(
            x=[row["time_ua"]], y=[row["avg_tip_pct"]],
            marker_color=tc.get(row["time"], COLORS["purple"]),
            name=row["time_ua"],
            text=[f"{row['avg_tip_pct']}%"],
            textfont={"color": COLORS["text"]},
            textposition="outside",
            hovertemplate=(
                f"<b>{row['time_ua']}</b><br>"
                f"Avg Tip%%: {row['avg_tip_pct']:.1f}%%<br>"
                f"Avg чек: ${row['avg_bill']:.2f}<br>"
                f"Чеків: {row['orders']}<extra></extra>"
            ),
        ))
    fig_time.update_layout(showlegend=False, barmode="group",
                            yaxis_title="Avg Tip %")
    _theme(fig_time)

    # ── Chart 3: Scatter Рахунок vs Чайові ───────────────────────────────────
    fig_scatter = go.Figure()
    from itertools import groupby
    key = lambda o: o.day
    for day_val, group in groupby(sorted(enriched, key=key), key=key):
        grp = list(group)
        fig_scatter.add_trace(go.Scatter(
            x=[o.total_bill for o in grp],
            y=[o.tip        for o in grp],
            mode="markers",
            name=_DAY_UA.get(day_val, day_val),
            marker={
                "color":   DAY_COLORS.get(day_val, COLORS["blue"]),
                "size":    [o.size * 3.5 for o in grp],
                "opacity": 0.72,
                "line":    {"color": COLORS["bg"], "width": 0.5},
            },
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Рахунок: $%{x:.2f}<br>"
                "Чайові: $%{y:.2f}<br>"
                "Tip%%: %{customdata[1]:.1f}%%<br>"
                "Гості: %{customdata[2]}<extra></extra>"
            ),
            customdata=[(o.day_ua, o.tip_pct, o.size) for o in grp],
        ))
    fig_scatter.update_layout(
        xaxis_title="Сума рахунку ($)", yaxis_title="Чайові ($)",
    )
    _theme(fig_scatter)
    fig_scatter.update_layout(margin={"t": 10, "b": 40, "l": 50, "r": 10})

    # ── Chart 4: Розмір столу ─────────────────────────────────────────────────
    size_rows = data["by_size"]
    fig_size = go.Figure()
    fig_size.add_trace(go.Bar(
        x=[r["size_label"] for r in size_rows],
        y=[r["revenue"]    for r in size_rows],
        marker=dict(
            color=[r["avg_tip_pct"] for r in size_rows],
            colorscale=[[0, COLORS["blue"]], [0.5, COLORS["gold"]], [1, COLORS["green"]]],
            showscale=True,
            colorbar={"title": {"text": "Tip%", "font": {"color": COLORS["muted"]}},
                      "tickfont": {"color": COLORS["muted"]}},
        ),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Виручка: $%{y:.2f}<br>"
            "Avg Tip%%: %{customdata[0]:.1f}%%<br>"
            "Чеків: %{customdata[1]}<extra></extra>"
        ),
        customdata=[(r["avg_tip_pct"], r["orders"]) for r in size_rows],
    ))
    fig_size.update_layout(showlegend=False, yaxis_title="Виручка ($)")
    _theme(fig_size)

    # ── Chart 5: Розподіл Tip % ───────────────────────────────────────────────
    tip_pcts = [o.tip_pct for o in enriched]
    avg_p    = sum(tip_pcts) / len(tip_pcts)
    fig_dist = go.Figure(go.Histogram(
        x=tip_pcts, nbinsx=22,
        marker_color=COLORS["purple"], opacity=0.82,
        hovertemplate="Tip%%: %{x:.1f}%%<br>Чеків: %{y}<extra></extra>",
    ))
    fig_dist.add_vline(x=avg_p, line_dash="dash", line_color=COLORS["gold"],
                       annotation_text=f"  avg {avg_p:.1f}%",
                       annotation_font_color=COLORS["gold"])
    fig_dist.update_layout(showlegend=False,
                            xaxis_title="Tip %", yaxis_title="Чеків")
    _theme(fig_dist)

    # ── Chart 6: Стать (pie) ──────────────────────────────────────────────────
    sex_rows = data["by_sex"]
    fig_sex  = go.Figure(go.Pie(
        labels=[r["sex"] for r in sex_rows],
        values=[r["revenue"] for r in sex_rows],
        hole=0.45,
        marker={"colors": [COLORS["blue"], COLORS["gold"]],
                "line":   {"color": COLORS["bg"], "width": 2}},
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Виручка: $%{value:.2f}<br>"
            "Частка: %{percent}<extra></extra>"
        ),
        textfont={"color": COLORS["text"]},
    ))
    fig_sex.update_layout(showlegend=True, margin={"t": 5, "b": 5, "l": 5, "r": 5})
    _theme(fig_sex)
    fig_sex.update_layout(xaxis={"visible": False}, yaxis={"visible": False})

    # ── Топ-5 таблиця ─────────────────────────────────────────────────────────
    top = data["top_tips"]
    top_tbl = _table(
        rows=[{
            "День": o.day_ua, "Зміна": o.time_ua, "Гості": o.size,
            "Рахунок ($)": o.total_bill, "Чайові ($)": o.tip,
            "Tip %": o.tip_pct,
        } for o in top],
        columns=["День", "Зміна", "Гості", "Рахунок ($)", "Чайові ($)", "Tip %"],
        conditional=[{"if": {"column_id": "Tip %"}, "color": COLORS["green"], "fontWeight": 700}],
    )

    # ── Таблиця всіх чеків ────────────────────────────────────────────────────
    all_tbl = _table(
        rows=[{
            "День": o.day_ua, "Зміна": o.time_ua,
            "Гості": o.size,  "Стать": o.sex, "Курці": o.smoker,
            "Рахунок ($)": o.total_bill, "Чайові ($)": o.tip,
            "Tip %": o.tip_pct, "$/особу": o.bill_per_person,
        } for o in enriched],
        columns=["День", "Зміна", "Гості", "Стать", "Курці",
                 "Рахунок ($)", "Чайові ($)", "Tip %", "$/особу"],
        conditional=[
            {"if": {"filter_query": "{Tip %} > 20"},
             "color": COLORS["green"]},
            {"if": {"filter_query": "{Tip %} < 10"},
             "color": COLORS["red"]},
            {"if": {"column_id": "Зміна",
                    "filter_query": '{Зміна} = "Вечеря"'},
             "color": COLORS["gold"]},
        ],
    )
    tbl_count = f"— {kpis['count']} записів"

    return (badge, kpi_rev, kpi_tip, kpi_avg, kpi_pct,
            fig_day, fig_time, fig_scatter, fig_size, fig_dist, fig_sex,
            top_tbl, all_tbl, tbl_count)


@app.callback(
    Output("f-day",    "value"),
    Output("f-time",   "value"),
    Output("f-smoker", "value"),
    Output("f-sex",    "value"),
    Output("f-size",   "value"),
    Output("f-bill",   "value"),
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset(_):
    return list(_DAY_UA.keys()), ["Lunch", "Dinner"], ["No", "Yes"], ["Male", "Female"], [1, 6], [0, 55]


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  🍽️  Bistro Analytics запущено!")
    print(f"  📦 Завантажено: {len(ALL_ORDERS)} Order objects")
    print("  🔗 http://127.0.0.1:8050")
    print("=" * 60 + "\n")
    app.run(debug=True)
