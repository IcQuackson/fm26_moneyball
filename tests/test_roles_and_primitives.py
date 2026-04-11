from __future__ import annotations

import numpy as np

from src.io import load_fm_csv
from src.primitives import build_primitives
from src.roles import detect_roles, expand_player_roles

from conftest import build_complete_df


def test_role_parsing_from_fm_position_strings():
    assert detect_roles("GK") == ["GK"]
    assert detect_roles("D (C), DM") == ["CB", "DM"]
    assert detect_roles("AM (R), ST") == ["AM_W", "ST"]


def test_primitive_construction(csv_buffer):
    df = build_complete_df(["ST"])
    loaded, _ = load_fm_csv(csv_buffer(df))
    primitives = build_primitives(loaded)
    assert np.isclose(primitives.loc[0, "pass_completion"], 430 / 500)
    assert np.isclose(primitives.loc[0, "shot_on_target_rate"], 10 / 20)
    assert np.isclose(primitives.loc[0, "finishing_over_expected"], 0.50 - 0.42)


def test_player_with_multiple_eligible_roles(csv_buffer):
    df = build_complete_df(["AM (R), ST"])
    loaded, _ = load_fm_csv(csv_buffer(df))
    expanded = expand_player_roles(loaded)
    assert set(expanded["broad_role"]) == {"AM_W", "ST"}
