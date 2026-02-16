from __future__ import annotations

import altair as alt
import pandas as pd

from . import (
    AXIS_LABEL_COLOR,
    GRID_COLOR,
    TITLE_COLOR,
    coerce_date_column,
    maturity_sort_key,
    pick_first_existing,
)


def _coerce_heatmap_points(heatmap_points: pd.DataFrame) -> pd.DataFrame:
    plot_df = coerce_date_column(heatmap_points)
    if "Date" not in plot_df.columns:
        raise ValueError("Heatmap chart requires a Date column.")

    maturity_col = pick_first_existing(plot_df.columns, ["Maturity", "maturity", "Tenor", "tenor"])
    value_col = pick_first_existing(plot_df.columns, ["Yield", "yield", "Value", "value", "Rate", "rate"])

    if maturity_col is not None and value_col is not None:
        long_df = plot_df.rename(columns={maturity_col: "Maturity", value_col: "Value"})
        long_df["Maturity"] = long_df["Maturity"].astype(str)
        long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
        long_df = long_df.dropna(subset=["Value"])
        return long_df[["Date", "Maturity", "Value"]].sort_values(["Date", "Maturity"])

    value_columns = [column for column in plot_df.columns if column != "Date"]
    if not value_columns:
        raise ValueError("Heatmap chart requires maturity columns.")

    long_df = plot_df.melt(
        id_vars="Date",
        value_vars=value_columns,
        var_name="Maturity",
        value_name="Value",
    )
    long_df["Maturity"] = long_df["Maturity"].astype(str)
    long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
    long_df = long_df.dropna(subset=["Value"]).sort_values(["Date", "Maturity"])
    return long_df


def build_heatmap_chart(
    heatmap_points: pd.DataFrame,
    *,
    title: str | None = None,
    height: int = 560,
) -> alt.Chart:
    plot_df = _coerce_heatmap_points(heatmap_points)
    if plot_df.empty:
        raise ValueError("Heatmap chart received no rows after cleaning.")

    maturity_order = sorted(plot_df["Maturity"].dropna().unique().tolist(), key=maturity_sort_key)

    return (
        alt.Chart(plot_df)
        .mark_rect()
        .encode(
            x=alt.X("Date:T", title="Date", axis=alt.Axis(grid=False, tickCount="year")),
            y=alt.Y(
                "Maturity:N",
                title="Maturity",
                sort=maturity_order,
                axis=alt.Axis(grid=False),
            ),
            color=alt.Color(
                "Value:Q",
                title="Yield (%)",
                scale=alt.Scale(scheme="blues"),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Maturity:N", title="Maturity"),
                alt.Tooltip("Value:Q", title="Yield (%)", format=".3f"),
            ],
        )
        .properties(
            height=height,
            title=title or "Yield Surface Heatmap",
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
