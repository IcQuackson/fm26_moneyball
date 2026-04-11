from __future__ import annotations

import pandas as pd

from src.utils import fit_single_component_pca, nonconstant_columns, percentile_rank, zscore_series


def compute_performance_scores(family_df: pd.DataFrame) -> tuple[pd.DataFrame, dict, list[str]]:
    raw_columns = [column for column in family_df.columns if column.endswith("__raw")]
    usable = nonconstant_columns(family_df[raw_columns])
    warnings: list[str] = []
    metadata: dict[str, object] = {"usable_families": usable}

    if len(usable) < 2:
        warnings.append("Fewer than 2 family scores are available for overall performance PCA.")
        result = pd.DataFrame(index=family_df.index)
        result["performance_raw"] = pd.NA
        result["performance_score"] = pd.NA
        metadata["loadings"] = None
        metadata["explained_variance"] = None
        return result, metadata, warnings

    standardized = family_df[usable].apply(zscore_series)
    imputed = standardized.apply(lambda col: col.fillna(col.median()), axis=0)
    reference = imputed.mean(axis=1)
    scores, loadings, explained = fit_single_component_pca(imputed, reference)

    result = pd.DataFrame(index=family_df.index)
    result["performance_raw"] = scores
    result["performance_score"] = percentile_rank(scores)
    metadata["loadings"] = dict(zip(usable, loadings))
    metadata["explained_variance"] = explained
    return result, metadata, warnings
