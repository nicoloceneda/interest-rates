from __future__ import annotations

from collections.abc import Sequence

import altair as alt
import pandas as pd

from . import (
    AXIS_LABEL_COLOR,
    GRID_COLOR,
    INSTITUTIONAL_PALETTE,
    TITLE_COLOR,
    coerce_date_column,
    maturity_sort_key,
    pick_first_existing,
)


def _coerce_volatility_points(volatility_points: pd.DataFrame) -> pd.DataFrame:
    plot_df = coerce_date_column(volatility_points)
    maturity_col = pick_first_existing(plot_df.columns, ["Maturity", "maturity", "Tenor", "tenor", "Series"])
    value_col = pick_first_existing(plot_df.columns, ["Volatility", "volatility", "Value", "value", "Sigma", "sigma"])
    if "Date" not in plot_df.columns:
        raise ValueError("Volatility chart requires a Date column.")

    if maturity_col is not None and value_col is not None:
        long_df = plot_df.rename(columns={maturity_col: "Maturity", value_col: "Volatility"})
        long_df["Maturity"] = long_df["Maturity"].astype(str)
        long_df["Volatility"] = pd.to_numeric(long_df["Volatility"], errors="coerce")
        long_df = long_df.dropna(subset=["Volatility"])
        return long_df[["Date", "Maturity", "Volatility"]].sort_values(["Date", "Maturity"])

    value_columns = [column for column in plot_df.columns if column != "Date"]
    if not value_columns:
        raise ValueError("Volatility chart requires at least one volatility series.")

    long_df = plot_df.melt(
        id_vars="Date",
        value_vars=value_columns,
        var_name="Maturity",
        value_name="Volatility",
    )
    long_df["Maturity"] = long_df["Maturity"].astype(str)
    long_df["Volatility"] = pd.to_numeric(long_df["Volatility"], errors="coerce")
    long_df = long_df.dropna(subset=["Volatility"]).sort_values(["Date", "Maturity"])
    return long_df


def build_volatility_chart(
    volatility_points: pd.DataFrame,
    *,
    maturity_order: Sequence[str] | None = None,
    title: str | None = None,
    height: int = 500,
) -> alt.Chart:
    plot_df = _coerce_volatility_points(volatility_points)
    if plot_df.empty:
        raise ValueError("Volatility chart received no rows after cleaning.")

    if maturity_order:
        order = [str(item) for item in maturity_order]
    else:
        order = sorted(plot_df["Maturity"].dropna().unique().tolist(), key=maturity_sort_key)

    color_scale = alt.Scale(
        domain=order,
        range=[INSTITUTIONAL_PALETTE[idx % len(INSTITUTIONAL_PALETTE)] for idx, _ in enumerate(order)],
    )

    return (
        alt.Chart(plot_df)
        .mark_line(strokeWidth=2.1)
        .encode(
            x=alt.X("Date:T", title="Date", axis=alt.Axis(grid=True, tickCount="year")),
            y=alt.Y("Volatility:Q", title="Volatility (bp)", axis=alt.Axis(grid=True)),
            color=alt.Color(
                "Maturity:N",
                sort=order,
                scale=color_scale,
                legend=alt.Legend(title="Maturity", orient="top"),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Maturity:N", title="Maturity"),
                alt.Tooltip("Volatility:Q", title="Volatility (bp)", format=".2f"),
            ],
        )
        .properties(
            height=height,
            title=title or "Rate Volatility",
        )
        .configure_axis(
            labelColor=AXIS_LABEL_COLOR,
            titleColor=AXIS_LABEL_COLOR,
            gridColor=GRID_COLOR,
        )
        .configure_title(
            color=TITLE_COLOR,
            fontSize=16,
            anchor="start",
        )
        .configure_view(strokeOpacity=0)
    )
