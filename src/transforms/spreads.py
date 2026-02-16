"""Spread transforms for long-form yield data."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

DEFAULT_SPREAD_DEFINITIONS: dict[str, tuple[float, float]] = {
    "10y_2y": (10.0, 2.0),
    "30y_10y": (30.0, 10.0),
    "5y_2y": (5.0, 2.0),
}


def _validate_columns(frame: pd.DataFrame, required: list[str]) -> None:
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _build_curve_pivot(
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


def _nearest_column(
    columns: pd.Index,
    target: float,
    max_maturity_gap: float | None,
) -> float | None:
    numeric_columns = pd.to_numeric(columns, errors="coerce")
    valid_mask = pd.Index(numeric_columns).notna()
    if valid_mask.sum() == 0:
        return None

    valid_values = numeric_columns[valid_mask]
    distance = np.abs(valid_values - target)
    nearest_idx = int(np.argmin(distance))
    nearest_value = float(valid_values[nearest_idx])

    if max_maturity_gap is not None and distance[nearest_idx] > max_maturity_gap:
        return None
    return nearest_value


def _series_for_maturity(
    pivot: pd.DataFrame,
    target: float,
    max_maturity_gap: float | None,
) -> tuple[pd.Series, float]:
    nearest = _nearest_column(pivot.columns, target, max_maturity_gap)
    if nearest is None:
        return pd.Series(np.nan, index=pivot.index, dtype=float), float("nan")
    return pd.to_numeric(pivot[nearest], errors="coerce"), nearest


def calculate_spreads(
    data: pd.DataFrame,
    spread_definitions: Mapping[str, tuple[float, float]] | None = None,
    *,
    date_col: str = "date",
    maturity_col: str = "maturity_years",
    value_col: str = "value",
    max_maturity_gap: float | None = None,
    dropna_values: bool = True,
) -> pd.DataFrame:
    """
    Calculate named spreads from long-form curve data.

    `spread_definitions` values are (long_maturity, short_maturity).
    """
    definitions = dict(spread_definitions or DEFAULT_SPREAD_DEFINITIONS)
    if not definitions:
        return pd.DataFrame(
            columns=[
                "date",
                "spread",
                "value",
                "long_maturity_target",
                "short_maturity_target",
                "long_maturity_used",
                "short_maturity_used",
            ]
        )

    pivot = _build_curve_pivot(
        data,
        date_col=date_col,
        maturity_col=maturity_col,
        value_col=value_col,
    )
    if pivot.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "spread",
                "value",
                "long_maturity_target",
                "short_maturity_target",
                "long_maturity_used",
                "short_maturity_used",
            ]
        )

    spread_frames: list[pd.DataFrame] = []
    for spread_name, maturities in definitions.items():
        if len(maturities) != 2:
            raise ValueError(
                f"Spread definition for '{spread_name}' must be a (long, short) tuple."
            )
        long_target, short_target = float(maturities[0]), float(maturities[1])

        long_series, long_used = _series_for_maturity(
            pivot, long_target, max_maturity_gap
        )
        short_series, short_used = _series_for_maturity(
            pivot, short_target, max_maturity_gap
        )
        spread_values = long_series - short_series

        spread_frames.append(
            pd.DataFrame(
                {
                    "date": pivot.index,
                    "spread": str(spread_name),
                    "value": spread_values.to_numpy(),
                    "long_maturity_target": long_target,
                    "short_maturity_target": short_target,
                    "long_maturity_used": long_used,
                    "short_maturity_used": short_used,
                }
            )
        )

    result = pd.concat(spread_frames, ignore_index=True)
    if dropna_values:
        result = result[result["value"].notna()]

    return result.sort_values(["date", "spread"], kind="stable").reset_index(drop=True)
