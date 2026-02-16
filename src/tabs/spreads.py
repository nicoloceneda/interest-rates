"""Spreads tab renderer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import build_spread_chart
from src.state import DashboardState

from . import format_spread


def _custom_spread_from_curve(
    curve_table: pd.DataFrame,
    *,
    long_maturity: str,
    short_maturity: str,
) -> pd.DataFrame:
    if long_maturity not in curve_table.columns or short_maturity not in curve_table.columns:
        return pd.DataFrame(columns=["Date", "Spread", "Value"])

    spread_name = f"{long_maturity.upper()}-{short_maturity.upper()}"
    custom = curve_table[["Date", long_maturity, short_maturity]].copy()
    custom["Value"] = pd.to_numeric(custom[long_maturity], errors="coerce") - pd.to_numeric(
        custom[short_maturity], errors="coerce"
    )
    custom["Spread"] = spread_name
    return custom[["Date", "Spread", "Value"]].dropna(subset=["Value"])


def render_spreads_tab(state: DashboardState) -> None:
    """Render structural spread diagnostics."""
    st.subheader("Spread Analytics")
    if state.spreads_table.empty:
        st.info("Spread data is unavailable.")
        return

    start_date, end_date = st.select_slider(
        "Date range",
        options=state.available_dates,
        value=(state.available_dates[0], state.available_dates[-1]),
        format_func=lambda value: pd.Timestamp(value).strftime("%Y-%m-%d"),
        key="spreads_date_range_selector",
    )

    spreads = state.spreads_table[
        (state.spreads_table["Date"] >= pd.Timestamp(start_date))
        & (state.spreads_table["Date"] <= pd.Timestamp(end_date))
    ].copy()

    long_maturity = st.selectbox(
        "Custom spread long leg",
        options=state.maturity_columns,
        index=max(0, state.maturity_columns.index("10y")) if "10y" in state.maturity_columns else 0,
        key="custom_spread_long",
    )
    short_maturity_candidates = [maturity for maturity in state.maturity_columns if maturity != long_maturity]
    if not short_maturity_candidates:
        st.info("At least two maturities are required to build a custom spread.")
        return
    short_default = "2y" if "2y" in short_maturity_candidates else short_maturity_candidates[0]
    short_maturity = st.selectbox(
        "Custom spread short leg",
        options=short_maturity_candidates,
        index=short_maturity_candidates.index(short_default),
        key="custom_spread_short",
    )

    custom_spread = _custom_spread_from_curve(
        state.curve_table,
        long_maturity=long_maturity,
        short_maturity=short_maturity,
    )
    if not custom_spread.empty:
        custom_spread = custom_spread[
            (custom_spread["Date"] >= pd.Timestamp(start_date))
            & (custom_spread["Date"] <= pd.Timestamp(end_date))
        ]
        spreads = pd.concat([spreads, custom_spread], ignore_index=True)

    if spreads.empty:
        st.info("No spread observations are available for the selected range.")
        return

    latest_snapshot = spreads[spreads["Date"] == spreads["Date"].max()]
    metric_columns = st.columns(min(4, max(1, len(latest_snapshot))))
    for idx, (_, row) in enumerate(latest_snapshot.head(4).iterrows()):
        metric_columns[idx].metric(str(row["Spread"]), format_spread(row["Value"]))

    spread_order = sorted(spreads["Spread"].dropna().astype(str).unique().tolist())
    st.altair_chart(
        build_spread_chart(
            spreads,
            spread_order=spread_order,
            title="Treasury Curve Spreads",
            height=520,
        ),
        use_container_width=True,
    )
