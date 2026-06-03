"""
analyzer.py — Analytical Core of the E-commerce Analytics Engine

Architecture: this file knows NOTHING about UI.
It exposes pure analytical objects. app.py calls them.

Concepts demonstrated (Module 2):
  - Functions as first-class objects  (METRIC_REGISTRY, TRANSFORM_PIPELINE)
  - Functions passed as arguments      (run_metrics, run_pipeline)
  - Decorators                         (@timed)
  - OOP: base class + subclasses       (DatasetAnalyzer, SalesAnalyzer, ReturnAnalyzer)
  - Encapsulation                      (_df, _cache, _compute)
  - @property, dunder methods          (row_count, __repr__, __len__, __contains__)
  - Context manager                    (DataLoader)
"""

from __future__ import annotations

import time
import functools
from pathlib import Path
from typing import Callable

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# DECORATOR
# ─────────────────────────────────────────────────────────────────────────────

def timed(func: Callable) -> Callable:
    """Records wall-clock execution time; returns (result, ms) tuple."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return result, elapsed_ms
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
# PURE METRIC FUNCTIONS
# Key concept: functions are objects — stored in a list, passed as arguments.
# Signature contract: (df: DataFrame) → scalar
# ─────────────────────────────────────────────────────────────────────────────

def metric_avg_order_value(df: pd.DataFrame) -> float:
    """Average final price of delivered orders."""
    delivered = df[df['delivery_status'] == 'Delivered']
    return round(float(delivered['final_price'].mean()), 2)


def metric_return_rate(df: pd.DataFrame) -> float:
    """Fraction of orders that were returned."""
    return round(float(df['is_returned'].mean()), 4)


def metric_total_revenue(df: pd.DataFrame) -> float:
    """Sum of final_price for delivered orders."""
    delivered = df[df['delivery_status'] == 'Delivered']
    return round(float(delivered['final_price'].sum()), 2)


def metric_avg_rating(df: pd.DataFrame) -> float:
    """Average customer rating across all orders."""
    return round(float(df['rating'].mean()), 3)


def metric_avg_shipping_days(df: pd.DataFrame) -> float:
    """Average shipping time for delivered orders."""
    delivered = df[df['delivery_status'] == 'Delivered']
    return round(float(delivered['shipping_time_days'].mean()), 2)


def metric_discount_adoption(df: pd.DataFrame) -> float:
    """Fraction of orders that received any discount."""
    return round(float((df['discount'] > 0).mean()), 4)


# ─────────────────────────────────────────────────────────────────────────────
# METRIC REGISTRY
# Key concept: a list of (name, function) pairs.
# Any code can iterate this list and call each function generically.
# ─────────────────────────────────────────────────────────────────────────────

METRIC_REGISTRY: list[tuple[str, Callable[[pd.DataFrame], float]]] = [
    ('Avg Order Value (₹)',  metric_avg_order_value),
    ('Return Rate',          metric_return_rate),
    ('Total Revenue (₹)',    metric_total_revenue),
    ('Avg Customer Rating',  metric_avg_rating),
    ('Avg Shipping Days',    metric_avg_shipping_days),
    ('Discount Adoption',    metric_discount_adoption),
]


# ─────────────────────────────────────────────────────────────────────────────
# TRANSFORM PIPELINE STEPS
# Key concept: each function is a pure transformation DataFrame → DataFrame.
# They can be composed into any sequence.
# ─────────────────────────────────────────────────────────────────────────────

def step_filter_delivered(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only orders with delivery_status == 'Delivered'."""
    return df[df['delivery_status'] == 'Delivered'].copy()


def step_add_revenue_band(df: pd.DataFrame) -> pd.DataFrame:
    """Classify orders into Low / Mid / High revenue bands."""
    df = df.copy()
    df['revenue_band'] = pd.cut(
        df['final_price'],
        bins=[0, 2_000, 15_000, float('inf')],
        labels=['Low', 'Mid', 'High'],
    )
    return df


def step_add_is_late(df: pd.DataFrame) -> pd.DataFrame:
    """Flag orders with shipping_time_days > 5 as late."""
    df = df.copy()
    df['is_late'] = df['shipping_time_days'] > 5
    return df


def step_add_discount_tier(df: pd.DataFrame) -> pd.DataFrame:
    """Bucket discount percentage into tiers."""
    df = df.copy()
    df['discount_tier'] = pd.cut(
        df['discount'],
        bins=[0, 15, 35, 100],
        labels=['Light (<15%)', 'Medium (15-35%)', 'Heavy (>35%)'],
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# TRANSFORM PIPELINE
# Key concept: ordered list of transform functions — each step hands off to next.
# ─────────────────────────────────────────────────────────────────────────────

TRANSFORM_PIPELINE: list[Callable[[pd.DataFrame], pd.DataFrame]] = [
    step_filter_delivered,
    step_add_revenue_band,
    step_add_is_late,
    step_add_discount_tier,
]


# ─────────────────────────────────────────────────────────────────────────────
# BASE CLASS: DatasetAnalyzer
# ─────────────────────────────────────────────────────────────────────────────

class DatasetAnalyzer:
    """
    Base analytical engine over a tabular e-commerce dataset.

    Demonstrates:
      • encapsulation  — _df and _cache are private
      • @property      — computed read-only attributes
      • dunder methods — __repr__, __len__, __contains__
      • functions as arguments — run_metrics(), run_pipeline()
      • caching        — _compute() stores results to avoid re-computation
    """

    def __init__(self, df: pd.DataFrame, name: str = 'Dataset') -> None:
        self._df: pd.DataFrame = df.copy()   # _private: external code cannot mutate
        self._name: str = name
        self._cache: dict = {}               # _private: implementation detail

    # ── @property — computed read-only attributes ─────────────────────────────

    @property
    def name(self) -> str:
        return self._name

    @property
    def row_count(self) -> int:
        return len(self._df)

    @property
    def delivered(self) -> pd.DataFrame:
        """Subset of delivered orders — computed lazily on each access."""
        return self._df[self._df['delivery_status'] == 'Delivered']

    @property
    def returned(self) -> pd.DataFrame:
        """Subset of returned orders."""
        return self._df[self._df['is_returned']]

    @property
    def date_range(self) -> str:
        mn = self._df['purchase_date'].min()
        mx = self._df['purchase_date'].max()
        return f'{str(mn)[:10]} → {str(mx)[:10]}'

    # ── Dunder methods ─────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'name={self._name!r}, rows={self.row_count:,})'
        )

    def __len__(self) -> int:
        """len(analyzer) → number of rows."""
        return self.row_count

    def __contains__(self, user_id: str) -> bool:
        """'U12345' in analyzer → True if user exists in dataset."""
        return user_id in self._df['user_id'].values

    # ── Private: cache layer ───────────────────────────────────────────────────

    def _compute(self, key: str, func: Callable):
        """
        Compute-once cache.
        First call: executes func() and stores result.
        Subsequent calls: returns stored result instantly.
        """
        if key not in self._cache:
            self._cache[key] = func()
        return self._cache[key]

    # ── Public: functions as arguments ────────────────────────────────────────

    def run_metrics(
        self,
        metric_list: list[tuple[str, Callable[[pd.DataFrame], float]]],
    ) -> dict[str, float]:
        """
        KEY CONCEPT — functions as arguments.

        Takes a LIST OF FUNCTIONS, executes each against the dataset.
        The caller decides which metrics to compute; this class does the execution.

        Usage:
            results = analyzer.run_metrics(METRIC_REGISTRY)
            # → {'Avg Order Value (₹)': 8432.1, 'Return Rate': 0.105, ...}
        """
        return {name: func(self._df) for name, func in metric_list}

    def run_pipeline(
        self,
        pipeline: list[Callable[[pd.DataFrame], pd.DataFrame]],
    ) -> pd.DataFrame:
        """
        KEY CONCEPT — pipeline pattern.

        Applies a sequence of transform functions to the dataset.
        Each function: DataFrame → DataFrame (same shape contract).
        The result of each step is the input to the next.

        Usage:
            enriched = analyzer.run_pipeline(TRANSFORM_PIPELINE)
        """
        result = self._df.copy()
        for step in pipeline:
            result = step(result)
        return result

    def status(self) -> dict:
        """Returns metadata about the dataset — used by the UI for 'Engine Status'."""
        return {
            'Name':       self._name,
            'Total Rows': f'{self.row_count:,}',
            'Delivered':  f'{len(self.delivered):,}',
            'Returned':   f'{len(self.returned):,}',
            'Categories': str(self._df['category'].nunique()),
            'Sellers':    f'{self._df["seller_id"].nunique():,}',
            'Date Range': self.date_range,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SUBCLASS: SalesAnalyzer
# ─────────────────────────────────────────────────────────────────────────────

class SalesAnalyzer(DatasetAnalyzer):
    """
    Specialization of DatasetAnalyzer for sales pattern analysis.

    Inherits:  all base properties, run_metrics, run_pipeline, status
    Adds:      revenue_by_category, discount_impact, monthly_revenue_trend,
               top_brands_by_revenue, category_rating_comparison
    """

    def __init__(self, df: pd.DataFrame, name: str = 'Sales') -> None:
        super().__init__(df, name)

    def revenue_by_category(self) -> pd.Series:
        """Total revenue (₹) per category, sorted descending."""
        return self._compute(
            'rev_cat',
            lambda: (
                self.delivered
                .groupby('category')['final_price']
                .sum()
                .sort_values(ascending=False)
                .round(0)
            ),
        )

    def discount_impact(self) -> pd.DataFrame:
        """
        Groups orders by discount tier → shows avg rating + avg revenue + count.
        Answers: 'Does a bigger discount improve customer satisfaction?'
        """
        df = self._df.copy()
        df['discount_tier'] = pd.cut(
            df['discount'],
            bins=[0, 15, 35, 100],
            labels=['Light (<15%)', 'Medium (15-35%)', 'Heavy (>35%)'],
        )
        return (
            df.groupby('discount_tier', observed=True)
            .agg(
                avg_rating=('rating',      'mean'),
                avg_revenue=('final_price', 'mean'),
                order_count=('user_id',    'count'),
            )
            .round(2)
        )

    def top_brands_by_revenue(self, n: int = 8) -> pd.Series:
        """Top-N brands by total revenue from delivered orders."""
        return (
            self.delivered
            .groupby('brand')['final_price']
            .sum()
            .nlargest(n)
            .round(0)
        )

    def monthly_revenue_trend(self) -> pd.Series:
        """Monthly revenue trend from delivered orders."""
        return (
            self.delivered
            .set_index('purchase_date')
            .resample('ME')['final_price']
            .sum()
            .round(0)
        )

    def category_rating_comparison(self) -> pd.DataFrame:
        """Per-category: avg rating, avg price, return rate, order count."""
        total = self._df.groupby('category').size()
        ret = self._df[self._df['is_returned']].groupby('category').size()
        return (
            self._df.groupby('category')
            .agg(
                avg_rating=('rating',      'mean'),
                avg_price= ('final_price', 'mean'),
                orders=    ('user_id',     'count'),
            )
            .assign(return_rate=(ret / total).round(3))
            .round(2)
            .sort_values('avg_rating', ascending=False)
        )


# ─────────────────────────────────────────────────────────────────────────────
# SUBCLASS: ReturnAnalyzer
# ─────────────────────────────────────────────────────────────────────────────

class ReturnAnalyzer(DatasetAnalyzer):
    """
    Specialization of DatasetAnalyzer for return pattern analysis.

    Inherits:  all base functionality
    Adds:      return_rate_by_category, shipping_vs_return,
               seller_reliability_score, payment_method_analysis
    """

    def __init__(self, df: pd.DataFrame, name: str = 'Returns') -> None:
        super().__init__(df, name)

    def return_rate_by_category(self) -> pd.Series:
        """Return rate (0–1) for each category, sorted descending."""
        total = self._df.groupby('category').size()
        ret   = self.returned.groupby('category').size()
        return (ret / total).fillna(0).sort_values(ascending=False).round(4)

    def shipping_vs_return(self) -> pd.DataFrame:
        """
        Groups orders by shipping duration → shows return rate per group.
        Answers: 'Do longer deliveries cause more returns?'
        """
        df = self._df.copy()
        df['ship_band'] = pd.cut(
            df['shipping_time_days'],
            bins=[0, 2, 4, 6, 100],
            labels=['1-2 days', '3-4 days', '5-6 days', '7+ days'],
        )
        return (
            df.groupby('ship_band', observed=True)
            .agg(
                return_rate=('is_returned', 'mean'),
                avg_rating= ('rating',      'mean'),
                order_count=('user_id',     'count'),
            )
            .round(3)
        )

    def seller_reliability_score(self) -> pd.DataFrame:
        """
        Composite score per seller:
            reliability = avg_rating × (1 − return_rate)
        Higher score → more reliable seller.
        """
        total    = self._df.groupby('seller_id').size()
        ret      = self.returned.groupby('seller_id').size()
        avg_rat  = self._df.groupby('seller_id')['rating'].mean()
        avg_rev  = self.delivered.groupby('seller_id')['final_price'].mean()

        score = pd.DataFrame({
            'orders':      total,
            'return_rate': (ret / total).fillna(0).round(3),
            'avg_rating':  avg_rat.round(2),
            'avg_revenue': avg_rev.round(0),
        })
        score['reliability'] = (
            score['avg_rating'] * (1 - score['return_rate'])
        ).round(3)
        return score.sort_values('reliability', ascending=False)

    def payment_return_analysis(self) -> pd.DataFrame:
        """Return rate per payment method — which payment type correlates with returns?"""
        total = self._df.groupby('payment_method').size()
        ret   = self.returned.groupby('payment_method').size()
        avg_r = self._df.groupby('payment_method')['rating'].mean()
        return pd.DataFrame({
            'orders':      total,
            'return_rate': (ret / total).fillna(0).round(3),
            'avg_rating':  avg_r.round(2),
        }).sort_values('return_rate', ascending=False)


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT MANAGER: DataLoader
# ─────────────────────────────────────────────────────────────────────────────

class DataLoader:
    """
    Context manager for safe, guaranteed CSV loading.

    __enter__: reads CSV → constructs (SalesAnalyzer, ReturnAnalyzer)
    __exit__:  logs completion; guaranteed to run even if analysis fails

    Usage:
        with DataLoader('amazon_ecommerce_1M.csv', nrows=200_000) as (sales, ret):
            sales.revenue_by_category()
    """

    def __init__(
        self,
        filepath: str | Path,
        nrows: int | None = None,
        name: str = 'Amazon',
    ) -> None:
        self._filepath = Path(filepath)
        self._nrows    = nrows
        self._name     = name

    def __enter__(self) -> tuple[SalesAnalyzer, ReturnAnalyzer]:
        if not self._filepath.exists():
            raise FileNotFoundError(f'Dataset not found: {self._filepath}')
        df = pd.read_csv(
            self._filepath,
            parse_dates=['purchase_date'],
            nrows=self._nrows,
        )
        return (
            SalesAnalyzer(df,  name=self._name),
            ReturnAnalyzer(df, name=self._name),
        )

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        # This block ALWAYS runs — whether analysis succeeded or raised an error.
        # That is the entire point of a context manager.
        return False  # False → do not suppress exceptions
