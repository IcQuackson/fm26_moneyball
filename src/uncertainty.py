from __future__ import annotations

import numpy as np
import pandas as pd

from src.constants import BOOTSTRAP_ITERATIONS, SEED
from src.utils import fit_single_component_pca, nonconstant_columns, percentile_rank, zscore_series


def bootstrap_perf_raw(
    role_df: pd.DataFrame,
    scorer,
    iterations: int = BOOTSTRAP_ITERATIONS,
) -> pd.Series:
    rng = np.random.default_rng(SEED)
    samples: dict[str, list[float]] = {player_role_id: [] for player_role_id in role_df["player_role_id"]}

    for _ in range(iterations):
        sampled_idx = rng.integers(0, len(role_df), size=len(role_df))
        sampled = role_df.iloc[sampled_idx].copy()
        sampled_result = scorer(sampled, bootstrap_mode=True)
        if sampled_result["results"].empty:
            continue
        grouped = sampled_result["results"].groupby("player_role_id")["performance_raw"].mean()
        for player_role_id, value in grouped.items():
            if pd.notna(value):
                samples.setdefault(player_role_id, []).append(float(value))

    instability = pd.Series(index=role_df["player_role_id"], dtype=float)
    for player_role_id, values in samples.items():
        instability.loc[player_role_id] = float(np.std(values, ddof=0)) if len(values) >= 2 else np.nan
    return instability


def compute_uncertainty_scores(
    role_df: pd.DataFrame,
    shrink_delta: pd.DataFrame,
    used_primitives: set[str],
    bootstrap_instability: pd.Series,
) -> tuple[pd.DataFrame, dict, list[str]]:
    result = pd.DataFrame(index=role_df.index)
    warnings: list[str] = []
    exposure_uncertainty = 1.0 / np.sqrt(role_df["E"].astype(float) + 1.0)

    primitives = list(sorted(used_primitives))
    if primitives:
        shrink_intensity = shrink_delta[primitives].mean(axis=1)
    else:
        shrink_intensity = pd.Series(np.nan, index=role_df.index, dtype=float)

    boot_values = role_df["player_role_id"].map(bootstrap_instability)

    uncertainty_frame = pd.DataFrame(
        {
            "u_exp": zscore_series(pd.Series(exposure_uncertainty, index=role_df.index)),
            "u_boot": zscore_series(boot_values),
            "u_shrink": zscore_series(shrink_intensity),
        },
        index=role_df.index,
    )

    available = [column for column in uncertainty_frame.columns if uncertainty_frame[column].notna().any()]
    usable = nonconstant_columns(uncertainty_frame[available]) if available else []

    result["bootstrap_sd"] = boot_values
    result["shrinkage_intensity"] = shrink_intensity
    result["exposure_uncertainty"] = exposure_uncertainty

    if not usable:
        warnings.append("Uncertainty score could not be estimated because all uncertainty primitives were missing or constant.")
        result["uncertainty_raw"] = pd.NA
        result["uncertainty_score"] = pd.NA
        return result, {"usable_features": usable, "loadings": None, "explained_variance": None}, warnings

    dropped = [column for column in uncertainty_frame.columns if column not in usable]
    if dropped:
        warnings.append(f"Uncertainty score dropped unusable primitives: {', '.join(dropped)}.")

    imputed = uncertainty_frame[usable].apply(lambda col: col.fillna(col.median()), axis=0)
    reference = imputed.mean(axis=1)
    raw, loadings, explained = fit_single_component_pca(imputed, reference)
    result["uncertainty_raw"] = raw
    result["uncertainty_score"] = percentile_rank(raw)

    return result, {"usable_features": usable, "loadings": dict(zip(imputed.columns, loadings)), "explained_variance": explained}, warnings
