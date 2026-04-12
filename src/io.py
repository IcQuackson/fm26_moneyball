from __future__ import annotations

import hashlib
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from src.constants import DEFAULT_DIVISION, IDENTIFIER_COLUMNS, REQUIRED_COLUMNS
from src.parse_numeric import parse_numeric_series


def _normalize_columns(columns: list[str]) -> list[str]:
    normalized: list[str] = []
    for column in columns:
        clean = str(column).replace("\ufeff", "").strip()
        lower = clean.lower()
        if lower == "league":
            clean = "Division"
        elif lower == "division":
            clean = "Division"
        normalized.append(clean)
    return normalized


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
    raw_df.columns = _normalize_columns(raw_df.columns.tolist())
    missing = [column for column in REQUIRED_COLUMNS if column not in raw_df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    division_warning = None
    if "Division" not in raw_df.columns:
        raw_df["Division"] = DEFAULT_DIVISION
        division_warning = (
            "Division column was not present. Cohorts were computed within the whole upload for each broad role."
        )
        league_assumption = "upload_wide_broad_role_cohort"
        warnings = [
            "Division was not found, so each upload is treated as one broad-role cohort."
        ]
    else:
        league_assumption = "division_broad_role_cohort"
        warnings = [
            "Division column detected. Percentiles and category scores are computed within Division x Broad Role cohorts."
        ]

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
        "league_assumption": league_assumption,
        "warnings": warnings + ([division_warning] if division_warning is not None else []),
    }
    return df, metadata
