"""Layout helpers for dashboard composition."""

from __future__ import annotations

from typing import List

import streamlit as st

from src.config import DashboardConfig


def configure_page(config: DashboardConfig) -> None:
    """Apply Streamlit page settings."""

    st.set_page_config(page_title=config.page_title, layout=config.layout)


def render_header(config: DashboardConfig) -> None:
    """Render the main dashboard header block."""

    st.title(config.app_title)
    st.caption(config.app_caption)


def render_tabs(labels: List[str]):
    """Return Streamlit tab containers in label order."""

    return st.tabs(labels)

