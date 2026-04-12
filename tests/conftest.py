from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

import src.model_artifacts as model_artifacts
from src.constants import REQUIRED_COLUMNS


def build_complete_df(positions: list[str]) -> pd.DataFrame:
    rows = []
    for idx, position in enumerate(positions):
        row = {column: "0" for column in REQUIRED_COLUMNS}
        shots = 20 + idx
        shots_on_target = 10 + idx
        tackles_attempted = 25 + idx
        tackles_completed = 18 + idx
        headers_attempted = 30 + idx
        headers_won = 20 + idx
        passes_attempted = 500 + idx * 20
        passes_completed = 430 + idx * 18
        minutes = 900 + idx * 90
        pens = 5 + (idx % 3)
        pens_scored = pens - 1
        pens_faced = 4 + (idx % 2)
        pens_saved = 1 + (idx % 2)

        row.update(
            {
                "Inf": "",
                "Player": f"Player {idx}",
                "Nation": "England",
                "Club": f"Club {idx % 4}",
                "Division": "Division A",
                "Position": position,
                "Age": str(19 + idx),
                "Ability": str(100 + idx),
                "Potential": str(140 + idx),
                "Transfer Value": f"£{1.5 + idx * 0.1:.1f}M",
                "Wage": f"£{10 + idx}K p/w",
                "Recommendation": str(50 + idx),
                "Pres A": str(40 + idx),
                "Poss Won/90": f"{4.0 + idx * 0.2:.2f}",
                "K Tck/90": f"{1.0 + idx * 0.1:.2f}",
                "K Tck": str(10 + idx),
                "Itc": str(12 + idx),
                "Int/90": f"{2.0 + idx * 0.1:.2f}",
                "Clr/90": f"{1.5 + idx * 0.1:.2f}",
                "Clearances": str(30 + idx),
                "Blk/90": f"{0.8 + idx * 0.05:.2f}",
                "Pres A/90": f"{3.0 + idx * 0.2:.2f}",
                "Pres C": str(25 + idx),
                "Pres C/90": f"{2.0 + idx * 0.1:.2f}",
                "Shts Blckd/90": f"{0.4 + idx * 0.03:.2f}",
                "Tck R": "0",
                "Tck A": str(tackles_attempted),
                "Tck C": str(tackles_completed),
                "Tck/90": f"{2.2 + idx * 0.1:.2f}",
                "Shts Blckd": str(8 + idx),
                "Blk": str(10 + idx),
                "Shot/90": f"{2.5 + idx * 0.15:.2f}",
                "Shot %": "50%",
                "ShT/90": f"{1.3 + idx * 0.1:.2f}",
                "ShT": str(shots_on_target),
                "Shots From Outside The Box Per 90 minutes": f"{0.8 + idx * 0.05:.2f}",
                "Shots": str(shots),
                "Goals From Outside The Box": str(1 + (idx % 2)),
                "Free Kick Shots": str(2 + (idx % 2)),
                "xG/shot": f"{0.12 + idx * 0.005:.3f}",
                "Conv %": f"{12 + idx}%",
                "Svt": str(2 + idx),
                "Svp": str(3 + idx),
                "Svh": str(1 + idx),
                "Sv %": f"{70 + idx}%",
                "xSv %": f"{68 + idx}%",
                "xGP/90": f"{1.2 + idx * 0.08:.2f}",
                "xGP": str(25 + idx),
                "PsP": f"{8 + idx * 0.3:.2f}",
                "Poss Lost/90": f"{8.0 - idx * 0.2:.2f}",
                "Ps C/90": f"{25 + idx:.2f}",
                "Ps C": str(passes_completed),
                "Ps A/90": f"{30 + idx:.2f}",
                "Pas A": str(passes_attempted),
                "Pas %": f"{85 + idx * 0.2:.2f}%",
                "OP-KP/90": f"{1.0 + idx * 0.1:.2f}",
                "KP/90": f"{1.5 + idx * 0.1:.2f}",
                "Key": str(15 + idx),
                "CCC": str(5 + idx),
                "Ch C/90": f"{1.2 + idx * 0.08:.2f}",
                "Pr passes/90": f"{4.0 + idx * 0.15:.2f}",
                "Asts/90": f"{0.20 + idx * 0.02:.2f}",
                "Off": str(4 + idx),
                "Sprints/90": f"{18 + idx:.2f}",
                "Drb/90": f"{2.0 + idx * 0.1:.2f}",
                "Saves/90": f"{2.2 + idx * 0.1:.2f}",
                "Drb": str(30 + idx),
                "Dist/90": f"{10.5 + idx * 0.2:.2f}",
                "Distance": str(100 + idx * 5),
                "MLG": str(1 + (idx % 3)),
                "Yel": str(2 + (idx % 4)),
                "xG": f"{8.0 + idx * 0.3:.2f}",
                "Tcon/90": f"{1.1 + idx * 0.05:.2f}",
                "Red cards": str(idx % 2),
                "Pts/Gm": f"{1.0 + (idx % 5) * 0.2:.2f}",
                "PoM": str(idx % 3),
                "Pen/R": "0",
                "Pens S": str(pens_scored),
                "Pens Saved Ratio": "25%",
                "Pens Saved": str(pens_saved),
                "Pens Faced": str(pens_faced),
                "Pens": str(pens),
                "NP-xG/90": f"{0.45 + idx * 0.03:.2f}",
                "NP-xG": f"{7.5 + idx * 0.25:.2f}",
                "Mins/Gm": "90",
                "Minutes": str(minutes),
                "Goals per 90 minutes": f"{0.50 + idx * 0.04:.2f}",
                "Goals Conceded": str(10 + idx),
                "Goals": str(10 + idx),
                "Game Win Ratio": "50%",
                "Fouls Made": str(15 + idx),
                "Fouls Against": str(20 + idx),
                "xG/90": f"{0.42 + idx * 0.03:.2f}",
                "xG-OP": f"{0.05 + idx * 0.01:.2f}",
                "xA/90": f"{0.18 + idx * 0.02:.2f}",
                "xA": f"{4.0 + idx * 0.2:.2f}",
                "Con/90": f"{0.8 + idx * 0.05:.2f}",
                "Cln/90": f"{0.3 + idx * 0.02:.2f}",
                "Clean Sheets": str(8 + idx),
                "Rating": f"{6.8 + idx * 0.05:.2f}",
                "Mins/Gl": "180",
                "Assists": str(6 + idx),
                "OP-Crs C": str(20 + idx),
                "OP-Crs A": str(50 + idx),
                "Cr C": str(30 + idx),
                "Cr A": str(70 + idx),
                "Hdrs": str(headers_won),
                "Hdrs A": str(headers_attempted),
                "Hdr %": "60%",
                "Preferred Foot": "Right",
                "Right Foot": "Very Strong",
                "Left Foot": "Reasonable",
                "Height": "182",
                "OP-Cr %": "40%",
                "Appearances": str(10 + idx),
                "OP-Crs C/90": f"{0.9 + idx * 0.05:.2f}",
                "OP-Crs A/90": f"{2.2 + idx * 0.08:.2f}",
                "Hdrs L/90": f"{1.1 + idx * 0.04:.2f}",
                "Cr C/90": f"{1.1 + idx * 0.05:.2f}",
                "Crs A/90": f"{2.6 + idx * 0.08:.2f}",
                "Cr C/A": "40%",
                "AT League Apps": str(20 + idx),
                "AT Gls": str(8 + idx),
                "AT Apps": str(25 + idx),
                "K Hdrs/90": f"{0.7 + idx * 0.05:.2f}",
                "Hdrs W/90": f"{2.0 + idx * 0.08:.2f}",
                "Aer A/90": f"{3.0 + idx * 0.09:.2f}",
                "Actual Playing Time": str(minutes),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def dataframe_to_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(sep=";", index=False).encode("utf-8")


@pytest.fixture(autouse=True)
def isolated_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(model_artifacts, "ARTIFACT_DIR", tmp_path / "artifacts")
    yield


@pytest.fixture
def csv_buffer():
    def _build(df: pd.DataFrame) -> BytesIO:
        return BytesIO(dataframe_to_bytes(df))

    return _build
