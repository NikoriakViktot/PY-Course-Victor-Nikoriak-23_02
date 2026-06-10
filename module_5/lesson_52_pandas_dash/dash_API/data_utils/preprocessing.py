# =============================================================================
# data_utils/preprocessing.py — Аналітичні функції обробки даних
# =============================================================================
# Цей модуль містить всі функції для:
#   - фільтрації та агрегації цін на продукти
#   - підготовки часових рядів обмінного курсу
#   - роботи з макроекономічними індикаторами
#   - підготовки геопросторових даних для карт
#   - об'єднання (join) датасетів з валідацією
#
# ПРИНЦИПИ:
#   1. Кожна функція приймає датафрейм явно — без прихованих глобальних залежностей
#   2. Агрегація виконується тільки після фільтрації за товаром + одиницею
#   3. Методологічні обмеження задокументовані безпосередньо у функціях
# =============================================================================

import pandas as pd
import numpy as np
from typing import Optional


# =============================================================================
# БЛОК 1: Функції для аналізу цін на продукти харчування
# =============================================================================

def filter_food(
    df: pd.DataFrame,
    commodity: Optional[str] = None,
    unit: Optional[str] = None,
    oblast: Optional[str] = None,
    start_date=None,
    end_date=None,
    exclude_national_average: bool = True,
) -> pd.DataFrame:
    """
    Фільтрує датасет цін на продукти харчування за заданими параметрами.

    Параметри:
        df                       — вихідний датафрейм food (після load_food)
        commodity                — назва товару (наприклад, 'Sugar')
        unit                     — одиниця виміру (наприклад, 'KG')
        oblast                   — назва області (наприклад, 'Kyivska')
        start_date               — початок діапазону дат
        end_date                 — кінець діапазону дат
        exclude_national_average — чи виключати рядки з ринком 'National Average'
                                   (True = тільки реальні регіональні ринки)

    Повертає:
        Відфільтрований pd.DataFrame

    МЕТОДОЛОГІЧНА ПРИМІТКА:
        Параметри commodity та unit завжди повинні вказуватися разом,
        оскільки один і той самий товар може мати різні одиниці виміру
        (наприклад, 'Butter' продається і в KG, і в 200G).
        Змішування одиниць у агрегаціях є науково некоректним.
    """
    dff = df.copy()

    # Виключаємо "National Average" — це попередньо обчислений WFP показник,
    # а не реальний ринок; для регіонального аналізу він не підходить
    if exclude_national_average:
        dff = dff[dff["ринок"] != "National Average"]

    # Фільтр за товаром
    if commodity:
        dff = dff[dff["товар"] == commodity]

    # Фільтр за одиницею виміру — ОБОВ'ЯЗКОВИЙ при агрегації!
    if unit:
        dff = dff[dff["одиниця"] == unit]

    # Фільтр за областю
    if oblast and oblast != "Всі":
        dff = dff[dff["область"] == oblast]

    # Фільтр за діапазоном дат
    if start_date:
        dff = dff[dff["дата"] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff["дата"] <= pd.to_datetime(end_date)]

    return dff


def get_units_for_commodity(df: pd.DataFrame, commodity: str) -> list[str]:
    """
    Повертає список одиниць виміру, що наявні для обраного товару.

    Чому це потрібно:
        Деякі товари мають декілька одиниць виміру в датасеті
        (наприклад, Milk: 'KG' та 'L'; Bread (rye): 'KG' та 'Loaf').
        Перш ніж будувати будь-яку агрегацію, користувач МУСИТЬ обрати
        конкретну одиницю, щоб уникнути порівняння непорівнянних цін.
    """
    return sorted(df[df["товар"] == commodity]["одиниця"].dropna().unique().tolist())


def get_food_timeseries(
    df: pd.DataFrame,
    commodity: str,
    unit: str,
    oblast: Optional[str] = None,
    freq: str = "ME",
) -> pd.DataFrame:
    """
    Обчислює медіанну ціну обраного товару по місяцях.

    Параметри:
        df        — відфільтрований датафрейм food
        commodity — назва товару
        unit      — одиниця виміру
        oblast    — якщо задано, аналізується тільки ця область
        freq      — частота агрегації ('ME' = кінець місяця, 'QE' = квартал)

    Повертає:
        DataFrame з колонками: дата, медіана_ціни, середня_ціна, n_спостережень

    Чому медіана, а не середнє:
        Ціни на одному ринку можуть бути аномальними (recording errors).
        Медіана є робастнішою мірою центральної тенденції для таких даних.
        Середнє також наводиться для порівняння.
    """
    dff = filter_food(df, commodity=commodity, unit=unit, oblast=oblast)

    if dff.empty:
        return pd.DataFrame(columns=["дата", "медіана_ціни", "середня_ціна", "n"])

    # Агрегуємо по місяцях — беремо медіану та середнє по всіх ринках
    result = (
        dff.set_index("дата")["ціна"]
        .resample(freq)
        .agg(медіана_ціни="median", середня_ціна="mean", n="count")
        .reset_index()
    )

    # Назва для підпису на графіку
    result["товар_одиниця"] = f"{commodity} ({unit})"

    return result


def get_oblast_prices(
    df: pd.DataFrame,
    commodity: str,
    unit: str,
) -> pd.DataFrame:
    """
    Обчислює медіанну ціну по кожній області для порівняльного аналізу.

    Параметри:
        df        — датафрейм food
        commodity — назва товару
        unit      — одиниця виміру

    Повертає:
        DataFrame з колонками: область, медіана_ціни, середня_ціна, n

    МЕТОДОЛОГІЧНЕ ОБМЕЖЕННЯ:
        Охоплення ринків суттєво відрізняється між областями
        та може змінюватися з часом. Область з меншою кількістю ринків
        матиме менш репрезентативну оцінку. Завжди перевіряйте n.
    """
    dff = filter_food(df, commodity=commodity, unit=unit)

    if dff.empty:
        return pd.DataFrame(columns=["область", "медіана_ціни", "середня_ціна", "n"])

    # Виключаємо рядки без назви області
    dff = dff.dropna(subset=["область"])

    result = (
        dff.groupby("область")["ціна"]
        .agg(медіана_ціни="median", середня_ціна="mean", n="count")
        .reset_index()
        .sort_values("медіана_ціни", ascending=False)
    )

    return result


def get_oblast_variability(
    df: pd.DataFrame,
    commodity: str,
    unit: str,
) -> pd.DataFrame:
    """
    Повертає всі індивідуальні цінові спостереження по областях
    для побудови box plot або violin plot.

    Box plot показує:
        - медіану (горизонтальна лінія в середині)
        - міжквартильний розмах IQR (тіло ящика: Q1–Q3)
        - "вуса" (1.5 * IQR)
        - викиди (точки поза вусами)

    Це дає повну картину розподілу цін без втрати інформації,
    на відміну від простого середнього.
    """
    dff = filter_food(df, commodity=commodity, unit=unit)
    return dff.dropna(subset=["область", "ціна"])


def get_top_oblasts(
    df: pd.DataFrame,
    commodity: str,
    unit: str,
    n: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Повертає топ-n найдорожчих та найдешевших областей за медіаною ціни.

    Повертає:
        (expensive_df, cheap_df) — кортеж з двох датафреймів
    """
    oblast_prices = get_oblast_prices(df, commodity, unit)

    if oblast_prices.empty:
        empty = pd.DataFrame(columns=["область", "медіана_ціни"])
        return empty, empty

    # Фільтруємо регіони з достатньою кількістю спостережень (мін. 5)
    # Це запобігає появі "найдешевшого регіону" з 1 спостереженням
    reliable = oblast_prices[oblast_prices["n"] >= 5]

    expensive = reliable.nlargest(n, "медіана_ціни")
    cheap     = reliable.nsmallest(n, "медіана_ціни")

    return expensive, cheap


def get_food_summary_stats(
    df: pd.DataFrame,
    commodity: str,
    unit: str,
) -> pd.DataFrame:
    """
    Обчислює зведену таблицю описової статистики для обраного товару.

    Включає: мінімум, Q1, медіану, середнє, Q3, максимум, стандартне відхилення.
    """
    dff = filter_food(df, commodity=commodity, unit=unit)

    if dff.empty:
        return pd.DataFrame()

    stats = dff["ціна"].describe(percentiles=[0.25, 0.5, 0.75])

    return pd.DataFrame({
        "Показник": [
            "Кількість спостережень",
            "Мінімальна ціна",
            "1-й квартиль (Q1)",
            "Медіана",
            "3-й квартиль (Q3)",
            "Максимальна ціна",
            "Середня ціна",
            "Стандартне відхилення",
        ],
        "Значення (UAH)": [
            int(stats["count"]),
            round(stats["min"], 2),
            round(stats["25%"], 2),
            round(stats["50%"], 2),
            round(stats["75%"], 2),
            round(stats["max"], 2),
            round(stats["mean"], 2),
            round(stats["std"], 2),
        ],
    })


# =============================================================================
# БЛОК 2: Функції для аналізу обмінного курсу
# =============================================================================

def get_exchange_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Повертає повний місячний ряд курсу UAH/USD, готовий для побудови графіка.

    Датасет вже відфільтрований у load_exchange() — тут просто
    перевіряємо цілісність і повертаємо.
    """
    dff = df.dropna(subset=["дата", "курс"]).copy()
    return dff.sort_values("дата")


def get_exchange_monthly_for_year_range(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """
    Фільтрує курс UAH/USD за заданим діапазоном років.

    Параметри:
        df         — датафрейм exchange (після load_exchange)
        start_year — початковий рік
        end_year   — кінцевий рік
    """
    dff = df[(df["рік"] >= start_year) & (df["рік"] <= end_year)].copy()
    return dff.sort_values("дата")


# =============================================================================
# БЛОК 3: Функції для аналізу зовнішнього боргу / макроіндикаторів
# =============================================================================

def get_debt_indicators(df: pd.DataFrame) -> list[str]:
    """
    Повертає відсортований список усіх доступних макроекономічних індикаторів.

    Примітка: 59 індикаторів мають РІЗНУ економічну природу та одиниці виміру.
    Порівнювати їх між собою без методологічного обґрунтування некоректно.
    """
    return sorted(df["індикатор"].dropna().unique().tolist())


def get_debt_timeseries(
    df: pd.DataFrame,
    indicator: str,
) -> pd.DataFrame:
    """
    Повертає часовий ряд обраного макроекономічного індикатора.

    Параметри:
        df        — датафрейм debt (після load_debt)
        indicator — повна назва індикатора зі списку get_debt_indicators()

    Повертає:
        DataFrame з колонками: рік, значення
    """
    dff = df[df["індикатор"] == indicator].copy()
    dff = dff.dropna(subset=["рік", "значення"])
    return dff[["рік", "значення"]].sort_values("рік")


def get_debt_indicator_code(df: pd.DataFrame, indicator: str) -> str:
    """Повертає код Світового банку для обраного індикатора."""
    row = df[df["індикатор"] == indicator].head(1)
    if row.empty:
        return ""
    return row["код_індикатора"].iloc[0]


# =============================================================================
# БЛОК 4: Геопросторові функції — карти ринків
# =============================================================================

def join_food_to_markets(
    food_df: pd.DataFrame,
    markets_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Об'єднує датафрейм цін на продукти з довідником ринків за market_id.

    ЧОМУ ЦЕЙ JOIN ВАЛІДНИЙ:
        1. id_ринку з food_prices та id_ринку з markets — один і той самий WFP ID
        2. Аудит показав: всі 268 id_ринку з food_prices ПРИСУТНІ в markets
        3. Markets — довідник, тому використовуємо left join
           (щоб не втратити рядки, якщо ринок є в food але не в markets)

    Після join датафрейм food збагачується координатами та назвами
    з довідника markets. Це потрібно для карти, де food_prices може мати
    null-координати (наприклад, 'National Average').

    Повертає:
        DataFrame з усіма колонками food + 'широта_ринку', 'довгота_ринку',
        'назва_ринку_ref' (з довідника, на випадок розбіжностей)
    """
    # Беремо тільки потрібні колонки з довідника — уникаємо конфліктів назв
    markets_slim = markets_df[["id_ринку", "широта", "довгота"]].rename(columns={
        "широта": "широта_ref",
        "довгота": "довгота_ref",
    })

    # Left join: всі рядки food зберігаються
    merged = food_df.merge(markets_slim, on="id_ринку", how="left")

    # Якщо в food є власні координати — використовуємо їх;
    # якщо ні (NaN) — беремо з довідника markets
    merged["широта_карта"] = merged["широта"].combine_first(merged["широта_ref"])
    merged["довгота_карта"] = merged["довгота"].combine_first(merged["довгота_ref"])

    return merged


def prepare_point_map_data(
    food_df: pd.DataFrame,
    markets_df: pd.DataFrame,
    commodity: str,
    unit: str,
) -> pd.DataFrame:
    """
    Підготовлює датасет для точкової карти ринків.

    Логіка:
        1. Фільтруємо за товаром та одиницею (ОБОВ'ЯЗКОВО перед агрегацією)
        2. Виключаємо 'National Average' — він не має координат
        3. Беремо ОСТАННЄ спостереження по кожному ринку
           (найновіша ціна = актуальна ситуація)
        4. Збагачуємо координатами через join

    Повертає:
        DataFrame з колонками:
            id_ринку, ринок, область, широта_карта, довгота_карта,
            ціна, дата, товар, одиниця

    МЕТОДОЛОГІЧНЕ ОБМЕЖЕННЯ:
        Ринки, що не звітували нещодавно, показуватимуть застарілі ціни.
        Перевіряйте дату на tooltip.
    """
    # Фільтр за товаром та одиницею — НІКОЛИ не об'єднуємо різні одиниці
    dff = filter_food(food_df, commodity=commodity, unit=unit)

    if dff.empty:
        return pd.DataFrame()

    # Останнє спостереження по кожному ринку
    latest = (
        dff.sort_values("дата")
        .groupby("id_ринку")
        .last()
        .reset_index()
    )

    # Збагачуємо координатами з довідника
    enriched = join_food_to_markets(latest, markets_df)

    # Залишаємо тільки ринки з наявними координатами
    enriched = enriched.dropna(subset=["широта_карта", "довгота_карта"])

    return enriched[[
        "id_ринку", "ринок", "область", "широта_карта", "довгота_карта",
        "ціна", "дата", "товар", "одиниця"
    ]]


def prepare_oblast_agg_map(
    food_df: pd.DataFrame,
    commodity: str,
    unit: str,
) -> pd.DataFrame:
    """
    Агрегує медіанну ціну по областях для хороплет-карти (choropleth).

    Чому медіана, а не середнє:
        Середнє чутливе до викидів і нерівномірного охоплення ринків.
        Медіана більш стійка до перекошеного розподілу.

    Повертає:
        DataFrame з колонками: область, медіана_ціни, n_спостережень
    """
    dff = filter_food(food_df, commodity=commodity, unit=unit)

    if dff.empty:
        return pd.DataFrame(columns=["область", "медіана_ціни", "n"])

    result = (
        dff.dropna(subset=["область"])
        .groupby("область")["ціна"]
        .agg(медіана_ціни="median", n="count")
        .reset_index()
    )

    return result


# =============================================================================
# БЛОК 5: Аналіз зв'язку цін і обмінного курсу
# =============================================================================

def align_food_and_exchange(
    food_df: pd.DataFrame,
    exchange_df: pd.DataFrame,
    commodity: str,
    unit: str,
    oblast: Optional[str] = None,
) -> pd.DataFrame:
    """
    Вирівнює місячні ряди ціни товару та курсу UAH/USD.

    Логіка вирівнювання:
        1. Агрегуємо ціни по місяцях (медіана) → food_monthly
        2. Берем курс UAH/USD по місяцях → exchange_monthly
        3. Inner join за 'рік_місяць'
           (зберігаємо тільки місяці, де є обидва джерела)

    Чому INNER join:
        Ми не можемо інтерполювати відсутні значення курсу або ціни —
        це б привнесло штучні кореляції. Краще мати менше,
        але реальних спостережень.

    КРИТИЧНА МЕТОДОЛОГІЧНА ПРИМІТКА:
        Кореляція між ціною товару та курсом валюти є ОПИСОВОЮ мірою.
        Вона НЕ доводить причинно-наслідковий зв'язок.
        Обидва показники можуть одночасно реагувати на третій чинник
        (наприклад, воєнний конфлікт, глобальна інфляція).

    Повертає:
        DataFrame з колонками:
            дата, медіана_ціни, курс, товар, одиниця
    """
    # Крок 1: місячні ціни (медіана по ринках)
    food_monthly = get_food_timeseries(
        food_df, commodity=commodity, unit=unit, oblast=oblast
    )

    if food_monthly.empty:
        return pd.DataFrame()

    # Округляємо дату до місяця для join
    food_monthly["рік_місяць"] = food_monthly["дата"].dt.to_period("M")

    # Крок 2: місячний курс
    exch = exchange_df.dropna(subset=["дата", "курс"]).copy()
    exch["рік_місяць"] = exch["дата"].dt.to_period("M")

    # Берем тільки курс і місяць
    exch_slim = exch[["рік_місяць", "курс"]]

    # Крок 3: inner join за місяцем
    merged = food_monthly.merge(exch_slim, on="рік_місяць", how="inner")

    merged["товар"]    = commodity
    merged["одиниця"]  = unit

    return merged[["дата", "медіана_ціни", "курс", "товар", "одиниця"]]


def compute_correlation(df: pd.DataFrame) -> dict:
    """
    Обчислює кореляцію між ціною та курсом валюти.

    Повертає словник з:
        pearson_r    — коефіцієнт кореляції Пірсона
        pearson_p    — p-значення (статистична значущість)
        n            — кількість спостережень
        interpretation — текстова інтерпретація

    ЗАСТЕРЕЖЕННЯ: кореляція ≠ причинність.
    """
    from scipy import stats as scipy_stats

    # Видаляємо рядки з пропущеними значеннями перед кореляційним аналізом
    df_clean = df.dropna(subset=["медіана_ціни", "курс"])

    if df_clean.empty or len(df_clean) < 5:
        return {"pearson_r": None, "pearson_p": None, "n": len(df_clean),
                "interpretation": "Недостатньо даних для аналізу"}

    r, p = scipy_stats.pearsonr(df_clean["медіана_ціни"], df_clean["курс"])
    n = len(df_clean)

    # Описова інтерпретація сили кореляції
    abs_r = abs(r)
    if abs_r < 0.2:
        strength = "дуже слабка"
    elif abs_r < 0.4:
        strength = "слабка"
    elif abs_r < 0.6:
        strength = "помірна"
    elif abs_r < 0.8:
        strength = "сильна"
    else:
        strength = "дуже сильна"

    direction = "пряма" if r > 0 else "обернена"
    sig_note  = "статистично значуща (p < 0.05)" if p < 0.05 else "статистично незначуща (p ≥ 0.05)"

    interp = (
        f"{strength.capitalize()} {direction} кореляція (r = {r:.3f}), {sig_note}. "
        f"n = {n} місячних спостережень. "
        f"⚠️ Кореляція не означає причинно-наслідковий зв'язок."
    )

    return {
        "pearson_r": round(r, 4),
        "pearson_p": round(p, 6),
        "n": n,
        "interpretation": interp,
    }
