from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import src.model_artifacts as model_artifacts
from src.family_scores import compute_family_scores
from src.io import _read_bytes, load_fm_csv
from src.model_artifacts import load_artifact, save_artifact
from src.parse_numeric import _clean_numeric_token, parse_numeric_value
from src.performance_score import compute_performance_scores
from src.roles import detect_roles
from src.shrinkage import estimate_beta_prior, estimate_gamma_poisson_strength, estimate_normal_tau
from src.team_adjustment import adjust_role_metrics

from conftest import build_complete_df, dataframe_to_bytes


def test_read_bytes_supports_path_and_missing_columns(tmp_path):
    df = build_complete_df(["ST"]).drop(columns=["Wage"])
    path = tmp_path / "bad.csv"
    path.write_bytes(dataframe_to_bytes(df))

    assert _read_bytes(path) == path.read_bytes()
    with pytest.raises(ValueError, match="Missing required columns"):
        load_fm_csv(path)


def test_load_fm_csv_falls_back_to_latin1(tmp_path):
    df = build_complete_df(["ST"])
    df.loc[0, "Player"] = "José"
    path = tmp_path / "latin1.csv"
    path.write_bytes(df.to_csv(sep=";", index=False).encode("latin-1"))

    loaded, _ = load_fm_csv(path)
    assert loaded.loc[0, "Player__raw"] == "José"


def test_parse_numeric_extra_branches():
    assert _clean_numeric_token("abc") is None
    assert np.isnan(parse_numeric_value(None))
    assert parse_numeric_value(7) == 7.0
    assert np.isnan(parse_numeric_value("foo"))
    assert parse_numeric_value("$1,234") == 1234.0


def test_family_scores_warn_when_fewer_than_two_primitives():
    adjusted = pd.DataFrame({"Saves/90": [1.0, 2.0, 3.0]})
    family_df, metadata, warnings, used_primitives = compute_family_scores("GK", adjusted)
    assert family_df["shot_stopper__raw"].isna().all()
    assert metadata["shot_stopper"]["loadings"] is None
    assert warnings
    assert used_primitives == set()


def test_performance_scores_warn_when_too_few_families():
    family_df = pd.DataFrame({"finisher__raw": [0.1, 0.2, 0.3], "finisher__score": [10, 20, 30]})
    result, metadata, warnings = compute_performance_scores(family_df)
    assert result["performance_raw"].isna().all()
    assert metadata["loadings"] is None
    assert warnings


def test_role_detection_covers_fb_wb_and_cm():
    assert detect_roles("D (L), WB (R)") == ["FB_WB"]
    assert detect_roles("M (C)") == ["CM"]


def test_shrinkage_parameter_fallbacks():
    alpha, beta = estimate_beta_prior(pd.Series([1.0]), pd.Series([1.0]))
    assert (alpha, beta) == (1.0, 1.0)

    k, mu = estimate_gamma_poisson_strength(pd.Series([0.0, 0.0]), pd.Series([1.0, 2.0]))
    assert k == 5.0
    assert mu == 0.0

    tau, mean_val = estimate_normal_tau(pd.Series([1.0]), pd.Series([1.0]))
    assert tau == 1.0
    assert mean_val == 1.0


def test_team_adjustment_falls_back_when_pts_gm_has_no_variance():
    role_df = pd.DataFrame({"Pts/Gm": [1.0, 1.0, 1.0], "metric": [0.1, 0.2, 0.3]})
    adjusted, metadata, warnings = adjust_role_metrics(role_df, ["metric"])
    assert adjusted["metric"].equals(role_df["metric"])
    assert metadata["metric"]["used_adjustment"] is False
    assert warnings


def test_model_artifact_version_mismatch_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(model_artifacts, "ARTIFACT_DIR", tmp_path)
    save_artifact("abc", {"results": []})
    payload = load_artifact("abc")
    assert payload is not None

    artifact_file = tmp_path / "abc.pkl"
    broken = {"artifact_version": -1}
    artifact_file.write_bytes(__import__("pickle").dumps(broken))
    assert load_artifact("abc") is None
