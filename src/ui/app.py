from __future__ import annotations

import streamlit as st

from src.pipeline import run_pipeline
from src.ui.diagnostics import render_diagnostics
from src.ui.overview import render_overview
from src.ui.player_detail import render_player_detail


def main() -> None:
    st.set_page_config(page_title="FM26 Moneyball Analyzer", layout="wide")
    st.title("FM26 Moneyball Analyzer")
    st.caption("Role-specific same-league scoring from a semicolon-delimited FM export.")

    upload = st.file_uploader("Upload FM CSV", type=["csv"])
    if upload is None:
        st.info("Upload a semicolon-delimited FM export to build the cohort dashboard.")
        return

    with st.spinner("Running role-specific model pipeline..."):
        payload = run_pipeline(upload)

    for warning in payload["load_meta"]["warnings"]:
        st.warning(warning)

    result_count = len(payload["results"])
    role_count = int(payload["results"]["broad_role"].nunique()) if result_count else 0
    summary_cols = st.columns(4)
    summary_cols[0].metric("Rows", str(payload["load_meta"]["row_count"]))
    summary_cols[1].metric("Player-Role Rows", str(result_count))
    summary_cols[2].metric("Roles", str(role_count))
    summary_cols[3].metric("League Assumption", "Single cohort assumed")

    tab_overview, tab_player, tab_diag = st.tabs(["Overview", "Player Detail", "Diagnostics"])
    with tab_overview:
        render_overview(payload["results"])
    with tab_player:
        render_player_detail(payload["results"], payload["traces"], payload["diagnostics"])
    with tab_diag:
        render_diagnostics(payload)
