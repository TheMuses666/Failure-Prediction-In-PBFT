from __future__ import annotations

import streamlit as st

from .pages import (
    page_ablations,
    page_dataset,
    page_early_prediction,
    page_extensions,
    page_figures,
    page_generalisation,
    page_main_results,
    page_overview,
)
from .ui import inject_css


def main() -> None:
    inject_css()
    st.sidebar.markdown(
        """
        <div class="sidebar-section">Main Menu</div>
        """,
        unsafe_allow_html=True,
    )
    page = st.sidebar.radio(
        "Navigate",
        [
            "Overview",
            "Dataset",
            "Main Results",
            "Early Prediction",
            "Generalisation",
            "Ablations",
            "GNN / BiLSTM",
            "Figures",
        ],
    )
    st.sidebar.markdown(
        """
        <div class="sidebar-footnote">
            Local CSV and PNG outputs only.<br>
            Tables, figures, and datasets are read from this workspace.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if page == "Overview":
        page_overview()
    elif page == "Dataset":
        page_dataset()
    elif page == "Main Results":
        page_main_results()
    elif page == "Early Prediction":
        page_early_prediction()
    elif page == "Generalisation":
        page_generalisation()
    elif page == "Ablations":
        page_ablations()
    elif page == "GNN / BiLSTM":
        page_extensions()
    else:
        page_figures()
