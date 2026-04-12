from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import os

import pandas as pd

from src.constants import BOOTSTRAP_ITERATIONS, FAMILY_DEFINITIONS, MIN_ROLE_COHORT
from src.cost_score import compute_cost_scores
from src.family_scores import compute_family_scores
from src.io import load_fm_csv
from src.model_artifacts import load_artifact, save_artifact
from src.performance_score import compute_performance_scores
from src.primitives import build_primitives
from src.roles import expand_player_roles
from src.shrinkage import shrink_role_primitives
from src.standardize import standardize_role_primitives
from src.team_adjustment import adjust_role_metrics
from src.uncertainty import bootstrap_perf_raw, compute_uncertainty_scores
from src.utils import flatten, percentile_rank

UNCERTAINTY_COLUMNS = [
    "uncertainty_raw",
    "uncertainty_score",
    "bootstrap_sd",
    "shrinkage_intensity",
    "exposure_uncertainty",
]

def make_cohort_key(division: str, role: str) -> str:
    return f"{division}::{role}"


def _report_progress(progress_callback, phase: str, progress: float, message: str) -> None:
    if progress_callback is not None:
        progress_callback(phase, progress, message)


def _ensure_uncertainty_columns(results: pd.DataFrame) -> pd.DataFrame:
    frame = results.copy()
    for column in UNCERTAINTY_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    return frame


def score_role_core(role_df: pd.DataFrame) -> dict:
    role = role_df["broad_role"].iloc[0]
    division = role_df["Division__raw"].iloc[0]
    cohort_key = make_cohort_key(division, role)
    primitive_columns = flatten(FAMILY_DEFINITIONS[role].values())
    primitive_columns = sorted(set(primitive_columns) | {"E"})

    shrunk_df, shrink_delta, shrinkage_meta = shrink_role_primitives(role_df, primitive_columns)
    standardized_df = standardize_role_primitives(shrunk_df, primitive_columns)
    adjusted_df, team_meta, team_warnings = adjust_role_metrics(
        pd.concat([role_df[["Pts/Gm"]], standardized_df], axis=1),
        primitive_columns,
    )
    family_df, family_meta, family_warnings, used_primitives = compute_family_scores(role_df["broad_role"].iloc[0], adjusted_df)
    performance_df, performance_meta, performance_warnings = compute_performance_scores(family_df)

    results = pd.concat(
        [
            role_df[
                [
                    "player_id",
                    "player_role_id",
                    "Player__raw",
                    "Club__raw",
                    "Division__raw",
                    "Position__raw",
                    "Age",
                    "Minutes",
                    "Pts/Gm",
                    "broad_role",
                    "Transfer Value",
                    "Wage",
                ]
            ].rename(
                columns={
                    "Player__raw": "player",
                    "Club__raw": "club",
                    "Division__raw": "division",
                    "Position__raw": "position",
                    "Age": "age",
                    "Minutes": "minutes",
                    "Pts/Gm": "pts_per_game",
                }
            ),
            performance_df,
            family_df,
        ],
        axis=1,
    )

    cost_df, cost_meta, cost_warnings = compute_cost_scores(role_df, results["performance_raw"])
    results = pd.concat([results, cost_df], axis=1)

    warnings = []
    if len(role_df) < MIN_ROLE_COHORT:
        warnings.append(f"{cohort_key} cohort has only {len(role_df)} rows; factor extraction may be unstable.")
    warnings.extend(team_warnings)
    warnings.extend(family_warnings)
    warnings.extend(performance_warnings)
    warnings.extend(cost_warnings)

    metric_percentiles = adjusted_df.apply(percentile_rank)
    results["cohort_key"] = cohort_key

    return {
        "results": _ensure_uncertainty_columns(results),
        "shrunk": shrunk_df,
        "standardized": standardized_df,
        "adjusted": adjusted_df,
        "metric_percentiles": metric_percentiles,
        "shrink_delta": shrink_delta,
        "used_primitives": used_primitives,
        "artifacts": {
            "shrinkage": shrinkage_meta,
            "team_adjustment": team_meta,
                "family": family_meta,
                "performance": performance_meta,
                "cost": cost_meta,
                "uncertainty": {"loadings": None, "explained_variance": None, "usable_features": []},
            },
        "warnings": warnings,
    }


def _compute_role_uncertainty_task(
    cohort_key: str,
    role_df: pd.DataFrame,
    shrink_delta: pd.DataFrame,
    used_primitives: set[str],
    iterations: int,
) -> tuple[str, pd.DataFrame, dict, list[str]]:
    role_df = role_df.reset_index(drop=True)
    shrink_delta = shrink_delta.reset_index(drop=True)
    bootstrap_sd = bootstrap_perf_raw(role_df, score_role_core, iterations=iterations)
    uncertainty_df, uncertainty_meta, uncertainty_warnings = compute_uncertainty_scores(
        role_df, shrink_delta, used_primitives, bootstrap_sd
    )
    uncertainty_df = uncertainty_df.copy()
    uncertainty_df.index = role_df["player_role_id"].values
    return cohort_key, uncertainty_df, uncertainty_meta, uncertainty_warnings


def _merge_uncertainty_into_payload(payload: dict, role_outputs: list[tuple[str, pd.DataFrame, dict, list[str]]]) -> dict:
    results = payload["results"].copy()
    diagnostics = payload["diagnostics"]

    for cohort_key, uncertainty_df, uncertainty_meta, uncertainty_warnings in role_outputs:
        role_mask = results["cohort_key"] == cohort_key
        role_ids = results.loc[role_mask, "player_role_id"]
        for column in UNCERTAINTY_COLUMNS:
            results.loc[role_mask, column] = role_ids.map(uncertainty_df[column])
        diagnostics["role_artifacts"][cohort_key]["uncertainty"] = uncertainty_meta
        diagnostics["role_warnings"][cohort_key].extend(uncertainty_warnings)

    payload = dict(payload)
    payload["results"] = results
    payload["diagnostics"] = diagnostics
    payload["uncertainty_state"] = "complete"
    return payload


def _compute_uncertainty_stage(payload: dict, progress_callback=None) -> dict:
    traces = payload["traces"]
    role_jobs = [
        (
            cohort_key,
            trace["raw_primitives"],
            trace["shrink_delta"],
            trace["used_primitives"],
            BOOTSTRAP_ITERATIONS,
        )
        for cohort_key, trace in traces.items()
    ]
    if not role_jobs:
        payload = dict(payload)
        payload["uncertainty_state"] = "complete"
        return payload

    outputs: list[tuple[str, pd.DataFrame, dict, list[str]]] = []
    _report_progress(progress_callback, "uncertainty", 0.8, "Computing uncertainty in parallel.")

    max_workers = min(len(role_jobs), max(1, min(6, (os.cpu_count() or 1))))
    if len(role_jobs) == 1:
        outputs.append(_compute_role_uncertainty_task(*role_jobs[0]))
        _report_progress(progress_callback, "uncertainty", 1.0, "Uncertainty completed.")
        return _merge_uncertainty_into_payload(payload, outputs)

    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_compute_role_uncertainty_task, *job): job[0]
                for job in role_jobs
            }
            completed = 0
            for future in as_completed(futures):
                outputs.append(future.result())
                completed += 1
                progress = 0.8 + 0.2 * (completed / len(role_jobs))
                _report_progress(progress_callback, "uncertainty", progress, f"Completed uncertainty for {completed}/{len(role_jobs)} roles.")
    except Exception:
        outputs = []
        _report_progress(progress_callback, "uncertainty", 0.8, "Parallel uncertainty unavailable; falling back to serial computation.")
        for index, job in enumerate(role_jobs, start=1):
            outputs.append(_compute_role_uncertainty_task(*job))
            progress = 0.8 + 0.2 * (index / len(role_jobs))
            _report_progress(progress_callback, "uncertainty", progress, f"Completed uncertainty for {index}/{len(role_jobs)} roles.")

    return _merge_uncertainty_into_payload(payload, outputs)


def run_core_pipeline(source, progress_callback=None) -> dict:
    df, load_meta = load_fm_csv(source)
    cached = load_artifact(load_meta["file_hash"])
    if cached is not None:
        _report_progress(progress_callback, "cache", 1.0, "Loaded cached model artifacts.")
        return cached

    _report_progress(progress_callback, "load", 0.1, "Loaded and validated CSV.")
    primitive_df = build_primitives(df)
    _report_progress(progress_callback, "primitives", 0.25, "Built primitive metrics.")
    base_df = df.copy()
    for column in primitive_df.columns:
        base_df[column] = primitive_df[column]
    expanded = expand_player_roles(base_df)
    _report_progress(progress_callback, "roles", 0.35, "Expanded player-role cohorts.")

    role_results: list[pd.DataFrame] = []
    diagnostics = {
        "load_meta": load_meta,
        "role_sizes": expanded.groupby(["Division__raw", "broad_role"]).size().sort_index(),
        "role_artifacts": {},
        "role_warnings": {},
        "dropped_columns": {},
    }

    traces = {}
    grouped_roles = list(expanded.groupby(["Division__raw", "broad_role"], sort=False))
    for index, ((division, role), role_df) in enumerate(grouped_roles, start=1):
        cohort_key = make_cohort_key(division, role)
        _report_progress(progress_callback, "core_scoring", 0.35 + 0.4 * (index - 1) / max(len(grouped_roles), 1), f"Scoring {cohort_key} cohort ({index}/{len(grouped_roles)}).")
        scored = score_role_core(role_df.reset_index(drop=True))
        role_results.append(scored["results"])
        traces[cohort_key] = {
            "raw_primitives": role_df.reset_index(drop=True),
            "shrunk": scored["shrunk"],
            "standardized": scored["standardized"],
            "adjusted": scored["adjusted"],
            "metric_percentiles": scored["metric_percentiles"],
            "shrink_delta": scored["shrink_delta"],
            "used_primitives": scored["used_primitives"],
            "division": division,
            "broad_role": role,
        }
        diagnostics["role_artifacts"][cohort_key] = scored["artifacts"]
        diagnostics["role_warnings"][cohort_key] = scored["warnings"]
        diagnostics["dropped_columns"][cohort_key] = {
            family: meta.get("dropped", [])
            for family, meta in scored["artifacts"]["family"].items()
        }

    results = pd.concat(role_results, axis=0, ignore_index=True) if role_results else pd.DataFrame()
    payload = {
        "results": results,
        "expanded": expanded,
        "diagnostics": diagnostics,
        "traces": traces,
        "load_meta": load_meta,
        "uncertainty_state": "pending",
    }
    _report_progress(progress_callback, "core_complete", 0.75, "Core scores are ready. Uncertainty will run separately.")
    save_artifact(load_meta["file_hash"], payload)
    return payload


def compute_uncertainty_for_file_hash(file_hash: str, progress_callback=None) -> dict:
    payload = load_artifact(file_hash)
    if payload is None:
        raise ValueError("No cached core payload exists for this file hash.")
    if payload.get("uncertainty_state") == "complete":
        _report_progress(progress_callback, "cache", 1.0, "Loaded cached uncertainty results.")
        return payload
    updated = _compute_uncertainty_stage(payload, progress_callback=progress_callback)
    save_artifact(file_hash, updated)
    return updated


def run_pipeline(source, progress_callback=None) -> dict:
    return run_core_pipeline(source, progress_callback=progress_callback)
