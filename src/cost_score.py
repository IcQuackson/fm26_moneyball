from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils import fit_single_component_pca, percentile_rank, zscore_series


def compute_cost_scores(role_df: pd.DataFrame, performance_raw: pd.Series) -> tuple[pd.DataFrame, dict, list[str]]:
    result = pd.DataFrame(index=role_df.index)
    warnings: list[str] = []

    cost_frame = pd.DataFrame(
        {
            "log_transfer_value": np.log1p(role_df["Transfer Value"].clip(lower=0).astype(float)),
            "log_wage": np.log1p(role_df["Wage"].clip(lower=0).astype(float)),
        },
        index=role_df.index,
    ).apply(zscore_series)

    usable = [column for column in cost_frame.columns if cost_frame[column].dropna().nunique() > 1]
    if not usable:
        warnings.append("Transfer Value and Wage are unavailable or constant for this role cohort.")
        result["cost_raw"] = pd.NA
        result["cost_score"] = pd.NA
        result["value_gap_raw"] = pd.NA
        result["value_gap_score"] = pd.NA
        return result, {"usable_features": usable, "loadings": None, "explained_variance": None}, warnings

    imputed = cost_frame[usable].apply(lambda col: col.fillna(col.median()), axis=0)
    reference = imputed.mean(axis=1)
    cost_raw, loadings, explained = fit_single_component_pca(imputed, reference)
    result["cost_raw"] = cost_raw
    result["cost_score"] = percentile_rank(cost_raw)

    perf_z = zscore_series(performance_raw)
    cost_z = zscore_series(cost_raw)
    value_gap_raw = perf_z - cost_z
    result["value_gap_raw"] = value_gap_raw
    result["value_gap_score"] = percentile_rank(value_gap_raw)

    return result, {"usable_features": usable, "loadings": dict(zip(usable, loadings)), "explained_variance": explained}, warnings
