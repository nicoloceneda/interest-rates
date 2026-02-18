"""Curve tab renderer."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.charts import GRID_COLOR, build_curve_chart
from src.state import DashboardState

from . import format_rate, format_spread


def _maturity_value(curve_row: pd.Series, maturity: str) -> float | None:
    if maturity not in curve_row.index:
        return None
    value = pd.to_numeric(pd.Series([curve_row[maturity]]), errors="coerce").iloc[0]
    if pd.isna(value):
        return None
    return float(value)


def _render_overlay_chart(primary: pd.DataFrame, compare: pd.DataFrame) -> alt.Chart:
    first = primary.copy()
    first["Scenario"] = "Selected"
    second = compare.copy()
    second["Scenario"] = "Comparison"
    combined = pd.concat([first, second], ignore_index=True)

    return (
        alt.Chart(combined)
        .mark_line(point=True, strokeWidth=2.3)
        .encode(
            x=alt.X(
                "MaturityYears:Q",
                title="Maturity (Years)",
                axis=alt.Axis(grid=True, tickMinStep=1),
            ),
            y=alt.Y("Yield:Q", title="Yield (%)", axis=alt.Axis(grid=True)),
            color=alt.Color(
                "Scenario:N",
                scale=alt.Scale(domain=["Selected", "Comparison"], range=["#0F4C81", "#A44A3F"]),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("Scenario:N", title="Curve"),
                alt.Tooltip("Maturity:N", title="Maturity"),
                alt.Tooltip("Yield:Q", title="Yield (%)", format=".3f"),
            ],
        )
        .properties(height=510, title="Yield Curve Comparison")
        .configure_axis(labelColor="#2A3647", titleColor="#2A3647", gridColor=GRID_COLOR)
        .configure_title(color="#1D2733", fontSize=16, anchor="start")
        .configure_view(strokeOpacity=0)
    )


def render_curve_tab(state: DashboardState) -> None:
    """Render the curve snapshot and comparison view."""
    st.subheader("Curve Snapshot")
    if not state.available_dates:
        st.info("No dates available to render the curve.")
        return

    latest_date = state.available_dates[-1]
    selected_curve_date = st.select_slider(
        "Date",
        options=state.available_dates,
        value=latest_date,
        format_func=lambda value: pd.Timestamp(value).strftime("%Y-%m-%d"),
        key="curve_date_selector",
    )

    curve_row = state.curve_table[state.curve_table["Date"] == pd.Timestamp(selected_curve_date)]
    if curve_row.empty:
        st.info("No observations are available for the selected date.")
        return

    current_row = curve_row.iloc[0]
    y2 = _maturity_value(current_row, "2y")
    y10 = _maturity_value(current_row, "10y")
    y30 = _maturity_value(current_row, "30y")
    spread_10_2 = (y10 - y2) if y10 is not None and y2 is not None else None
    spread_30_10 = (y30 - y10) if y30 is not None and y10 is not None else None

    metric_columns = st.columns(5)
    metric_columns[0].metric("2Y", format_rate(y2))
    metric_columns[1].metric("10Y", format_rate(y10))
    metric_columns[2].metric("30Y", format_rate(y30))
    metric_columns[3].metric("10Y-2Y", format_spread(spread_10_2))
    metric_columns[4].metric("30Y-10Y", format_spread(spread_30_10))

    selected_curve_points = state.historical_table[
        state.historical_table["Date"] == pd.Timestamp(selected_curve_date)
    ].copy()
    if selected_curve_points.empty:
        st.info("No curve points are available for the selected date.")
        return

    compare_enabled = st.toggle("Overlay comparison date", value=False, key="curve_compare_toggle")
    if compare_enabled:
        comparison_options = [date for date in state.available_dates if date <= pd.Timestamp(selected_curve_date)]
        comparison_default = comparison_options[0] if comparison_options else pd.Timestamp(selected_curve_date)
        comparison_date = st.select_slider(
            "Comparison date",
            options=comparison_options,
            value=comparison_default,
            format_func=lambda value: pd.Timestamp(value).strftime("%Y-%m-%d"),
            key="curve_compare_date_selector",
        )
        compare_points = state.historical_table[
            state.historical_table["Date"] == pd.Timestamp(comparison_date)
        ].copy()
        if compare_points.empty:
            st.warning("No observations found for the comparison date.")
        else:
            st.altair_chart(
                _render_overlay_chart(selected_curve_points, compare_points),
                use_container_width=True,
            )
    else:
        st.altair_chart(
            build_curve_chart(
                selected_curve_points[["Date", "Maturity", "MaturityYears", "Yield"]],
                title="Yield Curve Level",
                height=510,
            ),
            use_container_width=True,
        )
