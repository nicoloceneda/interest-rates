import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Yield Curve of U.S. Treasuries", layout="wide")
alt.data_transformers.disable_max_rows()

DATA_PATH = Path("data/gurkaynak/extracted/yields.csv")
MATURITY_PATTERN = re.compile(r"^(\d+)y$")
HISTORICAL_BASE_COLORS = [
    "#4e79a7",
    "#2a9d8f",
    "#d73027",
    "#1a9850",
    "#f28e2b",
    "#e15759",
    "#76b7b2",
    "#59a14f",
    "#edc949",
    "#af7aa1",
]


def historical_slider_container():
    # Shift the historical range slider slightly to the right while keeping the
    # same slider length (left+right gutters stay constant).
    _, center, _ = st.columns([0.65, 18.0, 1.05])
    return center


def curve_slider_container():
    # Start the curve slider a bit later while preserving the right endpoint.
    _, right_aligned = st.columns([0.65, 19.45])
    return right_aligned


@st.cache_data(show_spinner=False)
def load_yields(path_str: str):
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    raw_df = pd.read_csv(path)
    if "Date" not in raw_df.columns:
        raise ValueError("Input data must contain a 'Date' column.")

    raw_df["Date"] = pd.to_datetime(raw_df["Date"], errors="coerce")
    raw_df = raw_df.dropna(subset=["Date"])

    maturity_pairs = []
    for column in raw_df.columns:
        match = MATURITY_PATTERN.match(str(column))
        if match:
            maturity_pairs.append((int(match.group(1)), str(column)))

    if not maturity_pairs:
        raise ValueError("Input data must contain maturity columns named like '1y', '2y', ...")

    maturity_pairs.sort(key=lambda item: item[0])
    ordered_maturities = [column for _, column in maturity_pairs]

    curve_table = (
        raw_df[["Date", *ordered_maturities]]
        .sort_values("Date")
        .drop_duplicates(subset="Date", keep="last")
        .dropna(subset=ordered_maturities, how="all")
        .reset_index(drop=True)
    )
    if curve_table.empty:
        raise ValueError("No usable rows were found after parsing and cleaning the dataset.")

    historical_table = curve_table.melt(
        id_vars="Date",
        value_vars=ordered_maturities,
        var_name="Maturity",
        value_name="Yield",
    )
    historical_table["MaturityYears"] = (
        historical_table["Maturity"].str.extract(r"(\d+)").astype(int)
    )
    historical_table = (
        historical_table.dropna(subset=["Yield"])
        .sort_values(["Date", "MaturityYears"])
        .reset_index(drop=True)
    )
    if historical_table.empty:
        raise ValueError("No non-missing yield values were found in the dataset.")

    return curve_table, ordered_maturities, historical_table


def build_palette(n_colors: int):
    return [HISTORICAL_BASE_COLORS[idx % len(HISTORICAL_BASE_COLORS)] for idx in range(n_colors)]


st.markdown(
    """
    <style>
        .main {background-color: #f8f9fb;}
        .block-container {padding-top: 2rem;}
        h1, h2, h3 {font-family: "Segoe UI", sans-serif;}
        .stMetric {background-color: #ffffff; border-radius: 12px; padding: 12px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Yield Curve of U.S. Treasuries")
st.caption("Analysis of the Yield Curve of U.S. Treasuries")

try:
    curve_table, maturity_columns, historical_table = load_yields(str(DATA_PATH))
except FileNotFoundError:
    st.error(
        "Could not find `data/gurkaynak/extracted/yields.csv`. "
        "Run `python data.py` first to download and extract the data."
    )
    st.stop()
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load yield data: {exc}")
    st.stop()

available_dates = curve_table["Date"].dt.to_pydatetime().tolist()
latest_date = available_dates[-1]

curve_tab, historical_tab = st.tabs(["Curve", "Historical"])

with curve_tab:
    st.subheader("Current Yield Curve")
    curve_chart_slot = st.empty()

    with curve_slider_container():
        selected_curve_date = st.select_slider(
            "Date",
            options=available_dates,
            value=latest_date,
            format_func=lambda value: value.strftime("%Y-%m-%d"),
            key="curve_date_selector",
        )

    selected_curve_points = historical_table[
        historical_table["Date"] == pd.Timestamp(selected_curve_date)
    ]

    if selected_curve_points.empty:
        curve_chart_slot.info("No yield values were found for the selected date.")
    else:
        curve_chart = (
            alt.Chart(selected_curve_points)
            .mark_line(point=True, color="#4e79a7")
            .encode(
                x=alt.X(
                    "MaturityYears:Q",
                    title="Maturity (Years)",
                    scale=alt.Scale(domain=[1, 30], nice=False),
                    axis=alt.Axis(tickMinStep=1),
                ),
                y=alt.Y("Yield:Q", title="Yield (%)"),
                tooltip=[
                    alt.Tooltip("Date:T", title="Date"),
                    alt.Tooltip("Maturity:N", title="Maturity"),
                    alt.Tooltip("Yield:Q", title="Yield (%)", format=".4f"),
                ],
            )
            .properties(height=430)
        )
        curve_chart_slot.altair_chart(curve_chart, use_container_width=True)

with historical_tab:
    st.subheader("Historical Yields")
    default_maturities = [item for item in ["2y", "10y", "30y"] if item in maturity_columns]

    selected_maturities = st.multiselect(
        "Maturities",
        options=maturity_columns,
        default=default_maturities,
        key="historical_maturity_selector",
    )

    historical_chart_slot = st.empty()

    with historical_slider_container():
        selected_date_range = st.select_slider(
            "Date range",
            options=available_dates,
            value=(available_dates[0], latest_date),
            format_func=lambda value: value.strftime("%Y-%m-%d"),
            key="historical_date_range_selector",
        )

    if not selected_maturities:
        historical_chart_slot.info("Select at least one maturity to display historical yields.")
    else:
        start_date, end_date = selected_date_range
        historical_filtered = historical_table[
            historical_table["Maturity"].isin(selected_maturities)
            & (historical_table["Date"] >= pd.Timestamp(start_date))
            & (historical_table["Date"] <= pd.Timestamp(end_date))
        ].copy()

        if historical_filtered.empty:
            historical_chart_slot.info("No observations are available for the selected filters.")
        else:
            maturity_order = sorted(
                selected_maturities,
                key=lambda maturity: int(maturity.rstrip("y")),
            )
            color_scale = alt.Scale(
                domain=maturity_order,
                range=build_palette(len(maturity_order)),
            )

            historical_chart = (
                alt.Chart(historical_filtered)
                .mark_line()
                .encode(
                    x=alt.X(
                        "Date:T",
                        title="Date",
                        axis=alt.Axis(grid=True, tickCount="year"),
                    ),
                    y=alt.Y(
                        "Yield:Q",
                        title="Yield (%)",
                        axis=alt.Axis(grid=True),
                    ),
                    color=alt.Color(
                        "Maturity:N",
                        sort=maturity_order,
                        scale=color_scale,
                        legend=alt.Legend(title="Maturity"),
                    ),
                    tooltip=[
                        alt.Tooltip("Date:T", title="Date"),
                        alt.Tooltip("Maturity:N", title="Maturity"),
                        alt.Tooltip("Yield:Q", title="Yield (%)", format=".4f"),
                    ],
                )
                .properties(height=430)
            )
            historical_chart_slot.altair_chart(historical_chart, use_container_width=True)
