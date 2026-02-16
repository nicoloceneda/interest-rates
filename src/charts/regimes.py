from __future__ import annotations

import altair as alt
import pandas as pd

from . import (
    AXIS_LABEL_COLOR,
    GRID_COLOR,
    INSTITUTIONAL_PALETTE,
    REGIME_COLORS,
    TITLE_COLOR,
    coerce_date_column,
    pick_first_existing,
)


def _coerce_regime_points(regime_points: pd.DataFrame) -> pd.DataFrame:
    plot_df = coerce_date_column(regime_points)
    regime_col = pick_first_existing(plot_df.columns, ["Regime", "regime", "State", "state", "Label", "label"])
    if "Date" not in plot_df.columns or regime_col is None:
        raise ValueError("Regime chart requires Date and Regime-like columns.")
    plot_df = plot_df.rename(columns={regime_col: "Regime"})
    plot_df["Regime"] = plot_df["Regime"].astype(str)
    return plot_df[["Date", "Regime"]].dropna().sort_values("Date")


def _coerce_overlay_points(overlay_points: pd.DataFrame) -> pd.DataFrame:
    plot_df = coerce_date_column(overlay_points)
    value_col = pick_first_existing(plot_df.columns, ["Value", "value", "Yield", "yield", "Rate", "rate"])
    if "Date" not in plot_df.columns or value_col is None:
        raise ValueError("Overlay series requires Date and a numeric value column.")
    plot_df = plot_df.rename(columns={value_col: "Value"})
    plot_df["Value"] = pd.to_numeric(plot_df["Value"], errors="coerce")
    plot_df = plot_df.dropna(subset=["Value"]).sort_values("Date")
    return plot_df[["Date", "Value"]]


def build_regime_chart(
    regime_points: pd.DataFrame,
    *,
    overlay_points: pd.DataFrame | None = None,
    overlay_label: str = "Reference Yield (%)",
    title: str | None = None,
    height: int = 500,
) -> alt.Chart:
    regime_df = _coerce_regime_points(regime_points)
    if regime_df.empty:
        raise ValueError("Regime chart received no rows after cleaning.")

    regime_domain = regime_df["Regime"].dropna().unique().tolist()
    regime_range = [
        REGIME_COLORS.get(regime, INSTITUTIONAL_PALETTE[idx % len(INSTITUTIONAL_PALETTE)])
        for idx, regime in enumerate(regime_domain)
    ]
    strip_height = max(80, int(height * 0.22))

    strip_chart = (
        alt.Chart(regime_df)
        .mark_tick(thickness=10, size=56)
        .encode(
            x=alt.X("Date:T", title="Date", axis=alt.Axis(grid=False, labels=False, ticks=False)),
            color=alt.Color(
                "Regime:N",
                sort=regime_domain,
                scale=alt.Scale(domain=regime_domain, range=regime_range),
                legend=alt.Legend(title="Regime", orient="top"),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Regime:N", title="Regime"),
            ],
        )
        .properties(height=strip_height, title=title or "Rate Regimes")
    )

    if overlay_points is None or overlay_points.empty:
        return (
            strip_chart.configure_axis(
                labelColor=AXIS_LABEL_COLOR,
                titleColor=AXIS_LABEL_COLOR,
                gridColor=GRID_COLOR,
            )
            .configure_title(color=TITLE_COLOR, fontSize=16, anchor="start")
            .configure_view(strokeOpacity=0)
        )

    overlay_df = _coerce_overlay_points(overlay_points)
    line_height = max(220, height - strip_height - 14)
    line_chart = (
        alt.Chart(overlay_df)
        .mark_line(strokeWidth=2.2, color=INSTITUTIONAL_PALETTE[0])
        .encode(
            x=alt.X("Date:T", title="Date", axis=alt.Axis(grid=True, tickCount="year")),
            y=alt.Y("Value:Q", title=overlay_label, axis=alt.Axis(grid=True)),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Value:Q", title=overlay_label, format=".3f"),
            ],
        )
        .properties(height=line_height)
    )

    return (
        alt.vconcat(strip_chart, line_chart, spacing=8)
        .resolve_scale(x="shared")
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
