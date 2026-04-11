from __future__ import annotations

import pandas as pd

from src.constants import FAMILY_DEFINITIONS
from src.utils import fit_single_component_pca, nonconstant_columns, percentile_rank


def compute_family_scores(role: str, adjusted_df: pd.DataFrame) -> tuple[pd.DataFrame, dict, list[str], set[str]]:
    definitions = FAMILY_DEFINITIONS[role]
    family_frame = pd.DataFrame(index=adjusted_df.index)
    metadata: dict[str, dict] = {}
    warnings: list[str] = []
    used_primitives: set[str] = set()

    for family, primitives in definitions.items():
        subset = adjusted_df.reindex(columns=primitives)
        available = [column for column in subset.columns if subset[column].notna().any()]
        subset = subset[available]
        kept = nonconstant_columns(subset)
        dropped = [column for column in available if column not in kept]
        subset = subset[kept]

        if len(kept) < 2:
            warnings.append(f"{role}::{family} has fewer than 2 usable primitives after filtering.")
            metadata[family] = {"dropped": dropped, "kept": kept, "explained_variance": None, "loadings": None}
            family_frame[f"{family}__raw"] = pd.NA
            family_frame[f"{family}__score"] = pd.NA
            continue

        imputed = subset.apply(lambda col: col.fillna(col.median()), axis=0)
        reference = imputed.mean(axis=1)
        scores, loadings, explained = fit_single_component_pca(imputed, reference)
        family_frame[f"{family}__raw"] = scores
        family_frame[f"{family}__score"] = percentile_rank(scores)
        metadata[family] = {
            "dropped": dropped,
            "kept": kept,
            "medians": imputed.median().to_dict(),
            "explained_variance": explained,
            "loadings": dict(zip(kept, loadings)),
        }
        used_primitives.update(kept)
    return family_frame, metadata, warnings, used_primitives
