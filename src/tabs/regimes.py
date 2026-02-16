"""Regimes tab renderer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import build_regime_chart
from src.state import DashboardState


def render_regimes_tab(state: DashboardState) -> None:
    """Render rate regime segmentation and diagnostics."""
    st.subheader("Rate Regimes")
    if state.regimes_table.empty:
        st.info("Regime analytics are unavailable.")
        return

    start_date, end_date = st.select_slider(
        "Date range",
        options=state.available_dates,
        value=(state.available_dates[0], state.available_dates[-1]),
        format_func=lambda value: pd.Timestamp(value).strftime("%Y-%m-%d"),
        key="regimes_date_range_selector",
    )

    regimes = state.regimes_table[
        (state.regimes_table["Date"] >= pd.Timestamp(start_date))
        & (state.regimes_table["Date"] <= pd.Timestamp(end_date))
    ].copy()
    if regimes.empty:
        st.info("No regime observations for the selected date range.")
        return

    ten_year = state.historical_table[state.historical_table["Maturity"] == "10y"][
        ["Date", "Yield"]
    ].copy()
    ten_year = ten_year.rename(columns={"Yield": "Value"})
    ten_year = ten_year[
        (ten_year["Date"] >= pd.Timestamp(start_date)) & (ten_year["Date"] <= pd.Timestamp(end_date))
    ]

    st.altair_chart(
        build_regime_chart(
            regimes[["Date", "Regime"]],
            overlay_points=ten_year,
            overlay_label="10Y Yield (%)",
            title="Regime Timeline with 10Y Overlay",
            height=560,
        ),
        use_container_width=True,
    )

    regime_share = (
        regimes["Regime"].value_counts(normalize=True).mul(100).round(1).rename("Share (%)").to_frame()
    )
    st.dataframe(regime_share, use_container_width=True)
