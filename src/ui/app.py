from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import time

import streamlit as st

from src.pipeline import compute_uncertainty_for_file_hash, run_pipeline
from src.ui.diagnostics import render_diagnostics
from src.ui.overview import render_overview
from src.ui.player_detail import render_player_detail


def _inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg-main: #04111f;
            --bg-panel: rgba(8, 23, 41, 0.82);
            --bg-panel-strong: rgba(9, 31, 56, 0.96);
            --border-neon: rgba(59, 130, 246, 0.42);
            --border-soft: rgba(125, 211, 252, 0.20);
            --text-main: #e0f2fe;
            --text-soft: #93c5fd;
            --text-muted: #7dd3fc;
            --shadow-neon: 0 0 0 1px rgba(56, 189, 248, 0.18), 0 0 28px rgba(37, 99, 235, 0.22);
        }
        .stApp {
            background:
                radial-gradient(circle at 15% 15%, rgba(0, 191, 255, 0.18), transparent 24%),
                radial-gradient(circle at 85% 10%, rgba(37, 99, 235, 0.16), transparent 22%),
                radial-gradient(circle at 50% 100%, rgba(8, 145, 178, 0.12), transparent 28%),
                linear-gradient(180deg, #020817 0%, #04111f 45%, #030b16 100%);
            color: var(--text-main);
        }
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.4rem;
        }
        [data-testid="stAppViewContainer"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"] {
            background: transparent;
        }
        div[data-testid="stMetric"] {
            background:
                linear-gradient(180deg, rgba(13, 36, 64, 0.96) 0%, rgba(7, 20, 39, 0.96) 100%);
            border: 1px solid var(--border-neon);
            border-radius: 18px;
            padding: 0.8rem 1rem;
            box-shadow: var(--shadow-neon);
            color: var(--text-main);
        }
        div[data-testid="stMetricLabel"], div[data-testid="stMetricValue"] {
            color: var(--text-main);
        }
        div[data-testid="stMetricLabel"] p {
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        div[data-testid="stMarkdownContainer"],
        div[data-testid="stCaptionContainer"],
        label, p, span, h1, h2, h3, h4, h5 {
            color: var(--text-main);
        }
        div[data-testid="stCaptionContainer"],
        div[data-testid="stCaptionContainer"] p {
            color: var(--text-soft) !important;
        }
        div[data-testid="stDataFrame"], div[data-testid="stVegaLiteChart"], div[data-testid="stMarkdownContainer"] > p {
            border-radius: 16px;
        }
        div[data-testid="stDataFrame"],
        div[data-testid="stVegaLiteChart"],
        div[data-testid="stAlert"] {
            background: var(--bg-panel);
            border: 1px solid var(--border-soft);
            box-shadow: var(--shadow-neon);
        }
        div[data-testid="stDataFrame"] {
            border-radius: 18px;
        }
        button[kind="secondary"], button[kind="primary"] {
            border-radius: 999px;
            color: var(--text-main);
            background: linear-gradient(180deg, rgba(14, 50, 92, 0.95) 0%, rgba(7, 25, 46, 0.95) 100%);
            border: 1px solid var(--border-neon);
            box-shadow: 0 0 18px rgba(59, 130, 246, 0.18);
        }
        button[kind="secondary"]:hover, button[kind="primary"]:hover {
            border-color: rgba(96, 165, 250, 0.88);
            box-shadow: 0 0 24px rgba(56, 189, 248, 0.28);
        }
        div[data-baseweb="select"] > div {
            border-radius: 14px;
            background: var(--bg-panel-strong);
            color: var(--text-main);
            border: 1px solid var(--border-neon);
            box-shadow: 0 0 16px rgba(37, 99, 235, 0.12);
        }
        div[data-baseweb="select"] input {
            color: var(--text-main) !important;
        }
        div[data-baseweb="tag"] {
            background: rgba(14, 116, 144, 0.28) !important;
            color: var(--text-main) !important;
            border: 1px solid rgba(34, 211, 238, 0.35);
        }
        div[data-baseweb="tooltip"],
        div[data-baseweb="popover"] {
            background: #06182d !important;
            color: #e0f2fe !important;
            border: 1px solid rgba(56, 189, 248, 0.4);
            box-shadow: 0 0 22px rgba(37, 99, 235, 0.24);
        }
        div[data-baseweb="tooltip"] *,
        div[data-baseweb="popover"] * {
            color: #e0f2fe !important;
        }
        [data-baseweb="tab-list"] {
            gap: 0.4rem;
        }
        button[role="tab"] {
            background: rgba(7, 20, 39, 0.92);
            border: 1px solid rgba(59, 130, 246, 0.22);
            border-radius: 999px;
            color: var(--text-soft);
        }
        button[role="tab"][aria-selected="true"] {
            color: var(--text-main);
            border-color: rgba(96, 165, 250, 0.7);
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.18);
        }
        .stSlider [data-baseweb="slider"] > div > div {
            background: linear-gradient(90deg, #0ea5e9, #2563eb) !important;
        }
        .stCheckbox label, .stRadio label {
            color: var(--text-main) !important;
        }
        div[data-testid="stFileUploader"] section {
            background: var(--bg-panel);
            border: 1px dashed rgba(56, 189, 248, 0.45);
            border-radius: 18px;
        }
        div[data-testid="stAlert"] {
            color: var(--text-main);
        }
        .league-trait-table-wrap {
            overflow-x: auto;
            background: var(--bg-panel);
            border: 1px solid var(--border-soft);
            border-radius: 18px;
            box-shadow: var(--shadow-neon);
            margin: 0.4rem 0 1rem;
        }
        .league-trait-table {
            width: 100%;
            border-collapse: collapse;
            min-width: 920px;
            color: var(--text-main);
            font-size: 0.92rem;
        }
        .league-trait-table thead th {
            position: sticky;
            top: 0;
            z-index: 1;
            background: rgba(7, 20, 39, 0.98);
            color: var(--text-soft);
            text-align: left;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            padding: 0.8rem 0.75rem;
            border-bottom: 1px solid rgba(56, 189, 248, 0.18);
            white-space: nowrap;
        }
        .league-trait-table tbody td {
            padding: 0.72rem 0.75rem;
            border-bottom: 1px solid rgba(56, 189, 248, 0.08);
            white-space: nowrap;
        }
        .league-trait-table tbody tr:hover td {
            background: rgba(8, 145, 178, 0.08);
        }
        .league-trait-header {
            display: inline-flex;
            align-items: center;
            gap: 0.42rem;
        }
        .league-trait-header-icon {
            width: 0.95rem;
            height: 0.95rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #67e8f9;
            filter: drop-shadow(0 0 6px rgba(34, 211, 238, 0.28));
        }
        .league-trait-icon {
            width: 0.95rem;
            height: 0.95rem;
            stroke: currentColor;
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
    if "uncertainty_started_at" not in st.session_state:
        st.session_state["uncertainty_started_at"] = None
    if "uncertainty_completed_at" not in st.session_state:
        st.session_state["uncertainty_completed_at"] = None
    if "uncertainty_last_error" not in st.session_state:
        st.session_state["uncertainty_last_error"] = None


def _format_elapsed(started_at: float | None) -> str:
    if started_at is None:
        return "unknown"
    elapsed_seconds = max(0, int(time.time() - started_at))
    minutes, seconds = divmod(elapsed_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _format_timestamp(timestamp: float | None) -> str:
    if timestamp is None:
        return "unknown"
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


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
    st.session_state["uncertainty_started_at"] = time.time()
    st.session_state["uncertainty_completed_at"] = None
    st.session_state["uncertainty_last_error"] = None


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
        st.session_state["uncertainty_last_error"] = str(exc)
        return payload, str(exc)
    st.session_state["uncertainty_future"] = None
    st.session_state["uncertainty_completed_at"] = time.time()
    st.session_state["uncertainty_last_error"] = None
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
        elapsed = _format_elapsed(st.session_state.get("uncertainty_started_at"))
        status_parts = [
            "Confidence status: running.",
            f"Elapsed: {elapsed}.",
            "Use the in-app refresh button instead of a full browser reload.",
        ]
        st.caption(" ".join(status_parts))
        st.info(
            "Player profiles are ready. Confidence estimates are still being calculated in the background. You can use the dashboard now and refresh later for the final confidence view."
        )
        if st.button("Refresh Uncertainty Status"):
            st.rerun()
    else:
        completed_at = st.session_state.get("uncertainty_completed_at")
        if completed_at is not None:
            st.caption(f"Confidence status: ready. Last completed: {_format_timestamp(completed_at)}.")
        elif st.session_state.get("uncertainty_last_error"):
            st.caption(f"Confidence status: previous background run failed: {st.session_state['uncertainty_last_error']}")

    show_advanced = st.checkbox("Show Advanced Model Notes", value=False)
    tab_labels = ["Scout Board", "Player Report"] + (["Model Notes"] if show_advanced else [])
    tabs = st.tabs(tab_labels)
    tab_overview, tab_player = tabs[0], tabs[1]
    with tab_overview:
        render_overview(payload["results"], payload["traces"])
    with tab_player:
        render_player_detail(payload["results"], payload["traces"], payload["diagnostics"])
    if show_advanced:
        with tabs[2]:
            render_diagnostics(payload)
