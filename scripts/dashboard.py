from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Streamlit adds only this script's directory to sys.path. Add the repository
# root so dashboard modules can import config.py as the project's single source
# of truth for paths, labels, and plotting colours.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

st.set_page_config(
    page_title="PBFT Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.plotting.dashboard.app import main


if __name__ == "__main__":
    main()
