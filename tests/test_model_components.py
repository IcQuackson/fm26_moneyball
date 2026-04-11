from __future__ import annotations

import numpy as np
import pandas as pd

from src.family_scores import compute_family_scores
from src.shrinkage import shrink_role_primitives
from src.team_adjustment import adjust_role_metrics


def test_shrinkage_is_stronger_for_lower_attempts():
    role_df = pd.DataFrame(
        {
            "E": [10.0, 10.0, 10.0],
            "Ps C": [1.0, 18.0, 90.0],
            "Pas A": [1.0, 20.0, 100.0],
            "pass_completion": [1.0, 0.9, 0.9],
        }
    )
    shrunk, delta, _ = shrink_role_primitives(role_df, ["pass_completion"])
    assert delta.loc[0, "pass_completion"] > delta.loc[2, "pass_completion"]
    assert shrunk.loc[0, "pass_completion"] < role_df.loc[0, "pass_completion"]


def test_family_score_sign_orientation_is_positive():
    adjusted = pd.DataFrame(
        {
            "Shot/90": [0.0, 0.5, 1.0, 1.5],
            "ShT/90": [0.0, 0.4, 0.8, 1.2],
            "xG/90": [0.1, 0.3, 0.6, 0.9],
            "NP-xG/90": [0.1, 0.25, 0.55, 0.85],
            "Goals per 90 minutes": [0.1, 0.3, 0.7, 1.0],
            "shot_on_target_rate": [0.2, 0.35, 0.45, 0.6],
            "Conv %": [0.08, 0.12, 0.18, 0.22],
            "xG/shot": [0.08, 0.09, 0.1, 0.11],
            "finishing_over_expected": [0.0, 0.02, 0.05, 0.08],
            "KP/90": [0.2, 0.4, 0.6, 0.8],
            "OP-KP/90": [0.1, 0.2, 0.3, 0.5],
            "Ch C/90": [0.2, 0.4, 0.6, 0.7],
            "xA/90": [0.1, 0.2, 0.3, 0.4],
            "Asts/90": [0.05, 0.1, 0.15, 0.2],
            "pass_completion": [0.7, 0.75, 0.8, 0.85],
            "PsP": [4.0, 5.0, 6.0, 7.0],
            "Pres A/90": [1.0, 1.5, 2.0, 2.5],
            "Pres C/90": [0.5, 1.0, 1.5, 2.0],
            "Poss Won/90": [0.8, 1.0, 1.2, 1.4],
            "Hdrs W/90": [0.2, 0.5, 0.7, 1.0],
            "header_win_rate": [0.4, 0.5, 0.6, 0.7],
            "K Hdrs/90": [0.1, 0.2, 0.3, 0.4],
            "Aer A/90": [0.4, 0.6, 0.8, 1.0],
        }
    )
    family_df, _, _, _ = compute_family_scores("ST", adjusted)
    reference = adjusted[["Shot/90", "ShT/90", "xG/90", "NP-xG/90", "Goals per 90 minutes"]].mean(axis=1)
    corr = np.corrcoef(family_df["threat_volume__raw"], reference)[0, 1]
    assert corr > 0


def test_team_adjustment_uses_pts_per_game():
    role_df = pd.DataFrame(
        {
            "Pts/Gm": [0.8, 1.0, 1.2, 1.4, 1.6],
            "metric": [0.1, 0.2, 0.3, 0.4, 0.5],
        }
    )
    adjusted, _, _ = adjust_role_metrics(role_df, ["metric"])
    corr = adjusted["metric"].corr(role_df["Pts/Gm"])
    assert abs(corr) < 1e-6
