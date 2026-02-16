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


def _coerce_historical_points(historical_points: pd.DataFrame) -> pd.DataFrame:
    plot_df = coerce_date_column(historical_points)
    maturity_col = pick_first_existing(plot_df.columns, ["Maturity", "maturity", "Tenor", "tenor"])
    yield_col = pick_first_existing(plot_df.columns, ["Yield", "yield", "Rate", "rate", "Value", "value"])
    if maturity_col is None or yield_col is None or "Date" not in plot_df.columns:
        raise ValueError("Historical chart requires Date, Maturity, and Yield-like columns.")

    plot_df = plot_df.rename(columns={maturity_col: "Maturity", yield_col: "Yield"})
    plot_df["Maturity"] = plot_df["Maturity"].astype(str)
    plot_df["Yield"] = pd.to_numeric(plot_df["Yield"], errors="coerce")
    plot_df = plot_df.dropna(subset=["Yield"])
    plot_df = plot_df.sort_values(["Date", "Maturity"])
    return plot_df


def build_historical_chart(
    historical_points: pd.DataFrame,
    *,
    maturity_order: Sequence[str] | None = None,
    title: str | None = None,
    height: int = 500,
) -> alt.Chart:
    plot_df = _coerce_historical_points(historical_points)
    if plot_df.empty:
        raise ValueError("Historical chart received no rows after cleaning.")

    if maturity_order:
        order = [str(item) for item in maturity_order]
    else:
        order = sorted(plot_df["Maturity"].dropna().unique().tolist(), key=maturity_sort_key)

    color_scale = alt.Scale(
        domain=order,
        range=[INSTITUTIONAL_PALETTE[idx % len(INSTITUTIONAL_PALETTE)] for idx, _ in enumerate(order)],
    )

    hover = alt.selection_point(
        fields=["Date"],
        nearest=True,
        on="mouseover",
        empty=False,
        clear="mouseout",
    )

    base = alt.Chart(plot_df).encode(
        x=alt.X("Date:T", title="Date", axis=alt.Axis(grid=True, tickCount="year")),
        y=alt.Y("Yield:Q", title="Yield (%)", axis=alt.Axis(grid=True)),
        color=alt.Color(
            "Maturity:N",
            sort=order,
            scale=color_scale,
            legend=alt.Legend(title="Maturity", orient="top"),
        ),
    )

    lines = base.mark_line(strokeWidth=2.1)
    points = (
        base.mark_circle(size=45, filled=True)
        .encode(
            opacity=alt.condition(hover, alt.value(1), alt.value(0)),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Maturity:N", title="Maturity"),
                alt.Tooltip("Yield:Q", title="Yield (%)", format=".3f"),
            ],
        )
        .add_params(hover)
    )
    rule = (
        alt.Chart(plot_df)
        .mark_rule(color="#97A3B3")
        .encode(x="Date:T")
        .transform_filter(hover)
    )

    return (
        (lines + points + rule)
        .properties(
            height=height,
            title=title or "Historical Yield Curves",
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
