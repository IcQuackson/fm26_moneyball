from __future__ import annotations

import pandas as pd

from src.uncertainty import compute_uncertainty_scores


def test_uncertainty_drops_all_nan_components_and_uses_remaining_signal():
    role_df = pd.DataFrame(
        {
            "player_role_id": ["a", "b", "c"],
            "E": [1.0, 4.0, 9.0],
        }
    )
    shrink_delta = pd.DataFrame(index=role_df.index)
    bootstrap_instability = pd.Series([float("nan"), float("nan"), float("nan")], index=["a", "b", "c"])

    result, metadata, warnings = compute_uncertainty_scores(role_df, shrink_delta, set(), bootstrap_instability)

    assert result["uncertainty_score"].notna().all()
    assert metadata["usable_features"] == ["u_exp"]
    assert any("dropped unusable primitives" in warning for warning in warnings)


def test_uncertainty_returns_na_when_everything_is_missing_or_constant():
    role_df = pd.DataFrame(
        {
            "player_role_id": ["a", "b", "c"],
            "E": [1.0, 1.0, 1.0],
        }
    )
    shrink_delta = pd.DataFrame(index=role_df.index)
    bootstrap_instability = pd.Series([float("nan"), float("nan"), float("nan")], index=["a", "b", "c"])

    result, metadata, warnings = compute_uncertainty_scores(role_df, shrink_delta, set(), bootstrap_instability)

    assert result["uncertainty_raw"].isna().all()
    assert result["uncertainty_score"].isna().all()
    assert metadata["loadings"] is None
    assert any("could not be estimated" in warning for warning in warnings)


def test_uncertainty_uses_shrinkage_when_bootstrap_is_missing():
    role_df = pd.DataFrame(
        {
            "player_role_id": ["a", "b", "c"],
            "E": [2.0, 3.0, 5.0],
        }
    )
    shrink_delta = pd.DataFrame(
        {
            "metric_1": [0.1, 0.2, 0.3],
            "metric_2": [0.2, 0.3, 0.4],
        },
        index=role_df.index,
    )
    bootstrap_instability = pd.Series([float("nan"), float("nan"), float("nan")], index=["a", "b", "c"])

    result, metadata, _ = compute_uncertainty_scores(role_df, shrink_delta, {"metric_1", "metric_2"}, bootstrap_instability)

    assert result["uncertainty_score"].notna().all()
    assert set(metadata["usable_features"]) == {"u_exp", "u_shrink"}
