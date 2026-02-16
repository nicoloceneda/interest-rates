"""Theme utilities shared across dashboard pages."""

from __future__ import annotations

import streamlit as st

BASE_THEME_CSS = """
<style>
    .block-container {
        max-width: 1840px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3, h4 {
        font-family: "Avenir Next", "Segoe UI", sans-serif;
        letter-spacing: 0.01em;
        color: #1d2733;
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid #d7dde5;
    }
    [data-testid="stMetric"] {
        border-radius: 10px;
        border: 1px solid #d7dde5;
        padding: 0.35rem 0.75rem;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0.9rem;
    }
</style>
"""


def apply_theme() -> None:
    """Inject the base CSS theme."""

    st.markdown(BASE_THEME_CSS, unsafe_allow_html=True)
