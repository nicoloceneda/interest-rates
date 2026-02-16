"""Macro context tab renderer."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.charts import INSTITUTIONAL_PALETTE
from src.state import DashboardState


def _build_recession_intervals(recession_df: pd.DataFrame) -> pd.DataFrame:
    if recession_df.empty:
        return pd.DataFrame(columns=["start", "end"])

    df = recession_df.copy().sort_values("Date")
    df["flag"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0.0) >= 0.5
    df = df[df["flag"]]
    if df.empty:
        return pd.DataFrame(columns=["start", "end"])

    dates = pd.to_datetime(df["Date"], errors="coerce").dropna().sort_values().reset_index(drop=True)
    if dates.empty:
        return pd.DataFrame(columns=["start", "end"])

    intervals: list[dict[str, pd.Timestamp]] = []
    start = dates.iloc[0]
    previous = dates.iloc[0]
    for current in dates.iloc[1:]:
        if (current - previous).days > 40:
            intervals.append({"start": start, "end": previous + pd.Timedelta(days=1)})
            start = current
        previous = current
    intervals.append({"start": start, "end": previous + pd.Timedelta(days=1)})
    return pd.DataFrame(intervals)


def render_macro_context_tab(state: DashboardState) -> None:
    """Render macro overlays around Treasury rates."""
    st.subheader("Macro Context")

    if state.macro_table.empty:
        st.info(
            "No FRED data available. Set `FRED_API_KEY` in `.streamlit/secrets.toml` or "
            "as an environment variable to enable macro context overlays."
        )
        return

    macro = state.macro_table.copy()
    start_date, end_date = st.select_slider(
        "Date range",
        options=state.available_dates,
        value=(state.available_dates[0], state.available_dates[-1]),
        format_func=lambda value: pd.Timestamp(value).strftime("%Y-%m-%d"),
        key="macro_date_range_selector",
    )
    macro = macro[
        (macro["Date"] >= pd.Timestamp(start_date)) & (macro["Date"] <= pd.Timestamp(end_date))
    ].copy()
    if macro.empty:
        st.info("No macro observations in the selected date range.")
        return

    series_options = sorted(
        [series for series in macro["Series"].dropna().astype(str).unique().tolist() if series != "NBER Recession Indicator"]
    )
    default_series = [series for series in ["Fed Funds", "10Y CMT", "10Y-3M Spread"] if series in series_options]
    if not default_series and series_options:
        default_series = series_options[: min(3, len(series_options))]

    selected_series = st.multiselect(
        "Series",
        options=series_options,
        default=default_series,
        key="macro_series_selector",
    )
    if not selected_series:
        st.info("Select at least one macro series.")
        return

    line_df = macro[macro["Series"].isin(selected_series)].copy()
    if line_df.empty:
        st.info("No values available for the selected series.")
        return

    series_domain = selected_series
    series_range = [INSTITUTIONAL_PALETTE[idx % len(INSTITUTIONAL_PALETTE)] for idx, _ in enumerate(series_domain)]

    line_chart = (
        alt.Chart(line_df)
        .mark_line(strokeWidth=2.2)
        .encode(
            x=alt.X("Date:T", title="Date", axis=alt.Axis(grid=True, tickCount="year")),
            y=alt.Y("Value:Q", title="Value", axis=alt.Axis(grid=True)),
            color=alt.Color(
                "Series:N",
                sort=series_domain,
                scale=alt.Scale(domain=series_domain, range=series_range),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Series:N", title="Series"),
                alt.Tooltip("Value:Q", title="Value", format=".3f"),
            ],
        )
    )

    recession = macro[macro["Series"] == "NBER Recession Indicator"][["Date", "Value"]]
    recession_intervals = _build_recession_intervals(recession)
    if recession_intervals.empty:
        chart = line_chart
    else:
        recession_layer = (
            alt.Chart(recession_intervals)
            .mark_rect(color="#A44A3F", opacity=0.12)
            .encode(x=alt.X("start:T"), x2=alt.X2("end:T"))
        )
        chart = recession_layer + line_chart

    st.altair_chart(
        chart.properties(height=540, title="Treasury Macro Overlay (with recession shading)")
        .configure_axis(labelColor="#2A3647", titleColor="#2A3647", gridColor="#D7DDE5")
        .configure_title(color="#1D2733", fontSize=16, anchor="start")
        .configure_view(strokeOpacity=0),
        use_container_width=True,
    )
