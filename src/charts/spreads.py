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
    pick_first_existing,
)


def _coerce_spread_points(spread_points: pd.DataFrame) -> pd.DataFrame:
    plot_df = coerce_date_column(spread_points)
    spread_col = pick_first_existing(plot_df.columns, ["Spread", "spread", "Series", "series", "Name", "name"])
    value_col = pick_first_existing(plot_df.columns, ["Value", "value", "SpreadValue", "spread_value", "Yield", "yield"])
    if "Date" not in plot_df.columns:
        raise ValueError("Spread chart requires a Date column.")

    if spread_col is not None and value_col is not None:
        long_df = plot_df.rename(columns={spread_col: "Spread", value_col: "Value"})
        long_df["Spread"] = long_df["Spread"].astype(str)
        long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
        long_df = long_df.dropna(subset=["Value"])
        return long_df[["Date", "Spread", "Value"]].sort_values(["Date", "Spread"])

    value_columns = [column for column in plot_df.columns if column != "Date"]
    if not value_columns:
        raise ValueError("Spread chart requires at least one spread series.")
    long_df = plot_df.melt(
        id_vars="Date",
        value_vars=value_columns,
        var_name="Spread",
        value_name="Value",
    )
    long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
    long_df = long_df.dropna(subset=["Value"]).sort_values(["Date", "Spread"])
    return long_df


def build_spread_chart(
    spread_points: pd.DataFrame,
    *,
    spread_order: Sequence[str] | None = None,
    title: str | None = None,
    height: int = 500,
) -> alt.Chart:
    plot_df = _coerce_spread_points(spread_points)
    if plot_df.empty:
        raise ValueError("Spread chart received no rows after cleaning.")

    if spread_order:
        order = [str(item) for item in spread_order]
    else:
        order = sorted(plot_df["Spread"].dropna().unique().tolist())

    color_scale = alt.Scale(
        domain=order,
        range=[INSTITUTIONAL_PALETTE[idx % len(INSTITUTIONAL_PALETTE)] for idx, _ in enumerate(order)],
    )

    zero_rule = alt.Chart(pd.DataFrame({"Zero": [0.0]})).mark_rule(
        color="#6F7E8F",
        strokeDash=[6, 4],
    ).encode(y="Zero:Q")

    lines = (
        alt.Chart(plot_df)
        .mark_line(strokeWidth=2.1)
        .encode(
            x=alt.X("Date:T", title="Date", axis=alt.Axis(grid=True, tickCount="year")),
            y=alt.Y("Value:Q", title="Spread (pp)", axis=alt.Axis(grid=True)),
            color=alt.Color(
                "Spread:N",
                sort=order,
                scale=color_scale,
                legend=alt.Legend(title="Spread", orient="top"),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Spread:N", title="Spread"),
                alt.Tooltip("Value:Q", title="Spread (pp)", format=".3f"),
            ],
        )
    )

    return (
        (zero_rule + lines)
        .properties(
            height=height,
            title=title or "Yield Spreads",
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
