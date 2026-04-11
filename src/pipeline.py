from __future__ import annotations

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
from src.utils import flatten


def _score_role(role_df: pd.DataFrame, bootstrap_mode: bool = False) -> dict:
    role = role_df["broad_role"].iloc[0]
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
        warnings.append(f"{role} cohort has only {len(role_df)} rows; factor extraction may be unstable.")
    warnings.extend(team_warnings)
    warnings.extend(family_warnings)
    warnings.extend(performance_warnings)
    warnings.extend(cost_warnings)

    if bootstrap_mode:
        return {
            "results": results,
            "shrunk": shrunk_df,
            "standardized": standardized_df,
            "adjusted": adjusted_df,
            "shrink_delta": shrink_delta,
            "used_primitives": used_primitives,
            "artifacts": {
                "shrinkage": shrinkage_meta,
                "team_adjustment": team_meta,
                "family": family_meta,
                "performance": performance_meta,
                "cost": cost_meta,
            },
            "warnings": warnings,
        }

    bootstrap_sd = bootstrap_perf_raw(role_df, _score_role, iterations=BOOTSTRAP_ITERATIONS)
    uncertainty_df, uncertainty_meta, uncertainty_warnings = compute_uncertainty_scores(role_df, shrink_delta, used_primitives, bootstrap_sd)
    results = pd.concat([results, uncertainty_df], axis=1)
    warnings.extend(uncertainty_warnings)

    return {
        "results": results,
        "shrunk": shrunk_df,
        "standardized": standardized_df,
        "adjusted": adjusted_df,
        "shrink_delta": shrink_delta,
        "used_primitives": used_primitives,
        "artifacts": {
            "shrinkage": shrinkage_meta,
            "team_adjustment": team_meta,
            "family": family_meta,
            "performance": performance_meta,
            "cost": cost_meta,
            "uncertainty": uncertainty_meta,
        },
        "warnings": warnings,
    }


def run_pipeline(source) -> dict:
    df, load_meta = load_fm_csv(source)
    cached = load_artifact(load_meta["file_hash"])
    if cached is not None:
        return cached

    primitive_df = build_primitives(df)
    base_df = df.copy()
    for column in primitive_df.columns:
        base_df[column] = primitive_df[column]
    expanded = expand_player_roles(base_df)

    role_results: list[pd.DataFrame] = []
    diagnostics = {
        "load_meta": load_meta,
        "role_sizes": expanded["broad_role"].value_counts().sort_index(),
        "role_artifacts": {},
        "role_warnings": {},
        "dropped_columns": {},
    }

    traces = {}
    for role, role_df in expanded.groupby("broad_role", sort=False):
        scored = _score_role(role_df.reset_index(drop=True))
        role_results.append(scored["results"])
        traces[role] = {
            "raw_primitives": role_df,
            "shrunk": scored["shrunk"],
            "standardized": scored["standardized"],
            "adjusted": scored["adjusted"],
            "shrink_delta": scored["shrink_delta"],
        }
        diagnostics["role_artifacts"][role] = scored["artifacts"]
        diagnostics["role_warnings"][role] = scored["warnings"]
        diagnostics["dropped_columns"][role] = {
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
    }
    save_artifact(load_meta["file_hash"], payload)
    return payload
