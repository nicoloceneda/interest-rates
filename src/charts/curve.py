from __future__ import annotations

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


def _coerce_curve_points(curve_points: pd.DataFrame) -> pd.DataFrame:
    plot_df = coerce_date_column(curve_points)
    yield_col = pick_first_existing(plot_df.columns, ["Yield", "yield", "Rate", "rate", "Value", "value"])
    maturity_col = pick_first_existing(plot_df.columns, ["Maturity", "maturity", "Tenor", "tenor"])
    years_col = pick_first_existing(
        plot_df.columns,
        ["MaturityYears", "maturity_years", "Years", "years", "TenorYears", "tenor_years"],
    )

    if yield_col is None:
        raise ValueError("Curve chart requires a yield-like column.")
    if years_col is None and maturity_col is None:
        raise ValueError("Curve chart requires either maturity labels or maturity years.")

    if years_col is None and maturity_col is not None:
        plot_df["MaturityYears"] = (
            plot_df[maturity_col].astype(str).str.extract(r"([0-9]+(?:\.[0-9]+)?)").astype(float)
        )
        years_col = "MaturityYears"

    if maturity_col is None and years_col is not None:
        plot_df["Maturity"] = plot_df[years_col].map(
            lambda value: f"{int(value)}y" if pd.notna(value) else ""
        )
        maturity_col = "Maturity"

    plot_df = plot_df.dropna(subset=[yield_col, years_col])
    plot_df = plot_df.sort_values(years_col).reset_index(drop=True)
    plot_df["Maturity"] = plot_df[maturity_col].astype(str)
    plot_df["MaturityYears"] = pd.to_numeric(plot_df[years_col], errors="coerce")
    plot_df["Yield"] = pd.to_numeric(plot_df[yield_col], errors="coerce")
    plot_df = plot_df.dropna(subset=["MaturityYears", "Yield"])
    plot_df = plot_df.sort_values("MaturityYears")
    return plot_df


def build_curve_chart(
    curve_points: pd.DataFrame,
    *,
    title: str | None = None,
    height: int = 500,
) -> alt.Chart:
    plot_df = _coerce_curve_points(curve_points)
    if plot_df.empty:
        raise ValueError("Curve chart received no rows after cleaning.")

    x_domain = [float(plot_df["MaturityYears"].min()), float(plot_df["MaturityYears"].max())]
    if x_domain[0] == x_domain[1]:
        x_domain[1] = x_domain[0] + 1.0

    tooltip_fields: list[alt.Tooltip] = [
        alt.Tooltip("Maturity:N", title="Maturity"),
        alt.Tooltip("Yield:Q", title="Yield (%)", format=".3f"),
    ]
    if "Date" in plot_df.columns:
        tooltip_fields.insert(0, alt.Tooltip("Date:T", title="Date"))

    base = alt.Chart(plot_df).encode(
        x=alt.X(
            "MaturityYears:Q",
            title="Maturity (Years)",
            axis=alt.Axis(grid=True, tickMinStep=1),
            scale=alt.Scale(domain=x_domain, nice=False),
        ),
        y=alt.Y(
            "Yield:Q",
            title="Yield (%)",
            axis=alt.Axis(grid=True),
        ),
    )

    line = base.mark_line(
        color=INSTITUTIONAL_PALETTE[0],
        strokeWidth=2.8,
        interpolate="monotone",
    )
    points = base.mark_circle(size=62, color=INSTITUTIONAL_PALETTE[0]).encode(tooltip=tooltip_fields)

    return (
        (line + points)
        .properties(
            height=height,
            title=title or "Yield Curve Snapshot",
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
