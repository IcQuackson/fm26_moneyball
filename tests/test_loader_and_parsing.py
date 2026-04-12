from __future__ import annotations

import numpy as np

from src.io import load_fm_csv
from src.parse_numeric import parse_numeric_value

from conftest import build_complete_df


def test_parse_numeric_currency_and_percentages():
    assert parse_numeric_value("£1.5M") == 1_500_000.0
    assert parse_numeric_value("£10K p/w") == 10_000.0
    assert np.isclose(parse_numeric_value("75%"), 0.75)
    assert np.isnan(parse_numeric_value("-"))


def test_loads_semicolon_csv(csv_buffer):
    df = build_complete_df(["ST", "AM (R)"])
    loaded, metadata = load_fm_csv(csv_buffer(df))
    assert len(loaded) == 2
    assert metadata["row_count"] == 2
    assert loaded.loc[0, "Player__raw"] == "Player 0"
    assert loaded.loc[0, "Transfer Value"] == 1_500_000.0
    assert metadata["league_assumption"] == "division_broad_role_cohort"
    assert any("Division column detected" in warning for warning in metadata["warnings"])
