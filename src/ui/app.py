from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from src.pipeline import compute_uncertainty_for_file_hash, run_pipeline
from src.ui.diagnostics import render_diagnostics
from src.ui.overview import render_overview
from src.ui.player_detail import render_player_detail


def _ensure_session_state() -> None:
    if "uncertainty_executor" not in st.session_state:
        st.session_state["uncertainty_executor"] = ThreadPoolExecutor(max_workers=1)
    if "uncertainty_future" not in st.session_state:
        st.session_state["uncertainty_future"] = None
    if "uncertainty_file_hash" not in st.session_state:
        st.session_state["uncertainty_file_hash"] = None


def _maybe_start_uncertainty_job(file_hash: str) -> None:
    future = st.session_state.get("uncertainty_future")
    target_hash = st.session_state.get("uncertainty_file_hash")
    if future is not None and not future.done() and target_hash == file_hash:
        return
    st.session_state["uncertainty_future"] = st.session_state["uncertainty_executor"].submit(
        compute_uncertainty_for_file_hash,
        file_hash,
        None,
    )
    st.session_state["uncertainty_file_hash"] = file_hash


def _resolve_uncertainty_future(payload: dict) -> tuple[dict, str | None]:
    future = st.session_state.get("uncertainty_future")
    target_hash = st.session_state.get("uncertainty_file_hash")
    file_hash = payload["load_meta"]["file_hash"]
    if future is None or target_hash != file_hash:
        return payload, None
    if not future.done():
        return payload, None
    try:
        resolved = future.result()
    except Exception as exc:
        st.session_state["uncertainty_future"] = None
        return payload, str(exc)
    st.session_state["uncertainty_future"] = None
    return resolved, None


def main() -> None:
    st.set_page_config(page_title="FM26 Moneyball Analyzer", layout="wide")
    st.title("FM26 Moneyball Analyzer")
    st.caption("Role-specific same-league scoring from a semicolon-delimited FM export.")
    _ensure_session_state()

    upload = st.file_uploader("Upload FM CSV", type=["csv"])
    if upload is None:
        st.info("Upload a semicolon-delimited FM export to build the cohort dashboard.")
        return

    progress_bar = st.progress(0.0)
    phase_text = st.empty()

    def progress_callback(phase: str, progress: float, message: str) -> None:
        progress_bar.progress(max(0.0, min(1.0, float(progress))))
        phase_text.caption(message)

    payload = run_pipeline(upload, progress_callback=progress_callback)
    payload, uncertainty_error = _resolve_uncertainty_future(payload)
    progress_bar.empty()
    phase_text.empty()

    for warning in payload["load_meta"]["warnings"]:
        st.warning(warning)
    if uncertainty_error is not None:
        st.warning(f"Background uncertainty computation failed: {uncertainty_error}")

    result_count = len(payload["results"])
    role_count = int(payload["results"]["broad_role"].nunique()) if result_count else 0
    summary_cols = st.columns(4)
    summary_cols[0].metric("Rows", str(payload["load_meta"]["row_count"]))
    summary_cols[1].metric("Player-Role Rows", str(result_count))
    summary_cols[2].metric("Roles", str(role_count))
    summary_cols[3].metric("Uncertainty", "Ready" if payload.get("uncertainty_state") == "complete" else "Computing")

    if payload.get("uncertainty_state") != "complete":
        _maybe_start_uncertainty_job(payload["load_meta"]["file_hash"])
        st.info(
            "Core scores are ready. Uncertainty is computing in the background. The dashboard is usable now; click refresh after a while to load the completed uncertainty metrics."
        )
        if st.button("Refresh Uncertainty Status"):
            st.rerun()

    tab_overview, tab_player, tab_diag = st.tabs(["Overview", "Player Detail", "Diagnostics"])
    with tab_overview:
        render_overview(payload["results"])
    with tab_player:
        render_player_detail(payload["results"], payload["traces"], payload["diagnostics"])
    with tab_diag:
        render_diagnostics(payload)
