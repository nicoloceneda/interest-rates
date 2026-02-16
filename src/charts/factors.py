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


def _coerce_factor_points(factor_points: pd.DataFrame) -> pd.DataFrame:
    plot_df = coerce_date_column(factor_points)
    factor_col = pick_first_existing(plot_df.columns, ["Factor", "factor", "Series", "series", "Name", "name"])
    value_col = pick_first_existing(plot_df.columns, ["Value", "value", "FactorValue", "factor_value", "Score"])
    if "Date" not in plot_df.columns:
        raise ValueError("Factor chart requires a Date column.")

    if factor_col is not None and value_col is not None:
        long_df = plot_df.rename(columns={factor_col: "Factor", value_col: "Value"})
        long_df["Factor"] = long_df["Factor"].astype(str)
        long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
        long_df = long_df.dropna(subset=["Value"])
        return long_df[["Date", "Factor", "Value"]].sort_values(["Date", "Factor"])

    value_columns = [column for column in plot_df.columns if column != "Date"]
    if not value_columns:
        raise ValueError("Factor chart requires at least one factor series.")
    long_df = plot_df.melt(
        id_vars="Date",
        value_vars=value_columns,
        var_name="Factor",
        value_name="Value",
    )
    long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
    long_df = long_df.dropna(subset=["Value"]).sort_values(["Date", "Factor"])
    return long_df


def build_factor_chart(
    factor_points: pd.DataFrame,
    *,
    factor_order: Sequence[str] | None = None,
    title: str | None = None,
    height: int = 500,
) -> alt.Chart:
    plot_df = _coerce_factor_points(factor_points)
    if plot_df.empty:
        raise ValueError("Factor chart received no rows after cleaning.")

    if factor_order:
        order = [str(item) for item in factor_order]
    else:
        order = sorted(plot_df["Factor"].dropna().unique().tolist())

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
            y=alt.Y("Value:Q", title="Factor Value", axis=alt.Axis(grid=True)),
            color=alt.Color(
                "Factor:N",
                sort=order,
                scale=color_scale,
                legend=alt.Legend(title="Factor", orient="top"),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Factor:N", title="Factor"),
                alt.Tooltip("Value:Q", title="Value", format=".3f"),
            ],
        )
    )

    return (
        (zero_rule + lines)
        .properties(
            height=height,
            title=title or "Term Structure Factors",
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
