from __future__ import annotations

import numpy as np
import pandas as pd

import src.pipeline as pipeline_module
from src.pipeline import compute_uncertainty_for_file_hash, run_pipeline

from conftest import build_complete_df, dataframe_to_bytes


def _run_fast_pipeline(df, monkeypatch):
    monkeypatch.setattr(pipeline_module, "BOOTSTRAP_ITERATIONS", 5)
    return run_pipeline(dataframe_to_bytes(df))


def test_same_input_is_deterministic(monkeypatch):
    df = build_complete_df(["ST"] * 8)
    first = _run_fast_pipeline(df, monkeypatch)["results"].sort_values("player_role_id").reset_index(drop=True)
    second = _run_fast_pipeline(df, monkeypatch)["results"].sort_values("player_role_id").reset_index(drop=True)
    pd.testing.assert_series_equal(first["performance_score"], second["performance_score"])
    pd.testing.assert_series_equal(first["value_gap_score"], second["value_gap_score"])


def test_leakage_and_market_columns_do_not_change_performance(monkeypatch):
    df = build_complete_df(["ST"] * 8)
    baseline = _run_fast_pipeline(df, monkeypatch)["results"].sort_values("player_role_id").reset_index(drop=True)

    changed = df.copy()
    changed["Ability"] = "1"
    changed["Potential"] = "200"
    changed["Recommendation"] = "999"
    changed["Rating"] = "9.99"
    changed["Transfer Value"] = "£100M"
    changed["Wage"] = "£500K p/w"
    modified = _run_fast_pipeline(changed, monkeypatch)["results"].sort_values("player_role_id").reset_index(drop=True)

    assert np.allclose(baseline["performance_raw"], modified["performance_raw"], equal_nan=True)
    assert np.allclose(baseline["performance_score"], modified["performance_score"], equal_nan=True)


def test_pipeline_produces_multiple_role_rows(monkeypatch):
    positions = ["AM (R), ST"] + ["AM (R)"] * 4 + ["ST"] * 4
    results = _run_fast_pipeline(build_complete_df(positions), monkeypatch)["results"]
    player_rows = results[results["player"] == "Player 0"]
    assert set(player_rows["broad_role"]) == {"AM_W", "ST"}


def test_pipeline_returns_core_first_then_uncertainty(monkeypatch):
    monkeypatch.setattr(pipeline_module, "BOOTSTRAP_ITERATIONS", 5)
    df = build_complete_df(["ST"] * 8)
    payload = run_pipeline(dataframe_to_bytes(df))

    assert payload["uncertainty_state"] == "pending"
    assert payload["results"]["uncertainty_score"].isna().all()

    completed = compute_uncertainty_for_file_hash(payload["load_meta"]["file_hash"])
    assert completed["uncertainty_state"] == "complete"
    assert completed["results"]["exposure_uncertainty"].notna().all()
