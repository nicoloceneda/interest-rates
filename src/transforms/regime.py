"""Heatmap and regime-label transforms."""

from __future__ import annotations

import numpy as np
import pandas as pd


def prepare_heatmap_data(
    data: pd.DataFrame,
    *,
    date_col: str = "date",
    bucket_col: str = "maturity_years",
    value_col: str = "value",
    aggfunc: str = "mean",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """
    Prepare a date x bucket matrix for heatmap plotting.

    Rows are dates, columns are bucket labels (typically maturities or spread names).
    """
    missing = [col for col in (date_col, bucket_col, value_col) if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    frame = data[[date_col, bucket_col, value_col]].copy()
    frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce")
    frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")

    numeric_bucket = pd.to_numeric(frame[bucket_col], errors="coerce")
    non_null_bucket_count = frame[bucket_col].notna().sum()
    if non_null_bucket_count > 0 and numeric_bucket.notna().sum() == non_null_bucket_count:
        frame[bucket_col] = numeric_bucket
    else:
        frame[bucket_col] = frame[bucket_col].astype(str).str.strip()

    frame = frame.dropna(subset=[date_col, bucket_col])

    heatmap = frame.pivot_table(
        index=date_col,
        columns=bucket_col,
        values=value_col,
        aggfunc=aggfunc,
    )

    heatmap = heatmap.sort_index(axis=0)
    if isinstance(heatmap.columns, pd.Index):
        try:
            heatmap = heatmap.sort_index(axis=1)
        except TypeError:
            heatmap = heatmap.reindex(sorted(heatmap.columns, key=str), axis=1)

    if fill_value is not None:
        heatmap = heatmap.fillna(fill_value)
    return heatmap


def label_regimes(
    data: pd.DataFrame,
    *,
    slope_col: str = "slope",
    level_col: str = "level",
    volatility_col: str = "rolling_volatility",
    output_col: str = "regime",
    slope_flat_band: float = 0.10,
    level_low_quantile: float = 0.33,
    level_high_quantile: float = 0.67,
    volatility_high_quantile: float = 0.67,
) -> pd.DataFrame:
    """
    Label rate regimes using slope, level, and volatility.

    Output columns added:
    - curve_regime
    - level_regime
    - volatility_regime
    - regime (configurable name via `output_col`)
    """
    frame = data.copy()

    for quantile_name, quantile_value in (
        ("level_low_quantile", level_low_quantile),
        ("level_high_quantile", level_high_quantile),
        ("volatility_high_quantile", volatility_high_quantile),
    ):
        if not 0.0 <= float(quantile_value) <= 1.0:
            raise ValueError(f"`{quantile_name}` must be between 0 and 1.")

    slope = (
        pd.to_numeric(frame[slope_col], errors="coerce")
        if slope_col in frame.columns
        else pd.Series(np.nan, index=frame.index)
    )
    level = (
        pd.to_numeric(frame[level_col], errors="coerce")
        if level_col in frame.columns
        else pd.Series(np.nan, index=frame.index)
    )
    volatility = (
        pd.to_numeric(frame[volatility_col], errors="coerce")
        if volatility_col in frame.columns
        else pd.Series(np.nan, index=frame.index)
    )

    level_non_null = level.dropna()
    vol_non_null = volatility.dropna()

    low_level_threshold = (
        float(level_non_null.quantile(level_low_quantile))
        if len(level_non_null) > 0
        else float("nan")
    )
    high_level_threshold = (
        float(level_non_null.quantile(level_high_quantile))
        if len(level_non_null) > 0
        else float("nan")
    )
    high_vol_threshold = (
        float(vol_non_null.quantile(volatility_high_quantile))
        if len(vol_non_null) > 0
        else float("nan")
    )

    abs_band = abs(float(slope_flat_band))

    def _curve_state(value: float) -> str:
        if pd.isna(value):
            return "unknown_curve"
        if value < -abs_band:
            return "inverted"
        if value > abs_band:
            return "steep"
        return "flat"

    def _level_state(value: float) -> str:
        if pd.isna(value) or pd.isna(low_level_threshold) or pd.isna(high_level_threshold):
            return "unknown_level"
        if value <= low_level_threshold:
            return "low"
        if value >= high_level_threshold:
            return "high"
        return "mid"

    def _vol_state(value: float) -> str:
        if pd.isna(value) or pd.isna(high_vol_threshold):
            return "unknown_vol"
        if value >= high_vol_threshold:
            return "high_vol"
        return "calm"

    curve_state = slope.map(_curve_state)
    level_state = level.map(_level_state)
    vol_state = volatility.map(_vol_state)

    def _combined_regime(curve: str, level_lbl: str, vol_lbl: str) -> str:
        if "unknown" in curve or "unknown" in level_lbl or "unknown" in vol_lbl:
            return "unknown"
        if curve == "inverted" and vol_lbl == "high_vol":
            return "risk_off"
        if curve == "inverted":
            return "inversion"
        if curve == "steep" and level_lbl == "low":
            return "reflation"
        if curve == "flat" and level_lbl == "high":
            return "tight_policy"
        if vol_lbl == "high_vol":
            return "volatile"
        return "normal"

    frame["curve_regime"] = curve_state
    frame["level_regime"] = level_state
    frame["volatility_regime"] = vol_state
    frame[output_col] = [
        _combined_regime(curve, level_lbl, vol_lbl)
        for curve, level_lbl, vol_lbl in zip(curve_state, level_state, vol_state)
    ]
    return frame
