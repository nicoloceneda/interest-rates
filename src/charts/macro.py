from __future__ import annotations

import altair as alt
import pandas as pd

from . import AXIS_LABEL_COLOR, GRID_COLOR, INSTITUTIONAL_PALETTE, TITLE_COLOR


def build_macro_context_chart(
    macro_points: pd.DataFrame,
    *,
    x_field: str,
    y_field: str,
    series_field: str | None = None,
    color_field: str | None = None,
    kind: str = "line",
    title: str | None = None,
    height: int = 500,
) -> alt.Chart:
    if x_field not in macro_points.columns or y_field not in macro_points.columns:
        raise ValueError("Macro chart requires the specified x_field and y_field.")

    plot_df = macro_points.copy()
    if x_field.lower() == "date":
        plot_df[x_field] = pd.to_datetime(plot_df[x_field], errors="coerce")
    plot_df[y_field] = pd.to_numeric(plot_df[y_field], errors="coerce")
    plot_df = plot_df.dropna(subset=[x_field, y_field])
    if plot_df.empty:
        raise ValueError("Macro chart received no rows after cleaning.")

    if kind == "scatter":
        encodings: dict[str, alt.Color | alt.X | alt.Y | list[alt.Tooltip]] = {
            "x": alt.X(f"{x_field}:Q" if x_field.lower() != "date" else f"{x_field}:T", title=x_field),
            "y": alt.Y(f"{y_field}:Q", title=y_field),
            "tooltip": [
                alt.Tooltip(f"{x_field}:Q" if x_field.lower() != "date" else f"{x_field}:T", title=x_field),
                alt.Tooltip(f"{y_field}:Q", title=y_field, format=".3f"),
            ],
        }
        if color_field and color_field in plot_df.columns:
            if pd.api.types.is_numeric_dtype(plot_df[color_field]):
                encodings["color"] = alt.Color(f"{color_field}:Q", title=color_field, scale=alt.Scale(scheme="blues"))
            else:
                encodings["color"] = alt.Color(f"{color_field}:N", title=color_field)
                encodings["tooltip"].append(alt.Tooltip(f"{color_field}:N", title=color_field))
        chart = alt.Chart(plot_df).mark_circle(size=70, opacity=0.78).encode(**encodings)
    else:
        x_type = "T" if x_field.lower() == "date" else "Q"
        line_encodings: dict[str, alt.Color | alt.X | alt.Y | list[alt.Tooltip]] = {
            "x": alt.X(f"{x_field}:{x_type}", title=x_field, axis=alt.Axis(grid=True, tickCount="year")),
            "y": alt.Y(f"{y_field}:Q", title=y_field, axis=alt.Axis(grid=True)),
            "tooltip": [
                alt.Tooltip(f"{x_field}:{x_type}", title=x_field),
                alt.Tooltip(f"{y_field}:Q", title=y_field, format=".3f"),
            ],
        }
        if series_field and series_field in plot_df.columns:
            series_domain = plot_df[series_field].dropna().astype(str).unique().tolist()
            line_encodings["color"] = alt.Color(
                f"{series_field}:N",
                sort=series_domain,
                scale=alt.Scale(
                    domain=series_domain,
                    range=[
                        INSTITUTIONAL_PALETTE[idx % len(INSTITUTIONAL_PALETTE)]
                        for idx, _ in enumerate(series_domain)
                    ],
                ),
                legend=alt.Legend(title=series_field, orient="top"),
            )
            line_encodings["tooltip"].append(alt.Tooltip(f"{series_field}:N", title=series_field))

        chart = alt.Chart(plot_df).mark_line(strokeWidth=2.1).encode(**line_encodings)

    return (
        chart.properties(
            height=height,
            title=title or "Macro Context",
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
