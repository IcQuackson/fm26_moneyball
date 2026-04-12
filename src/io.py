from __future__ import annotations

import hashlib
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from src.constants import DEFAULT_DIVISION, IDENTIFIER_COLUMNS, REQUIRED_COLUMNS
from src.parse_numeric import parse_numeric_series


def _read_bytes(source: Any) -> bytes:
    if hasattr(source, "read"):
        payload = source.read()
        if hasattr(source, "seek"):
            source.seek(0)
        return payload
    if isinstance(source, bytes):
        return source
    return Path(source).read_bytes()


def load_fm_csv(source: Any) -> tuple[pd.DataFrame, dict]:
    payload = _read_bytes(source)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        text = payload.decode("latin-1")

    raw_df = pd.read_csv(StringIO(text), sep=";", dtype=str, keep_default_na=False)
    missing = [column for column in REQUIRED_COLUMNS if column not in raw_df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    division_warning = None
    if "Division" not in raw_df.columns:
        raw_df["Division"] = DEFAULT_DIVISION
        division_warning = (
            "Division column was not present. Cohorts were computed within the whole upload for each broad role."
        )

    parsed_df = raw_df.copy()
    for column in raw_df.columns:
        if column not in IDENTIFIER_COLUMNS and column != "Position":
            parsed_df[column] = parse_numeric_series(raw_df[column])
    raw_suffix_df = raw_df.add_suffix("__raw")
    df = pd.concat([pd.Series(range(len(raw_df)), name="player_id"), parsed_df, raw_suffix_df], axis=1)

    file_hash = hashlib.sha256(payload).hexdigest()
    metadata = {
        "file_hash": file_hash,
        "row_count": int(len(df)),
        "missingness": raw_df.replace("", pd.NA).isna().mean().sort_values(ascending=False),
        "league_assumption": "unverified_single_upload_cohort",
        "warnings": [
            "League homogeneity cannot be verified because the export has no League column. One uploaded file is treated as one cohort."
        ]
        + ([division_warning] if division_warning is not None else []),
    }
    return df, metadata
