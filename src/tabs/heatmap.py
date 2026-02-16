"""Heatmap tab renderer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import build_heatmap_chart
from src.state import DashboardState


def render_heatmap_tab(state: DashboardState) -> None:
    """Render the cross-sectional term-structure heatmap."""
    st.subheader("Yield Surface Heatmap")
    metric_choice = st.radio(
        "Metric",
        options=["Yield level (%)", "Daily change (bp)"],
        horizontal=True,
        key="heatmap_metric_choice",
    )

    source = state.heatmap_levels if metric_choice == "Yield level (%)" else state.heatmap_changes
    if source.empty:
        st.info("No heatmap observations are available.")
        return

    start_date, end_date = st.select_slider(
        "Date range",
        options=state.available_dates,
        value=(state.available_dates[0], state.available_dates[-1]),
        format_func=lambda value: pd.Timestamp(value).strftime("%Y-%m-%d"),
        key="heatmap_date_range_selector",
    )
    filtered = source[
        (source["Date"] >= pd.Timestamp(start_date)) & (source["Date"] <= pd.Timestamp(end_date))
    ].copy()

    selected_maturities = st.multiselect(
        "Maturities",
        options=state.maturity_columns,
        default=state.maturity_columns,
        key="heatmap_maturity_selector",
    )
    if selected_maturities:
        filtered = filtered[filtered["Maturity"].isin(selected_maturities)]

    if filtered.empty:
        st.info("No heatmap data after applying current filters.")
        return

    st.altair_chart(
        build_heatmap_chart(
            filtered,
            title=f"Term Structure {metric_choice}",
            height=560,
        ),
        use_container_width=True,
    )
