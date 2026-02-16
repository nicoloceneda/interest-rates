"""Factors tab renderer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import build_factor_chart
from src.state import DashboardState


def _format_factor(value: float | None, *, signed: bool = True) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    if signed:
        return f"{float(value):+.2f}"
    return f"{float(value):.2f}"


def render_factors_tab(state: DashboardState) -> None:
    """Render term-structure factor decomposition."""
    st.subheader("Level, Slope, Curvature")
    if state.factors_long.empty:
        st.info("Factor data is unavailable.")
        return

    start_date, end_date = st.select_slider(
        "Date range",
        options=state.available_dates,
        value=(state.available_dates[0], state.available_dates[-1]),
        format_func=lambda value: pd.Timestamp(value).strftime("%Y-%m-%d"),
        key="factors_date_range_selector",
    )

    filtered = state.factors_long[
        (state.factors_long["Date"] >= pd.Timestamp(start_date))
        & (state.factors_long["Date"] <= pd.Timestamp(end_date))
    ].copy()
    if filtered.empty:
        st.info("No factor observations for the selected range.")
        return

    latest_date = filtered["Date"].max()
    latest = filtered[filtered["Date"] == latest_date]
    factor_to_value = {str(row["Factor"]): row["Value"] for _, row in latest.iterrows()}
    metric_columns = st.columns(3)
    metric_columns[0].metric("Level", _format_factor(factor_to_value.get("Level"), signed=False))
    metric_columns[1].metric("Slope", _format_factor(factor_to_value.get("Slope")))
    metric_columns[2].metric("Curvature", _format_factor(factor_to_value.get("Curvature")))

    st.altair_chart(
        build_factor_chart(
            filtered,
            factor_order=["Level", "Slope", "Curvature"],
            title="Term Structure Factors Through Time",
            height=520,
        ),
        use_container_width=True,
    )
