"""Shared configuration and secure settings helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass(frozen=True)
class TabDefinition:
    """Static metadata for a dashboard tab."""

    key: str
    label: str


@dataclass(frozen=True)
class DashboardConfig:
    """Container for application-level dashboard settings."""

    page_title: str = "US Treasury Rates Research Dashboard"
    layout: str = "wide"
    app_title: str = "US Treasury Rates"
    app_caption: str = "State-of-the-art visual analytics for the US Treasury term structure"
    data_path: Path = Path("data/gurkaynak/extracted/yields.csv")
    fred_cache_ttl_hours: int = 12
    volatility_window_days: int = 21
    spread_definitions: tuple[tuple[str, tuple[float, float]], ...] = (
        ("10Y-2Y", (10.0, 2.0)),
        ("30Y-10Y", (30.0, 10.0)),
        ("5Y-2Y", (5.0, 2.0)),
    )
    fred_series: tuple[tuple[str, str], ...] = (
        ("DFF", "Fed Funds"),
        ("DTB3", "3M T-Bill"),
        ("GS10", "10Y CMT"),
        ("T10Y3M", "10Y-3M Spread"),
        ("T10Y2Y", "10Y-2Y Spread"),
        ("T10YIE", "10Y Breakeven Inflation"),
        ("T5YIE", "5Y Breakeven Inflation"),
        ("USREC", "NBER Recession Indicator"),
    )
    tabs: Tuple[TabDefinition, ...] = (
        TabDefinition(key="curve", label="Curve"),
        TabDefinition(key="historical", label="Historical"),
        TabDefinition(key="spreads", label="Spreads"),
        TabDefinition(key="factors", label="Factors"),
        TabDefinition(key="heatmap", label="Heatmap"),
        TabDefinition(key="volatility", label="Volatility"),
        TabDefinition(key="regimes", label="Regimes"),
        TabDefinition(key="macro_context", label="Macro Context"),
    )


def get_fred_api_key() -> str | None:
    """
    Resolve the FRED API key from Streamlit secrets or environment.

    The key is intentionally never persisted to disk from this function.
    """
    secret_value: str | None = None
    try:
        import streamlit as st

        if "FRED_API_KEY" in st.secrets:
            secret_value = str(st.secrets["FRED_API_KEY"]).strip()
    except Exception:  # noqa: BLE001
        secret_value = None

    if secret_value:
        return secret_value

    env_value = os.getenv("FRED_API_KEY", "").strip()
    return env_value or None


def get_config() -> DashboardConfig:
    """Return the immutable dashboard configuration."""
    return DashboardConfig()
