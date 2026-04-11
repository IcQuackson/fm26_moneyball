from __future__ import annotations

import numpy as np
import pandas as pd

from src.constants import BINOMIAL_PRIMITIVES, NORMAL_PRIMITIVES, RATE_PRIMITIVES
from src.utils import safe_divide, zscore_series


def _rateify(series: pd.Series, exposure: pd.Series, is_rate: bool) -> pd.Series:
    if is_rate:
        return series.astype(float)
    return safe_divide(series.astype(float), exposure)


def build_primitives(df: pd.DataFrame) -> pd.DataFrame:
    primitives = pd.DataFrame(index=df.index)
    exposure = np.maximum(df["Minutes"].fillna(0.0).astype(float) / 90.0, 1e-6)
    primitives["E"] = exposure

    for primitive, (success, attempts) in BINOMIAL_PRIMITIVES.items():
        primitives[primitive] = safe_divide(df[success], df[attempts])

    for primitive, source in RATE_PRIMITIVES.items():
        is_rate = "/90" in source or source == "Goals per 90 minutes"
        primitives[primitive] = _rateify(df[source], exposure, is_rate=is_rate)

    primitives["Poss Lost/90"] = df["Poss Lost/90"]
    primitives["xG/shot"] = df["xG/shot"]
    primitives["xG-OP"] = df["xG-OP"]
    primitives["xSv %"] = df["xSv %"]
    primitives["Sv %"] = df["Sv %"]
    primitives["PsP"] = df["PsP"]
    primitives["Conv %"] = df["Conv %"]
    primitives["finishing_over_expected"] = df["Goals per 90 minutes"] - df["xG/90"]
    primitives["assist_over_expected"] = df["Asts/90"] - df["xA/90"]
    primitives["shot_quality"] = df["xG/shot"]
    primitives["loss_security"] = -df["Poss Lost/90"]

    discipline_frame = pd.DataFrame(
        {
            "Fouls Made": primitives["Fouls Made"],
            "Yel": primitives["Yel"],
            "Red cards": primitives["Red cards"],
            "MLG": primitives["MLG"],
        }
    ).apply(zscore_series)
    primitives["discipline_penalty"] = -discipline_frame.mean(axis=1)

    for primitive in NORMAL_PRIMITIVES:
        if primitive not in primitives.columns:
            primitives[primitive] = np.nan

    return primitives
