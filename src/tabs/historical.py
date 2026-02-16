"""Historical tab renderer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import build_historical_chart
from src.state import DashboardState

from . import default_maturity_selection


def render_historical_tab(state: DashboardState) -> None:
    """Render time-series history for selected maturities."""
    st.subheader("Historical Yields")
    if state.historical_table.empty:
        st.info("No historical data available.")
        return

    default_maturities = default_maturity_selection(state.maturity_columns, max_items=4)
    selected_maturities = st.multiselect(
        "Maturities",
        options=state.maturity_columns,
        default=default_maturities,
        key="historical_maturity_selector",
    )

    if not selected_maturities:
        st.info("Select at least one maturity to render historical yields.")
        return

    start_date, end_date = st.select_slider(
        "Date range",
        options=state.available_dates,
        value=(state.available_dates[0], state.available_dates[-1]),
        format_func=lambda value: pd.Timestamp(value).strftime("%Y-%m-%d"),
        key="historical_date_range_selector",
    )

    historical_filtered = state.historical_table[
        state.historical_table["Maturity"].isin(selected_maturities)
        & (state.historical_table["Date"] >= pd.Timestamp(start_date))
        & (state.historical_table["Date"] <= pd.Timestamp(end_date))
    ].copy()

    if historical_filtered.empty:
        st.info("No observations are available for the selected filters.")
        return

    chart_input = historical_filtered[["Date", "Maturity", "Yield"]].copy()
    st.altair_chart(
        build_historical_chart(
            chart_input,
            maturity_order=selected_maturities,
            title="Yield History by Maturity",
            height=520,
        ),
        use_container_width=True,
    )
