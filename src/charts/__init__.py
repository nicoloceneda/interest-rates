from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

import pandas as pd

INSTITUTIONAL_PALETTE = [
    "#0F4C81",
    "#5B8FB9",
    "#2F6A4F",
    "#A44A3F",
    "#B08900",
    "#6B5B95",
    "#3E7C7D",
    "#8C5A3C",
]
REGIME_COLORS = {
    "Inversion": "#8C2D19",
    "Restrictive": "#B08900",
    "Steepening": "#2F6A4F",
    "Low-rate": "#2F4B7C",
    "Neutral": "#657184",
}
GRID_COLOR = "#D7DDE5"
AXIS_LABEL_COLOR = "#2A3647"
TITLE_COLOR = "#1D2733"


def pick_first_existing(columns: Iterable[str], candidates: Sequence[str]) -> str | None:
    column_set = {str(column) for column in columns}
    for candidate in candidates:
        if candidate in column_set:
            return candidate
    return None


def coerce_date_column(frame: pd.DataFrame, column: str = "Date") -> pd.DataFrame:
    if column not in frame.columns:
        return frame.copy()
    plot_df = frame.copy()
    plot_df[column] = pd.to_datetime(plot_df[column], errors="coerce")
    plot_df = plot_df.dropna(subset=[column]).sort_values(column)
    return plot_df


def maturity_sort_key(label: str) -> float:
    value = str(label).strip().lower()
    match = re.search(r"(\d+)\s*([my]?)", value)
    if not match:
        return float("inf")
    amount = float(match.group(1))
    unit = match.group(2)
    if unit == "m":
        return amount / 12.0
    return amount


from .curve import build_curve_chart
from .factors import build_factor_chart
from .heatmap import build_heatmap_chart
from .historical import build_historical_chart
from .macro import build_macro_context_chart
from .regimes import build_regime_chart
from .spreads import build_spread_chart
from .volatility import build_volatility_chart

__all__ = [
    "AXIS_LABEL_COLOR",
    "GRID_COLOR",
    "INSTITUTIONAL_PALETTE",
    "REGIME_COLORS",
    "TITLE_COLOR",
    "build_curve_chart",
    "build_factor_chart",
    "build_heatmap_chart",
    "build_historical_chart",
    "build_macro_context_chart",
    "build_regime_chart",
    "build_spread_chart",
    "build_volatility_chart",
    "coerce_date_column",
    "maturity_sort_key",
    "pick_first_existing",
]
