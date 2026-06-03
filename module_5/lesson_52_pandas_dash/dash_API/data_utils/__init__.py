# =============================================================================
# data_utils/__init__.py — Публічний API модуля data_utils
# =============================================================================
# Імпортуємо тільки те, що потрібно зовнішнім модулям.
# Решта (внутрішні деталі loader.py) залишається прихованою.
# =============================================================================

from .registry import get_dataset, DATASETS
from .preprocessing import (
    # Фільтрація та агрегація продуктових цін
    filter_food,
    get_units_for_commodity,
    get_food_timeseries,
    get_oblast_prices,
    get_oblast_variability,
    get_top_oblasts,
    get_food_summary_stats,

    # Обмінний курс
    get_exchange_timeseries,
    get_exchange_monthly_for_year_range,

    # Макроіндикатори / зовнішній борг
    get_debt_indicators,
    get_debt_timeseries,
    get_debt_indicator_code,

    # Геопросторовий аналіз
    join_food_to_markets,
    prepare_point_map_data,
    prepare_oblast_agg_map,

    # Кореляційний аналіз
    align_food_and_exchange,
    compute_correlation,
)

__all__ = [
    "get_dataset",
    "DATASETS",
    "filter_food",
    "get_units_for_commodity",
    "get_food_timeseries",
    "get_oblast_prices",
    "get_oblast_variability",
    "get_top_oblasts",
    "get_food_summary_stats",
    "get_exchange_timeseries",
    "get_exchange_monthly_for_year_range",
    "get_debt_indicators",
    "get_debt_timeseries",
    "get_debt_indicator_code",
    "join_food_to_markets",
    "prepare_point_map_data",
    "prepare_oblast_agg_map",
    "align_food_and_exchange",
    "compute_correlation",
]
