"""Volatility tab renderer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import build_volatility_chart
from src.state import DashboardState

from . import default_maturity_selection


def render_volatility_tab(state: DashboardState) -> None:
    """Render realized volatility curves by maturity."""
    st.subheader("Rolling Volatility")
    st.caption("Realized volatility of daily yield changes, measured in basis points.")

    if state.volatility_table.empty:
        st.info("Volatility data is unavailable.")
        return

    start_date, end_date = st.select_slider(
        "Date range",
        options=state.available_dates,
        value=(state.available_dates[0], state.available_dates[-1]),
        format_func=lambda value: pd.Timestamp(value).strftime("%Y-%m-%d"),
        key="volatility_date_range_selector",
    )

    default_maturities = default_maturity_selection(state.maturity_columns, max_items=5)
    selected_maturities = st.multiselect(
        "Maturities",
        options=state.maturity_columns,
        default=default_maturities,
        key="volatility_maturity_selector",
    )
    if not selected_maturities:
        st.info("Select at least one maturity.")
        return

    filtered = state.volatility_table[
        (state.volatility_table["Date"] >= pd.Timestamp(start_date))
        & (state.volatility_table["Date"] <= pd.Timestamp(end_date))
        & (state.volatility_table["Maturity"].isin(selected_maturities))
    ].copy()
    if filtered.empty:
        st.info("No volatility observations for the selected filters.")
        return

    latest = filtered[filtered["Date"] == filtered["Date"].max()]
    metric_columns = st.columns(min(4, max(1, len(latest))))
    for idx, (_, row) in enumerate(latest.head(4).iterrows()):
        metric_columns[idx].metric(str(row["Maturity"]), f"{float(row['Volatility']):.2f} bp")

    st.altair_chart(
        build_volatility_chart(
            filtered[["Date", "Maturity", "Volatility"]],
            maturity_order=selected_maturities,
            title="Rolling Volatility by Maturity",
            height=520,
        ),
        use_container_width=True,
    )
