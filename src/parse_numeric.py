from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd


MULTIPLIERS = {
    "k": 1_000.0,
    "m": 1_000_000.0,
    "b": 1_000_000_000.0,
}


def _clean_numeric_token(token: str) -> float | None:
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*([kmb])?", token.lower())
    if not match:
        return None
    value = float(match.group(1))
    suffix = match.group(2)
    if suffix:
        value *= MULTIPLIERS[suffix]
    return value


def parse_numeric_value(value: Any) -> float:
    if value is None:
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)

    text = str(value).strip()
    if not text or text in {"-", "--", "—", "n/a", "N/A"}:
        return np.nan

    is_percent = "%" in text
    numeric_tokens = re.findall(r"-?\d+(?:\.\d+)?\s*[kmbKMB]?", text.replace(",", ""))
    if numeric_tokens:
        parsed = [_clean_numeric_token(token) for token in numeric_tokens]
        parsed = [token for token in parsed if token is not None]
        if parsed:
            value_num = float(sum(parsed) / len(parsed))
            return value_num / 100.0 if is_percent else value_num

    stripped = re.sub(r"[^\d.\-]", "", text.replace(",", ""))
    try:
        value_num = float(stripped)
    except ValueError:
        return np.nan
    return value_num / 100.0 if is_percent else value_num


def parse_numeric_series(series: pd.Series) -> pd.Series:
    return series.map(parse_numeric_value).astype(float)
