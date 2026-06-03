import streamlit as st
from pathlib import Path
import sys
import time

sys.path.append(str(Path(__file__).parent.parent))

from core.analyzer import (
    DataLoader,
    METRIC_REGISTRY,
    TRANSFORM_PIPELINE,
    SalesAnalyzer
)

# ─────────────────────────
# CONFIG
# ─────────────────────────

st.set_page_config(layout="wide")
st.title("📊 Аналітична лабораторія")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "amazon_ecommerce_1M.csv"
INR_TO_USD = 1 / 83

# ─────────────────────────
# CONTROLLER
# ─────────────────────────

class AnalyzerController:

    def __init__(self, sales, returns):
        self.sales = sales
        self.returns = returns

        if "cache" not in st.session_state:
            st.session_state["cache"] = {}

        self.sales._cache = st.session_state["cache"]

    # ─────────────────────────
    def render_status(self):
        st.subheader("📌 Стан даних")
        st.json(self.sales.status())
        st.divider()

    # ─────────────────────────
    def render_metrics(self):
        """
        Інтерактивний блок обчислення метрик.

        Цей блок дозволяє користувачу обирати, які саме аналітичні
        показники (метрики) потрібно розрахувати для датасету.

        ─────────────────────────
        🔷 Концепція метрик:
        ─────────────────────────
        Метрика — це функція, яка обчислює певний показник
        на основі даних.

        Приклади:
            • середній чек
            • рівень повернень
            • загальна виручка
            • середній рейтинг

        ─────────────────────────
        🔷 Як це працює:
        ─────────────────────────
        1. Існує реєстр метрик (METRIC_REGISTRY)
           → список пар (назва, функція)

        2. Користувач обирає метрики через інтерфейс (multiselect)

        3. Формується список обраних функцій

        4. Викликається метод run_metrics(),
           який обчислює всі обрані метрики

        5. Результати відображаються у вигляді KPI-блоків

        ─────────────────────────
        🔷 Ключова ідея:
        ─────────────────────────
        Функції є об'єктами.

        Це означає, що:
            • їх можна зберігати у списку
            • передавати як аргументи
            • викликати динамічно

        ─────────────────────────
        🔷 Навчальна мета:
        ─────────────────────────
        Демонструє:

            • функціональне програмування
                (функції як об'єкти)

            • динамічний вибір логіки
                (користувач вирішує, що рахувати)

            • абстракцію аналітики
                (логіка відділена від UI)

        ─────────────────────────
        🔷 Архітектурна ідея:
        ─────────────────────────
        UI не знає, як рахуються метрики.

        Він лише:
            • передає список функцій
            • отримує результати

        Вся логіка знаходиться в Analyzer (core layer).
        """
        st.subheader("📈 Метрики")

        metric_names = [name for name, _ in METRIC_REGISTRY]

        selected = st.multiselect(
            "Оберіть метрики",
            metric_names,
            default=metric_names[:3]
        )

        selected_metrics = [
            (name, func)
            for name, func in METRIC_REGISTRY
            if name in selected
        ]

        metrics = self.sales.run_metrics(selected_metrics)

        cols = st.columns(3)
        for i, (name, value) in enumerate(metrics.items()):
            cols[i % 3].metric(name, value)

        st.divider()

    # ─────────────────────────
    def render_pipeline(self):
        """
        Інтерактивний pipeline обробки даних.

        Цей блок дозволяє користувачу динамічно сформувати послідовність
        кроків обробки даних (pipeline) та застосувати її до датасету.

        ─────────────────────────
        🔷 Концепція pipeline:
        ─────────────────────────
        Pipeline — це впорядкований список функцій перетворення.

        Кожна функція:
            • приймає DataFrame
            • повертає змінений DataFrame

        Приклад:
            df → фільтр → додавання колонки → створення прапорця → результат

        ─────────────────────────
        🔷 Як це працює:
        ─────────────────────────
        1. Користувач обирає кроки обробки (через checkbox)
        2. Формується список функцій (pipeline)
        3. Дані проходять через кожну функцію послідовно
        4. Виводиться результат після всіх перетворень

        ─────────────────────────
        🔷 Ключова ідея:
        ─────────────────────────
        Функції в Python є об'єктами.

        Це означає, що:
            • їх можна зберігати в списку
            • передавати як аргументи
            • виконувати динамічно

        ─────────────────────────
        🔷 Навчальна мета:
        ─────────────────────────
        Цей блок демонструє:

            • функціональне програмування
                (функції як об'єкти)

            • pipeline-підхід
                (послідовна обробка даних)

            • потік трансформації даних
                (як дані змінюються крок за кроком)

        """
        st.subheader("⚙️ Pipeline")

        st.info("Pipeline = послідовність обробки даних")

        use_delivered = st.checkbox("Тільки доставлені", True)
        use_band = st.checkbox("Додати категорії доходу")
        use_late = st.checkbox("Позначити затримку")

        pipeline = []

        if use_delivered:
            pipeline.append(TRANSFORM_PIPELINE[0])
        if use_band:
            pipeline.append(TRANSFORM_PIPELINE[1])
        if use_late:
            pipeline.append(TRANSFORM_PIPELINE[2])

        df = self.sales.run_pipeline(pipeline)

        st.dataframe(df.head(50), use_container_width=True)
        st.divider()
        # ─────────────────────────
        # 📊 АНАЛІЗ ПІСЛЯ PIPELINE
        # ─────────────────────────

        st.markdown("## 📊 Аналіз після pipeline")

        # 🧠 Пояснення
        st.info("""
        Pipeline змінює дані → графіки показують, що саме змінилось
        """)

        # ─────────────────────────
        # 1. 💰 КАТЕГОРІЇ ДОХОДУ
        # ─────────────────────────
        if "revenue_band" in df.columns:
            st.markdown("### 💰 Розподіл замовлень по категоріях доходу")

            band_counts = df["revenue_band"].value_counts()

            st.bar_chart(band_counts)

        # ─────────────────────────
        # 2. 🚚 ЗАТРИМКИ ДОСТАВКИ
        # ─────────────────────────
        if "is_late" in df.columns:
            st.markdown("### 🚚 Частка затримок доставки")

            late_counts = df["is_late"].value_counts()

            st.plotly_chart({
                "data": [{
                    "labels": ["Вчасно", "Затримка"],
                    "values": late_counts.values,
                    "type": "pie"
                }]
            })

        # ─────────────────────────
        # 3. 📈 ТРЕНД ПО ДАТАХ
        # ─────────────────────────
        if "purchase_date" in df.columns:
            st.markdown("### 📈 Динаміка замовлень")

            trend = df.groupby("purchase_date").size()

            st.line_chart(trend)

        # ─────────────────────────
        # 4. 📊 РОЗПОДІЛ ЦІН
        # ─────────────────────────
        import matplotlib.pyplot as plt

        st.markdown("### 📊 Розподіл цін")

        fig, ax = plt.subplots()

        ax.hist(df["final_price"], bins=30)
        ax.set_xlabel("Ціна")
        ax.set_ylabel("Кількість")

        st.pyplot(fig)

        st.divider()

    # ─────────────────────────
    def render_charts(self):
        st.subheader("📊 Аналітика даних")

        # ─────────────────────────
        # 1. ВИРУЧКА ПО КАТЕГОРІЯХ
        # ─────────────────────────
        st.markdown("### 💰 Виручка по категоріях")

        start = time.time()
        revenue = self.sales.revenue_by_category()
        end = time.time()

        st.write(f"⏱ Час: {round(end - start, 3)} сек")
        st.bar_chart(revenue)

        # ─────────────────────────
        # 2. PIE CHART (ЧАСТКА)
        # ─────────────────────────
        st.markdown("### 🥧 Частка виручки по категоріях")

        revenue_df = revenue.reset_index()
        revenue_df.columns = ["Категорія", "Виручка"]

        st.dataframe(revenue_df)

        st.write("Кожна категорія займає частину загальної виручки")

        st.plotly_chart({
            "data": [{
                "labels": revenue_df["Категорія"],
                "values": revenue_df["Виручка"],
                "type": "pie"
            }]
        })

        # ─────────────────────────
        # 3. ТОП БРЕНДІВ
        # ─────────────────────────
        st.markdown("### 🏆 Топ брендів")

        brands = self.sales.top_brands_by_revenue()
        st.bar_chart(brands)

        # ─────────────────────────
        # 4. ТРЕНД ПО ЧАСУ
        # ─────────────────────────
        st.markdown("### 📈 Тренд виручки по місяцях")

        trend = self.sales.monthly_revenue_trend()
        st.line_chart(trend)

        # ─────────────────────────
        # 5. РОЗПОДІЛ ЦІНИ
        # ─────────────────────────
        import matplotlib.pyplot as plt

        st.markdown("### 📊 Розподіл цін (histogram)")

        fig, ax = plt.subplots()

        ax.hist(self.sales._df["final_price"], bins=50)
        ax.set_xlabel("Ціна")
        ax.set_ylabel("Кількість")

        st.pyplot(fig)

        # ─────────────────────────
        # 6. ЗАЛЕЖНІСТЬ (SCATTER)
        # ─────────────────────────
        st.markdown("### 🔗 Залежність: рейтинг vs ціна")

        st.info("Чи дорожчі товари мають кращий рейтинг?")

        df = self.sales._df.sample(1000)

        st.scatter_chart(
            df,
            x="final_price",
            y="rating"
        )

        st.divider()

    # ─────────────────────────
    def render_simulation(self):
        """
        Інтерактивний блок симуляції (what-if analysis).

        Цей блок дозволяє змінювати параметри даних та
        миттєво бачити, як це впливає на результати аналітики.

        ─────────────────────────
        🔷 Концепція симуляції:
        ─────────────────────────
        Симуляція — це зміна вхідних даних з метою
        аналізу впливу на вихідні показники.

        Приклад:
            "Що буде, якщо збільшити знижки?"

        ─────────────────────────
        🔷 Як це працює:
        ─────────────────────────
        1. Користувач змінює параметр (знижку через slider)

        2. Створюється копія даних
            → щоб не змінювати оригінальний датасет

        3. У копії змінюється значення поля discount

        4. Створюється новий аналітичний об'єкт (SalesAnalyzer)

        5. Обчислюється метрика (середній чек)

        6. Результат показується користувачу

        ─────────────────────────
        🔷 Ключова ідея:
        ─────────────────────────
        Дані ≠ модель

        Ми не змінюємо модель,
        ми змінюємо вхідні дані і дивимось результат.

        ─────────────────────────
        🔷 Навчальна мета:
        ─────────────────────────
        Демонструє:

            • сценарний аналіз (what-if)
            • вплив параметрів на результат
            • ізоляцію даних (copy vs original)
            • повторне використання аналітичної логіки

        ─────────────────────────
        🔷 Архітектурна ідея:
        ─────────────────────────
        Ми створюємо новий Analyzer на змінених даних.

        Це означає:
            • логіка не змінюється
            • змінюється тільки вхід

        Такий підхід використовується в:
            • Data Science
            • бізнес-аналітиці
            • фінансовому моделюванні
        """
        st.subheader("🧪 Симуляція. Що буде, якщо змінити знижку?")

        # ─────────────────────────
        # 🎛 ПАРАМЕТР
        # ─────────────────────────
        discount = st.slider("Збільшити знижку (%)", 0, 50, 0)

        # ─────────────────────────
        # 📦 КОПІЯ ДАНИХ
        # ─────────────────────────
        df_sim = self.sales._df.copy()

        # 🔥 змінюємо ціну
        df_sim["final_price"] = df_sim["final_price"] * (1 - discount / 100)

        # ─────────────────────────
        # 🧠 АНАЛІЗ
        # ─────────────────────────
        sim = SalesAnalyzer(df_sim)

        selected_metrics = [
            METRIC_REGISTRY[0],  # AOV
            METRIC_REGISTRY[2],  # Revenue
            METRIC_REGISTRY[1],  # Return Rate
        ]

        original_metrics = self.sales.run_metrics(selected_metrics)
        sim_metrics = sim.run_metrics(selected_metrics)

        # ─────────────────────────
        # 📊 KPI (було vs стало)
        # ─────────────────────────
        st.markdown("### 📊 Вплив зміни знижки на ключові метрики")

        cols = st.columns(len(original_metrics))

        for i, key in enumerate(original_metrics.keys()):
            before = original_metrics[key]
            after = sim_metrics[key]

            delta = after - before

            # якщо це гроші → переводимо
            if "₹" in key or "Revenue" in key or "Value" in key:
                after = after * INR_TO_USD
                delta = delta * INR_TO_USD
                label = key.replace("₹", "$")
            else:
                label = key

            cols[i].metric(
                label=label,
                value=round(after, 2),
                delta=round(delta, 2)
            )

        # ─────────────────────────
        # 💰 ОКРЕМО ДОХІД (чіткий сигнал)
        # ─────────────────────────
        revenue_before = original_metrics["Total Revenue (₹)"] * INR_TO_USD
        revenue_after = sim_metrics["Total Revenue (₹)"] * INR_TO_USD

        st.metric(
            label="Загальний дохід ($)",
            value=round(revenue_after, 2),
            delta=round(revenue_after - revenue_before, 2)
        )

        st.markdown("### 💰 Вплив на дохід")

        st.metric(
            label="Загальний дохід",
            value=round(revenue_after, 2),
            delta=round(revenue_after - revenue_before, 2)
        )

        # ─────────────────────────
        # 📊 BAR CHART (правильна візуалізація)
        # ─────────────────────────
        import pandas as pd

        df_compare = pd.DataFrame({
            "Сценарій": ["Базовий", "Зі знижкою"],
            "Виручка ($)": [revenue_before, revenue_after]
        })

        st.bar_chart(df_compare.set_index("Сценарій"))

        st.divider()

    # ─────────────────────────
    def render_explainability(self):
        st.subheader("🔍 Як це рахується")

        st.info("Пояснення логіки розрахунків")

        with st.expander("Виручка по категоріях"):
            st.write("Кроки:")
            st.write("1. Беремо тільки доставлені замовлення")
            st.write("2. Групуємо по категоріях")
            st.write("3. Сумуємо ціни")

            st.code("""
df[df['delivery_status'] == 'Delivered']
  .groupby('category')['final_price']
  .sum()
""")

        st.divider()

    # ─────────────────────────
    def render_cache(self):
        st.subheader("🧠 Cache")

        if not self.sales._cache:
            st.warning("Ще нічого не закешовано")
        else:
            for key in self.sales._cache:
                st.success(f"✔ {key}")

        st.divider()


# ─────────────────────────
# RUN
# ─────────────────────────

with DataLoader(DATA_PATH) as (sales, returns):

    controller = AnalyzerController(sales, returns)

    controller.render_status()
    controller.render_metrics()
    controller.render_pipeline()
    controller.render_charts()
    controller.render_simulation()
    controller.render_explainability()
    controller.render_cache()

