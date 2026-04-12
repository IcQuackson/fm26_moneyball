from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from src.pipeline import compute_uncertainty_for_file_hash, run_pipeline
from src.ui.diagnostics import render_diagnostics
from src.ui.overview import render_overview
from src.ui.player_detail import render_player_detail


def _inject_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(14, 165, 233, 0.14), transparent 30%),
                radial-gradient(circle at top right, rgba(249, 115, 22, 0.12), transparent 24%),
                linear-gradient(180deg, #f8fafc 0%, #edf2f7 100%);
            color: #0f172a;
        }
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.4rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 18px;
            padding: 0.8rem 1rem;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.06);
            color: #0f172a;
        }
        div[data-testid="stMetricLabel"], div[data-testid="stMetricValue"] {
            color: #0f172a;
        }
        div[data-testid="stMarkdownContainer"], div[data-testid="stCaptionContainer"], label, p, span, h1, h2, h3 {
            color: #0f172a;
        }
        div[data-testid="stDataFrame"], div[data-testid="stVegaLiteChart"], div[data-testid="stMarkdownContainer"] > p {
            border-radius: 16px;
        }
        div[data-testid="stDataFrame"] {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(148, 163, 184, 0.18);
        }
        button[kind="secondary"], button[kind="primary"] {
            border-radius: 999px;
            color: #0f172a;
        }
        div[data-baseweb="select"] > div {
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.92);
            color: #0f172a;
        }
        div[data-baseweb="select"] input {
            color: #0f172a !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
    _inject_theme()
    st.title("FM26 Scout Dashboard")
    st.caption("Shortlist players by league, trait, price, and role fit from your Football Manager export.")
    _ensure_session_state()

    upload = st.file_uploader("Upload FM export", type=["csv"])
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
    summary_cols[0].metric("Players Loaded", str(payload["load_meta"]["row_count"]))
    summary_cols[1].metric("Scout Profiles", str(result_count))
    summary_cols[2].metric("Roles Covered", str(role_count))
    summary_cols[3].metric("Confidence Update", "Ready" if payload.get("uncertainty_state") == "complete" else "In Progress")

    if payload.get("uncertainty_state") != "complete":
        _maybe_start_uncertainty_job(payload["load_meta"]["file_hash"])
        st.info(
            "Player profiles are ready. Confidence estimates are still being calculated in the background. You can use the dashboard now and refresh later for the final confidence view."
        )
        if st.button("Refresh Uncertainty Status"):
            st.rerun()

    show_advanced = st.checkbox("Show Advanced Model Notes", value=False)
    tab_labels = ["Scout Board", "Player Report"] + (["Model Notes"] if show_advanced else [])
    tabs = st.tabs(tab_labels)
    tab_overview, tab_player = tabs[0], tabs[1]
    with tab_overview:
        render_overview(payload["results"])
    with tab_player:
        render_player_detail(payload["results"], payload["traces"], payload["diagnostics"])
    if show_advanced:
        with tabs[2]:
            render_diagnostics(payload)
