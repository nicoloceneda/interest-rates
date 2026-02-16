from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from ..charts import maturity_sort_key

DATE_COLUMN_CANDIDATES = ("Date", "date", "AsOfDate", "as_of_date")


def pick_first_existing(columns: Iterable[str], candidates: Sequence[str]) -> str | None:
    column_set = {str(column) for column in columns}
    for candidate in candidates:
        if candidate in column_set:
            return candidate
    return None


def get_state_value(state: Any, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if isinstance(state, Mapping) and key in state and state[key] is not None:
            return state[key]
        if hasattr(state, key):
            value = getattr(state, key)
            if value is not None:
                return value
    return default


def get_state_frame(state: Any, *keys: str) -> pd.DataFrame | None:
    value = get_state_value(state, *keys, default=None)
    if isinstance(value, pd.DataFrame):
        return value.copy()
    return None


def coerce_date_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    date_col = pick_first_existing(frame.columns, DATE_COLUMN_CANDIDATES)
    if date_col is None:
        return frame.copy()
    plot_df = frame.copy()
    plot_df[date_col] = pd.to_datetime(plot_df[date_col], errors="coerce")
    plot_df = plot_df.dropna(subset=[date_col]).sort_values(date_col)
    if date_col != "Date":
        plot_df = plot_df.rename(columns={date_col: "Date"})
    return plot_df


def available_dates(*frames: pd.DataFrame | None) -> list[datetime]:
    date_series_list: list[pd.Series] = []
    for frame in frames:
        if frame is None or frame.empty:
            continue
        plot_df = coerce_date_frame(frame)
        if "Date" in plot_df.columns:
            date_series_list.append(plot_df["Date"])
    if not date_series_list:
        return []
    combined = pd.concat(date_series_list, ignore_index=True)
    combined = pd.to_datetime(combined, errors="coerce").dropna().drop_duplicates().sort_values()
    return combined.dt.to_pydatetime().tolist()


def filter_by_date_range(
    frame: pd.DataFrame,
    start_date: datetime | pd.Timestamp | None,
    end_date: datetime | pd.Timestamp | None,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    plot_df = coerce_date_frame(frame)
    if "Date" not in plot_df.columns:
        return plot_df
    if start_date is not None:
        plot_df = plot_df[plot_df["Date"] >= pd.Timestamp(start_date)]
    if end_date is not None:
        plot_df = plot_df[plot_df["Date"] <= pd.Timestamp(end_date)]
    return plot_df


def detect_maturity_columns(frame: pd.DataFrame) -> list[str]:
    if frame is None or frame.empty:
        return []
    maturities = [
        str(column)
        for column in frame.columns
        if re.match(r"^\d+\s*[myMY]$", str(column).strip())
    ]
    return sorted(maturities, key=maturity_sort_key)


def default_maturity_selection(maturities: Sequence[str], max_items: int = 4) -> list[str]:
    canonical = ["2y", "5y", "10y", "30y"]
    selected = [maturity for maturity in canonical if maturity in maturities]
    if not selected:
        selected = list(maturities[:max_items])
    return selected


def format_rate(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.2f}%"


def format_spread(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):+.2f} pp"


def inject_dashboard_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                max-width: 1820px;
                padding-top: 1.1rem;
                padding-bottom: 2.2rem;
            }
            h1, h2, h3, h4 {
                color: #1D2733;
                letter-spacing: 0.01em;
            }
            [data-testid="stMetric"] {
                border: 1px solid #D7DDE5;
                border-radius: 10px;
                padding: 0.35rem 0.75rem;
            }
            [data-testid="stHorizontalBlock"] {
                gap: 0.9rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_tabs(state: Any) -> None:
    inject_dashboard_styles()
    tab_labels = [
        "Curve",
        "Historical",
        "Spreads",
        "Factors",
        "Heatmap",
        "Volatility",
        "Regimes",
        "Macro Context",
    ]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        render_curve_tab(state)
    with tabs[1]:
        render_historical_tab(state)
    with tabs[2]:
        render_spreads_tab(state)
    with tabs[3]:
        render_factors_tab(state)
    with tabs[4]:
        render_heatmap_tab(state)
    with tabs[5]:
        render_volatility_tab(state)
    with tabs[6]:
        render_regimes_tab(state)
    with tabs[7]:
        render_macro_context_tab(state)


from .curve import render_curve_tab
from .factors import render_factors_tab
from .heatmap import render_heatmap_tab
from .historical import render_historical_tab
from .macro_context import render_macro_context_tab
from .regimes import render_regimes_tab
from .spreads import render_spreads_tab
from .volatility import render_volatility_tab

__all__ = [
    "available_dates",
    "coerce_date_frame",
    "default_maturity_selection",
    "detect_maturity_columns",
    "filter_by_date_range",
    "format_rate",
    "format_spread",
    "get_state_frame",
    "get_state_value",
    "inject_dashboard_styles",
    "pick_first_existing",
    "render_curve_tab",
    "render_dashboard_tabs",
    "render_factors_tab",
    "render_heatmap_tab",
    "render_historical_tab",
    "render_macro_context_tab",
    "render_regimes_tab",
    "render_spreads_tab",
    "render_volatility_tab",
]
