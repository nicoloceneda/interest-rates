"""Term-structure factor transforms."""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd


def _validate_columns(frame: pd.DataFrame, required: Sequence[str]) -> None:
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _pivot_curve(
    data: pd.DataFrame,
    *,
    date_col: str,
    maturity_col: str,
    value_col: str,
) -> pd.DataFrame:
    _validate_columns(data, [date_col, maturity_col, value_col])

    frame = data[[date_col, maturity_col, value_col]].copy()
    frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce")
    frame[maturity_col] = pd.to_numeric(frame[maturity_col], errors="coerce")
    frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
    frame = frame.dropna(subset=[date_col, maturity_col])

    pivot = frame.pivot_table(
        index=date_col,
        columns=maturity_col,
        values=value_col,
        aggfunc="mean",
    )
    pivot.columns = pd.to_numeric(pivot.columns, errors="coerce")
    pivot = pivot.loc[:, pd.Index(pivot.columns).notna()]
    return pivot.sort_index(axis=0).sort_index(axis=1)


def _nearest_maturity_column(
    columns: pd.Index,
    target_maturity: float,
    max_maturity_gap: float | None = None,
) -> float | None:
    numeric_columns = pd.to_numeric(columns, errors="coerce")
    valid_mask = pd.Index(numeric_columns).notna()
    if valid_mask.sum() == 0:
        return None

    valid_values = numeric_columns[valid_mask]
    distance = np.abs(valid_values - target_maturity)
    nearest_idx = int(np.argmin(distance))
    nearest_value = float(valid_values[nearest_idx])

    if max_maturity_gap is not None and distance[nearest_idx] > max_maturity_gap:
        return None
    return nearest_value


def _series_for_target_maturity(
    pivot: pd.DataFrame,
    target_maturity: float,
    max_maturity_gap: float | None,
) -> tuple[pd.Series, float]:
    nearest = _nearest_maturity_column(
        pivot.columns,
        target_maturity=target_maturity,
        max_maturity_gap=max_maturity_gap,
    )
    if nearest is None:
        return pd.Series(np.nan, index=pivot.index, dtype=float), float("nan")
    return pd.to_numeric(pivot[nearest], errors="coerce"), nearest


def extract_level_slope_curvature(
    data: pd.DataFrame,
    *,
    date_col: str = "date",
    maturity_col: str = "maturity_years",
    value_col: str = "value",
    level_maturity: float = 10.0,
    slope_short_maturity: float = 2.0,
    slope_long_maturity: float = 10.0,
    curvature_short_maturity: float = 2.0,
    curvature_mid_maturity: float = 5.0,
    curvature_long_maturity: float = 10.0,
    max_maturity_gap: float | None = None,
) -> pd.DataFrame:
    """
    Extract level, slope, curvature factors from long-form term-structure data.

    Definitions:
    - level = y(level_maturity)
    - slope = y(slope_long_maturity) - y(slope_short_maturity)
    - curvature = 2*y(curvature_mid_maturity)
                  - y(curvature_short_maturity)
                  - y(curvature_long_maturity)
    """
    pivot = _pivot_curve(
        data,
        date_col=date_col,
        maturity_col=maturity_col,
        value_col=value_col,
    )
    if pivot.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "level",
                "slope",
                "curvature",
                "level_maturity_used",
                "slope_short_maturity_used",
                "slope_long_maturity_used",
                "curvature_short_maturity_used",
                "curvature_mid_maturity_used",
                "curvature_long_maturity_used",
            ]
        )

    level, level_used = _series_for_target_maturity(
        pivot, level_maturity, max_maturity_gap
    )
    slope_short, slope_short_used = _series_for_target_maturity(
        pivot, slope_short_maturity, max_maturity_gap
    )
    slope_long, slope_long_used = _series_for_target_maturity(
        pivot, slope_long_maturity, max_maturity_gap
    )
    curve_short, curve_short_used = _series_for_target_maturity(
        pivot, curvature_short_maturity, max_maturity_gap
    )
    curve_mid, curve_mid_used = _series_for_target_maturity(
        pivot, curvature_mid_maturity, max_maturity_gap
    )
    curve_long, curve_long_used = _series_for_target_maturity(
        pivot, curvature_long_maturity, max_maturity_gap
    )

    result = pd.DataFrame(
        {
            "date": pivot.index,
            "level": level.to_numpy(),
            "slope": (slope_long - slope_short).to_numpy(),
            "curvature": (2.0 * curve_mid - curve_short - curve_long).to_numpy(),
            "level_maturity_used": level_used,
            "slope_short_maturity_used": slope_short_used,
            "slope_long_maturity_used": slope_long_used,
            "curvature_short_maturity_used": curve_short_used,
            "curvature_mid_maturity_used": curve_mid_used,
            "curvature_long_maturity_used": curve_long_used,
        }
    )
    return result.sort_values("date", kind="stable").reset_index(drop=True)


def compute_rolling_volatility(
    data: pd.DataFrame,
    *,
    value_col: str = "value",
    date_col: str = "date",
    group_cols: Sequence[str] | None = None,
    window: int = 21,
    min_periods: int | None = None,
    annualize: bool = False,
    periods_per_year: int = 252,
    output_col: str = "rolling_volatility",
) -> pd.DataFrame:
    """Compute rolling standard deviation with optional grouping and annualization."""
    if window <= 0:
        raise ValueError("`window` must be a positive integer.")
    if min_periods is not None and min_periods <= 0:
        raise ValueError("`min_periods` must be positive when provided.")

    _validate_columns(data, [value_col])
    frame = data.copy()
    frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")

    resolved_group_cols = [col for col in (group_cols or ()) if col in frame.columns]
    sort_cols = list(resolved_group_cols)
    if date_col in frame.columns:
        frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce")
        sort_cols.append(date_col)
    if sort_cols:
        frame = frame.sort_values(sort_cols, kind="stable").reset_index(drop=True)

    effective_min_periods = window if min_periods is None else min_periods

    if resolved_group_cols:
        rolling = frame.groupby(resolved_group_cols, dropna=False, sort=False)[
            value_col
        ].transform(
            lambda series: series.rolling(
                window=window,
                min_periods=effective_min_periods,
            ).std(ddof=0)
        )
    else:
        rolling = frame[value_col].rolling(
            window=window,
            min_periods=effective_min_periods,
        ).std(ddof=0)

    if annualize:
        rolling = rolling * float(np.sqrt(periods_per_year))

    frame[output_col] = rolling.astype(float)
    return frame
