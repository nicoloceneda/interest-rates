"""Main Streamlit dashboard assembly and runtime orchestration."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.config import DashboardConfig, get_config, get_fred_api_key
from src.data import fetch_fred_series_batch
from src.state import DashboardState, build_dashboard_state, load_gsw_state
from src.tabs import render_dashboard_tabs
from src.ui.layout import configure_page, render_header
from src.ui.theme import apply_theme

DEFAULT_FRED_TTL_SECONDS = get_config().fred_cache_ttl_hours * 60 * 60


@st.cache_data(show_spinner=False)
def _load_gsw_cached(data_path: str) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[pd.Timestamp]]:
    return load_gsw_state(data_path)


@st.cache_data(show_spinner=False)
def _empty_macro_table() -> tuple[pd.DataFrame, dict[str, str]]:
    return pd.DataFrame(columns=["Date", "SeriesID", "Series", "Value"]), {}


@st.cache_data(show_spinner=False, ttl=DEFAULT_FRED_TTL_SECONDS)
def _load_fred_cached(
    *,
    series_pairs: tuple[tuple[str, str], ...],
    api_key: str,
    observation_start: str,
    observation_end: str,
) -> tuple[pd.DataFrame, dict[str, str]]:
    series_ids = [series_id for series_id, _ in series_pairs]
    label_map = dict(series_pairs)

    data, errors = fetch_fred_series_batch(
        series_ids,
        api_key=api_key,
        observation_start=observation_start,
        observation_end=observation_end,
        timeout_seconds=20.0,
        continue_on_error=True,
    )
    if data.empty:
        return pd.DataFrame(columns=["Date", "SeriesID", "Series", "Value"]), errors

    macro = data.rename(
        columns={"date": "Date", "series_id": "SeriesID", "value": "Value"}
    )[["Date", "SeriesID", "Value"]].copy()
    macro["Series"] = macro["SeriesID"].map(lambda series: label_map.get(series, series))
    macro["Date"] = pd.to_datetime(macro["Date"], errors="coerce")
    macro["Value"] = pd.to_numeric(macro["Value"], errors="coerce")
    macro = macro.dropna(subset=["Date", "Value"]).sort_values(["Date", "Series"])
    return macro.reset_index(drop=True), errors


def _load_macro_data(config: DashboardConfig, available_dates: list[pd.Timestamp]) -> tuple[pd.DataFrame, dict[str, str]]:
    if not available_dates:
        return _empty_macro_table()

    fred_api_key = get_fred_api_key()
    if not fred_api_key:
        return _empty_macro_table()

    start = available_dates[0].strftime("%Y-%m-%d")
    end = available_dates[-1].strftime("%Y-%m-%d")
    return _load_fred_cached(
        series_pairs=config.fred_series,
        api_key=fred_api_key,
        observation_start=start,
        observation_end=end,
    )


def _build_state(config: DashboardConfig) -> DashboardState:
    curve_table, historical_table, maturity_columns, available_dates = _load_gsw_cached(
        str(config.data_path)
    )
    macro_table, fred_errors = _load_macro_data(config, available_dates)
    return build_dashboard_state(
        curve_table=curve_table,
        historical_table=historical_table,
        maturity_columns=maturity_columns,
        available_dates=available_dates,
        macro_table=macro_table,
        fred_errors=fred_errors,
        spread_definitions=config.spread_definitions,
        volatility_window_days=config.volatility_window_days,
    )


def _render_sidebar_status(config: DashboardConfig, state: DashboardState) -> None:
    st.sidebar.subheader("Data Status")
    st.sidebar.write(f"GSW file: `{config.data_path}`")
    st.sidebar.write(f"Observations: `{len(state.available_dates):,}` dates")
    st.sidebar.write(f"Maturities: `{len(state.maturity_columns)}`")

    if get_fred_api_key():
        st.sidebar.success("FRED key detected")
    else:
        st.sidebar.warning("FRED key missing")
        st.sidebar.caption("Set `FRED_API_KEY` in `.streamlit/secrets.toml` or environment.")

    if state.fred_errors:
        st.sidebar.warning("Some FRED series failed")
        for series_id, message in sorted(state.fred_errors.items()):
            st.sidebar.caption(f"{series_id}: {message}")


def run() -> None:
    """Run the dashboard entrypoint."""
    config = get_config()
    configure_page(config)
    alt.data_transformers.disable_max_rows()
    apply_theme()
    render_header(config)

    try:
        state = _build_state(config)
    except FileNotFoundError:
        st.error(
            f"Could not find `{config.data_path}`. Run `python data.py` first to download and extract data."
        )
        st.stop()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not initialize dashboard data: {exc}")
        st.stop()

    _render_sidebar_status(config, state)
    render_dashboard_tabs(state)
