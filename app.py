from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).resolve().parent / "data/gurkaynak/extracted/yields.csv"

st.set_page_config(page_title="Zero Coupon Yield", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600&family=Work+Sans:wght@300;400;500;600&display=swap');

:root {
  --bg: #f4f1ea;
  --bg-accent: #e9efe4;
  --card: rgba(255, 255, 255, 0.75);
  --ink: #1e221b;
  --muted: #58615a;
  --accent: #0e7c86;
  --accent-soft: rgba(14, 124, 134, 0.18);
}

.stApp {
  background:
    radial-gradient(1200px 500px at 12% 8%, rgba(14, 124, 134, 0.12), transparent 60%),
    radial-gradient(900px 400px at 88% 12%, rgba(199, 125, 43, 0.12), transparent 60%),
    linear-gradient(180deg, var(--bg-accent), var(--bg));
  color: var(--ink);
  font-family: "Work Sans", sans-serif;
}

header[data-testid="stHeader"] {
  background: #0c0d0f;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  position: relative;
}

header[data-testid="stHeader"]::after {
  content: "Zero Coupon Yield";
  position: absolute;
  left: 1.4rem;
  top: 50%;
  transform: translateY(-50%);
  color: #f6f2ea;
  font-family: "Space Grotesk", sans-serif;
  font-size: 0.9rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.block-container {
  max-width: 1200px;
  padding-top: 4.5rem;
  padding-bottom: 2.5rem;
}

.date-pill {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: var(--card);
  border: 1px solid rgba(30, 34, 27, 0.12);
  color: var(--ink);
  font-size: 0.95rem;
  letter-spacing: 0.02em;
  box-shadow: 0 10px 25px rgba(30, 34, 27, 0.08);
  margin-bottom: 0.9rem;
}

.primary-wrap {
  display: flex;
  justify-content: flex-end;
}

div[data-testid="stCheckbox"] {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-top: 0;
  padding-right: 0.25rem;
  height: 2.1rem;
}

div[data-testid="stCheckbox"] label {
  padding: 0;
}

div[data-testid="stTextInput"] {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: var(--card);
  border-radius: 999px;
  border: 1px solid rgba(30, 34, 27, 0.12);
  padding: 0.35rem 0.75rem;
  box-shadow: 0 10px 25px rgba(30, 34, 27, 0.08);
  width: fit-content;
  font-size: 0.95rem;
  line-height: 1.4rem;
}

div[data-testid="stTextInput"]::before {
  content: "Secondary:";
  position: static;
  transform: none;
  display: inline-block;
  align-self: center;
  color: var(--ink);
  font-size: inherit;
  line-height: 1.4rem;
  letter-spacing: 0.02em;
}

div[data-testid="stTextInput"] input {
  border: none;
  background: transparent;
  padding: 0;
  font-size: inherit;
  color: var(--ink);
  width: 10ch;
  line-height: 1.4rem;
  height: 1.4rem;
  margin: 0;
}

div[data-testid="stTextInput"] div[data-baseweb="input"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  width: auto !important;
  flex: 0 0 auto !important;
  padding: 0 !important;
  min-height: unset !important;
  height: auto !important;
  align-items: center !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"] > div {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  min-height: unset !important;
  height: auto !important;
  align-items: center !important;
}

div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
  background: transparent !important;
  width: auto !important;
  padding: 0 !important;
  min-height: unset !important;
  height: auto !important;
  align-items: center !important;
}

div[data-testid="stTextInput"] input {
  background-color: transparent !important;
}

div[data-testid="stTextInput"] input::placeholder {
  color: var(--muted);
  opacity: 0.65;
}

div[data-testid="stPyplot"] {
  background: var(--card);
  border-radius: 18px;
  border: 1px solid rgba(30, 34, 27, 0.08);
  padding: 1rem 1.2rem 0.6rem 1.2rem;
  box-shadow: 0 18px 40px rgba(30, 34, 27, 0.08);
}

div[data-testid="stSlider"] {
  background: var(--card);
  border-radius: 16px;
  border: 1px solid rgba(30, 34, 27, 0.08);
  padding: 0.5rem 1rem 0.25rem 1rem;
  box-shadow: 0 12px 24px rgba(30, 34, 27, 0.08);
  margin-top: 0.35rem;
}

div[data-testid="stSlider"] label {
  color: var(--muted);
  font-size: 0.9rem;
}

div[data-baseweb="slider"] [role="slider"] {
  background-color: var(--accent);
  box-shadow: 0 0 0 6px var(--accent-soft);
  border: 2px solid #ffffff;
}

div[data-baseweb="slider"] > div > div > div {
  background-color: var(--accent);
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_yields(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date"])
    df = df.set_index("Date").sort_index()
    return df


if not DATA_PATH.exists():
    st.error(f"Missing data file: {DATA_PATH.as_posix()}")
    st.stop()

df_yields = load_yields(DATA_PATH)
if df_yields.empty:
    st.error("Yield curve data is empty.")
    st.stop()

date_options = df_yields.index.to_pydatetime()
default_date = date_options[-1]
state_key = "date_slider"

if state_key not in st.session_state:
    st.session_state[state_key] = default_date
elif st.session_state[state_key] not in date_options:
    st.session_state[state_key] = default_date

selected_date = st.session_state[state_key]

secondary_default = (
    df_yields.index[-2] if len(df_yields.index) > 1 else df_yields.index[-1]
)
secondary_default_str = secondary_default.strftime("%d/%m/%Y")
secondary_key = "secondary_date_str"
secondary_value_key = "secondary_date_value"

if secondary_key not in st.session_state:
    st.session_state[secondary_key] = secondary_default_str
if secondary_value_key not in st.session_state:
    st.session_state[secondary_value_key] = secondary_default


def parse_secondary_date(value: str) -> pd.Timestamp | None:
    try:
        parsed = datetime.strptime(value, "%d/%m/%Y")
    except ValueError:
        return None
    return pd.Timestamp(parsed)


def closest_available_before(
    index: pd.DatetimeIndex, target: pd.Timestamp
) -> pd.Timestamp:
    pos = index.searchsorted(target, side="right") - 1
    if pos < 0:
        pos = 0
    return index[pos]


raw_secondary = st.session_state[secondary_key].strip()
if len(raw_secondary) == 10:
    parsed_secondary = parse_secondary_date(raw_secondary)
    if parsed_secondary is not None:
        adjusted_secondary = closest_available_before(df_yields.index, parsed_secondary)
        st.session_state[secondary_value_key] = adjusted_secondary
        adjusted_secondary_str = adjusted_secondary.strftime("%d/%m/%Y")
        if raw_secondary != adjusted_secondary_str:
            st.session_state[secondary_key] = adjusted_secondary_str

top_row = st.columns([0.7, 0.08, 1.5], gap="small")
display_date = selected_date.strftime("%d/%m/%Y")
top_row[0].markdown(
    f'<div class="primary-wrap"><div class="date-pill">Primary: {display_date}</div></div>',
    unsafe_allow_html=True,
)
show_secondary = top_row[1].checkbox(
    "Show secondary",
    value=False,
    key="show_secondary",
    label_visibility="collapsed",
)

secondary_opacity = 1.0 if show_secondary else 0.45
st.markdown(
    f"<style>div[data-testid='stTextInput']{{opacity:{secondary_opacity};}}</style>",
    unsafe_allow_html=True,
)

top_row[2].text_input(
    "Secondary date",
    key=secondary_key,
    placeholder="dd/mm/yyyy",
    label_visibility="collapsed",
)

row = df_yields.loc[pd.Timestamp(selected_date)].dropna()
if row.empty:
    st.warning("No yields available for the selected date.")
    st.stop()

secondary_row = None
secondary_date = st.session_state[secondary_value_key]
if show_secondary:
    secondary_row = df_yields.loc[pd.Timestamp(secondary_date)].dropna()

tenors = [int(col[:-1]) for col in row.index]
pairs = sorted(zip(tenors, row.astype(float).to_numpy()))
tenors_sorted, yields_sorted = zip(*pairs)

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Avenir Next", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "axes.edgecolor": "#2f352f",
        "axes.labelcolor": "#2f352f",
        "xtick.color": "#2f352f",
        "ytick.color": "#2f352f",
        "grid.color": "#c5cfc4",
        "grid.linestyle": "--",
        "grid.linewidth": 0.8,
    }
)

fig, ax = plt.subplots(figsize=(10, 4.8))
fig.patch.set_alpha(0)
ax.set_facecolor("none")

ax.plot(tenors_sorted, yields_sorted, color="#0e7c86", linewidth=2.6)
ax.fill_between(tenors_sorted, yields_sorted, color="#0e7c86", alpha=0.12)
ax.scatter(tenors_sorted, yields_sorted, color="#0e7c86", s=22, zorder=3)

if show_secondary and secondary_row is not None and not secondary_row.empty:
    secondary_tenors = [int(col[:-1]) for col in secondary_row.index]
    secondary_pairs = sorted(
        zip(secondary_tenors, secondary_row.astype(float).to_numpy())
    )
    secondary_tenors_sorted, secondary_yields_sorted = zip(*secondary_pairs)
    ax.plot(
        secondary_tenors_sorted,
        secondary_yields_sorted,
        color="#c77d2b",
        linewidth=2.2,
        linestyle="--",
    )
    ax.scatter(
        secondary_tenors_sorted,
        secondary_yields_sorted,
        color="#c77d2b",
        s=18,
        zorder=3,
    )

ax.set_xlabel("Maturity (years)")
ax.set_ylabel("Yield (%)")
ax.set_xlim(min(tenors_sorted), max(tenors_sorted))
ax.grid(True, axis="y")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.set_xticks([1, 2, 3, 5, 7, 10, 15, 20, 30])

plt.tight_layout()
st.pyplot(fig, width="stretch")

st.select_slider(
    "Date",
    options=date_options,
    format_func=lambda dt: dt.strftime("%Y-%m-%d"),
    label_visibility="collapsed",
    key=state_key,
)
