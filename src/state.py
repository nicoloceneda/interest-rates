"""Canonical dashboard state contracts and builders."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.transforms import (
    calculate_spreads,
    compute_rolling_volatility,
    extract_level_slope_curvature,
    label_regimes,
)

MATURITY_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)([myMY])$")


@dataclass(frozen=True)
class DashboardState:
    """Container for all validated dataframes consumed by dashboard tabs."""

    curve_table: pd.DataFrame
    historical_table: pd.DataFrame
    available_dates: list[pd.Timestamp]
    maturity_columns: list[str]
    spreads_table: pd.DataFrame
    factors_wide: pd.DataFrame
    factors_long: pd.DataFrame
    heatmap_levels: pd.DataFrame
    heatmap_changes: pd.DataFrame
    volatility_table: pd.DataFrame
    regimes_table: pd.DataFrame
    macro_table: pd.DataFrame
    fred_errors: dict[str, str]


def _parse_maturity_years(label: str) -> float | None:
    match = MATURITY_PATTERN.match(str(label).strip())
    if not match:
        return None
    amount = float(match.group(1))
    unit = match.group(2).lower()
    if unit == "m":
        return amount / 12.0
    return amount


def _sorted_maturity_columns(columns: list[str]) -> list[str]:
    parsed_pairs: list[tuple[float, str]] = []
    for column in columns:
        parsed = _parse_maturity_years(column)
        if parsed is not None:
            parsed_pairs.append((parsed, column))
    parsed_pairs.sort(key=lambda item: item[0])
    return [column for _, column in parsed_pairs]


def load_gsw_state(data_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[pd.Timestamp]]:
    """Load the local GSW dataset and return wide/long canonical tables."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    raw_df = pd.read_csv(path)
    if "Date" not in raw_df.columns:
        raise ValueError("Input data must contain a 'Date' column.")

    raw_df["Date"] = pd.to_datetime(raw_df["Date"], errors="coerce")
    raw_df = raw_df.dropna(subset=["Date"])
    maturity_columns = _sorted_maturity_columns(raw_df.columns.tolist())
    if not maturity_columns:
        raise ValueError("Input data must contain maturity columns like '1y', '2y', ...")

    curve_table = (
        raw_df[["Date", *maturity_columns]]
        .sort_values("Date")
        .drop_duplicates(subset="Date", keep="last")
        .dropna(subset=maturity_columns, how="all")
        .reset_index(drop=True)
    )
    if curve_table.empty:
        raise ValueError("No usable rows were found after parsing and cleaning the GSW dataset.")

    historical_table = curve_table.melt(
        id_vars="Date",
        value_vars=maturity_columns,
        var_name="Maturity",
        value_name="Yield",
    )
    historical_table["MaturityYears"] = historical_table["Maturity"].map(_parse_maturity_years)
    historical_table["Yield"] = pd.to_numeric(historical_table["Yield"], errors="coerce")
    historical_table = (
        historical_table.dropna(subset=["MaturityYears", "Yield"])
        .sort_values(["Date", "MaturityYears"])
        .reset_index(drop=True)
    )
    if historical_table.empty:
        raise ValueError("No non-missing yield values were found in the GSW dataset.")

    available_dates = curve_table["Date"].drop_duplicates().sort_values().tolist()
    return curve_table, historical_table, maturity_columns, available_dates


def _to_transform_input(historical_table: pd.DataFrame) -> pd.DataFrame:
    return historical_table.rename(
        columns={
            "Date": "date",
            "MaturityYears": "maturity_years",
            "Yield": "value",
        }
    )[["date", "maturity_years", "value"]]


def _build_heatmap_changes(curve_table: pd.DataFrame, maturity_columns: list[str]) -> pd.DataFrame:
    if curve_table.empty or not maturity_columns:
        return pd.DataFrame(columns=["Date", "Maturity", "Value"])

    changes = curve_table[["Date", *maturity_columns]].copy()
    changes[maturity_columns] = changes[maturity_columns].diff() * 100.0
    long_changes = changes.melt(
        id_vars="Date",
        value_vars=maturity_columns,
        var_name="Maturity",
        value_name="Value",
    )
    long_changes["Value"] = pd.to_numeric(long_changes["Value"], errors="coerce")
    return long_changes.dropna(subset=["Value"]).sort_values(["Date", "Maturity"])


def _build_volatility_table(
    transform_input: pd.DataFrame,
    maturity_columns: list[str],
    window: int,
) -> pd.DataFrame:
    if transform_input.empty:
        return pd.DataFrame(columns=["Date", "Maturity", "MaturityYears", "Volatility"])

    pivot = (
        transform_input.pivot_table(
            index="date",
            columns="maturity_years",
            values="value",
            aggfunc="mean",
        )
        .sort_index(axis=0)
        .sort_index(axis=1)
    )
    daily_changes = pivot.diff() * 100.0
    try:
        stacked = daily_changes.stack(future_stack=True)
    except (TypeError, ValueError):
        stacked = daily_changes.stack(dropna=False)
    long_changes = stacked.reset_index(name="value")
    long_changes = long_changes.rename(columns={"date": "date", "maturity_years": "maturity_years"})
    vol_input = long_changes.dropna(subset=["date", "maturity_years"]).copy()
    min_periods = max(5, min(window, 10))
    vol = compute_rolling_volatility(
        vol_input,
        value_col="value",
        date_col="date",
        group_cols=["maturity_years"],
        window=window,
        min_periods=min_periods,
        annualize=False,
        output_col="volatility",
    )
    vol = vol.dropna(subset=["volatility"]).copy()
    vol["Date"] = pd.to_datetime(vol["date"], errors="coerce")
    vol["MaturityYears"] = pd.to_numeric(vol["maturity_years"], errors="coerce")

    year_to_label = {round(_parse_maturity_years(col) or 0.0, 8): col for col in maturity_columns}
    vol["Maturity"] = vol["MaturityYears"].map(
        lambda value: year_to_label.get(round(float(value), 8), f"{float(value):g}y")
    )
    vol["Volatility"] = pd.to_numeric(vol["volatility"], errors="coerce")
    return vol[["Date", "Maturity", "MaturityYears", "Volatility"]].dropna(subset=["Date", "Volatility"])


def _build_regimes_table(
    factors_wide: pd.DataFrame,
    volatility_table: pd.DataFrame,
) -> pd.DataFrame:
    if factors_wide.empty:
        return pd.DataFrame(columns=["Date", "Regime"])

    regime_input = factors_wide.rename(
        columns={"Date": "date", "Level": "level", "Slope": "slope"}
    )[["date", "level", "slope"]].copy()

    if not volatility_table.empty:
        volatility_reference = (
            volatility_table.sort_values("Date")
            .dropna(subset=["MaturityYears"])
            .copy()
        )
        volatility_reference["dist_to_10"] = (volatility_reference["MaturityYears"] - 10.0).abs()
        best_maturity = (
            volatility_reference.groupby("MaturityYears")["dist_to_10"].mean().sort_values().index
        )
        if len(best_maturity) > 0:
            target_maturity = float(best_maturity[0])
            selected = volatility_reference[volatility_reference["MaturityYears"] == target_maturity]
            selected = selected.rename(columns={"Date": "date", "Volatility": "rolling_volatility"})
            regime_input = regime_input.merge(
                selected[["date", "rolling_volatility"]],
                on="date",
                how="left",
            )
    if "rolling_volatility" not in regime_input.columns:
        regime_input["rolling_volatility"] = float("nan")

    labeled = label_regimes(
        regime_input,
        slope_col="slope",
        level_col="level",
        volatility_col="rolling_volatility",
        output_col="regime",
    )
    label_map = {
        "risk_off": "Risk-Off",
        "inversion": "Inversion",
        "reflation": "Steepening",
        "tight_policy": "Restrictive",
        "volatile": "Volatile",
        "normal": "Neutral",
        "unknown": "Unknown",
    }
    labeled["Regime"] = labeled["regime"].map(label_map).fillna("Unknown")
    labeled["Date"] = pd.to_datetime(labeled["date"], errors="coerce")
    labeled["Level"] = pd.to_numeric(labeled["level"], errors="coerce")
    labeled["Slope"] = pd.to_numeric(labeled["slope"], errors="coerce")
    labeled["Volatility"] = pd.to_numeric(labeled["rolling_volatility"], errors="coerce")
    return labeled[
        [
            "Date",
            "Regime",
            "Level",
            "Slope",
            "Volatility",
            "curve_regime",
            "level_regime",
            "volatility_regime",
        ]
    ].sort_values("Date")


def build_dashboard_state(
    *,
    curve_table: pd.DataFrame,
    historical_table: pd.DataFrame,
    maturity_columns: list[str],
    available_dates: list[pd.Timestamp],
    macro_table: pd.DataFrame,
    fred_errors: dict[str, str],
    spread_definitions: tuple[tuple[str, tuple[float, float]], ...],
    volatility_window_days: int,
) -> DashboardState:
    """Build derived analytics tables for all dashboard tabs."""
    transform_input = _to_transform_input(historical_table)

    spread_map = {name: value for name, value in spread_definitions}
    spreads = calculate_spreads(
        transform_input,
        spread_definitions=spread_map,
        date_col="date",
        maturity_col="maturity_years",
        value_col="value",
    )
    spreads_table = spreads.rename(
        columns={"date": "Date", "spread": "Spread", "value": "Value"}
    )[["Date", "Spread", "Value"]]

    factors = extract_level_slope_curvature(
        transform_input,
        date_col="date",
        maturity_col="maturity_years",
        value_col="value",
        level_maturity=10.0,
        slope_short_maturity=2.0,
        slope_long_maturity=10.0,
        curvature_short_maturity=2.0,
        curvature_mid_maturity=5.0,
        curvature_long_maturity=10.0,
    )
    factors_wide = factors.rename(
        columns={"date": "Date", "level": "Level", "slope": "Slope", "curvature": "Curvature"}
    )[["Date", "Level", "Slope", "Curvature"]]
    factors_long = factors_wide.melt(
        id_vars=["Date"],
        value_vars=["Level", "Slope", "Curvature"],
        var_name="Factor",
        value_name="Value",
    )

    heatmap_levels = historical_table.rename(columns={"Yield": "Value"})[
        ["Date", "Maturity", "Value"]
    ].copy()
    heatmap_changes = _build_heatmap_changes(curve_table, maturity_columns)
    volatility_table = _build_volatility_table(transform_input, maturity_columns, volatility_window_days)
    regimes_table = _build_regimes_table(factors_wide, volatility_table)

    return DashboardState(
        curve_table=curve_table,
        historical_table=historical_table,
        available_dates=available_dates,
        maturity_columns=maturity_columns,
        spreads_table=spreads_table,
        factors_wide=factors_wide,
        factors_long=factors_long,
        heatmap_levels=heatmap_levels,
        heatmap_changes=heatmap_changes,
        volatility_table=volatility_table,
        regimes_table=regimes_table,
        macro_table=macro_table,
        fred_errors=fred_errors,
    )
