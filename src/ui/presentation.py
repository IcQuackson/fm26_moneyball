from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd


CATEGORY_LABELS = {
    "shot_stopper": "Shot Stopping",
    "prevention_control": "Goal Prevention",
    "distributor": "Distribution",
    "ball_winner": "Ball Winning",
    "box_defender": "Box Defending",
    "aerial_defender": "Aerial Defending",
    "progressor": "Progression",
    "discipline_security": "Defensive Security",
    "defender": "Defending",
    "creator": "Chance Creation",
    "engine": "Work Rate",
    "retainer": "Ball Retention",
    "shooter": "Shooting",
    "finisher": "Finishing",
    "presser": "Pressing",
    "security": "Ball Security",
    "shot_volume": "Shot Volume",
    "aerial_presence": "Aerial Presence",
}

ROLE_LABELS = {
    "GK": "Goalkeeper",
    "CB": "Centre-Back",
    "FB_WB": "Full-Back / Wing-Back",
    "DM": "Defensive Midfielder",
    "CM": "Central Midfielder",
    "AM_W": "Attacker / Winger",
    "ST": "Striker",
}


@lru_cache(maxsize=1)
def abbreviation_mapping() -> dict[str, str]:
    mapping_path = Path("fm26_abbreviation_mapping.json")
    if not mapping_path.exists():
        return {}
    return json.loads(mapping_path.read_text())


def format_metric_label(metric: str) -> str:
    if metric in CATEGORY_LABELS:
        return CATEGORY_LABELS[metric]
    mapped = abbreviation_mapping().get(metric)
    if mapped:
        return mapped
    return metric.replace("__score", "").replace("__raw", "").replace("_", " ").title()


def format_role_label(role: str) -> str:
    return ROLE_LABELS.get(role, role)


def trait_label(metric: str) -> str:
    return format_metric_label(metric.replace("__score", ""))


def percentile_band(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "Not enough data"
    value = float(value)
    if value >= 90:
        return "Elite"
    if value >= 75:
        return "Strong"
    if value >= 60:
        return "Good"
    if value >= 40:
        return "Average"
    if value >= 25:
        return "Below Average"
    return "Weak"


def confidence_label(uncertainty_score: float | int | None) -> tuple[str, float | None]:
    if uncertainty_score is None or pd.isna(uncertainty_score):
        return "Still computing", None
    confidence = max(0.0, min(100.0, 100.0 - float(uncertainty_score)))
    return percentile_band(confidence), confidence


def percentile_color(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "#e5e7eb"
    value = float(value)
    if value >= 90:
        return "#99f6e4"
    if value >= 75:
        return "#bbf7d0"
    if value >= 60:
        return "#d9f99d"
    if value >= 40:
        return "#fde68a"
    if value >= 25:
        return "#fed7aa"
    return "#fecaca"


def percentile_style(value: float | int | None) -> str:
    color = percentile_color(value)
    return f"background-color: {color}; color: #111827; font-weight: 600;"


def percentile_text(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{float(value):.0f}/100"


def compact_number(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "NA"
    value = float(value)
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.0f}K"
    return f"{value:.0f}"


def money_text(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"£{compact_number(value)}"


def whole_number_text(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{float(value):.0f}"


def formatted_table(frame: pd.DataFrame, percent_columns: list[str] | None = None, money_columns: list[str] | None = None) -> pd.io.formats.style.Styler:
    percent_columns = percent_columns or []
    money_columns = money_columns or []
    formatter: dict[str, object] = {}
    for column in frame.columns:
        if column in percent_columns:
            formatter[column] = percentile_text
        elif column in money_columns:
            formatter[column] = money_text
        elif pd.api.types.is_float_dtype(frame[column]) or pd.api.types.is_integer_dtype(frame[column]):
            formatter[column] = whole_number_text
    styler = frame.style.format(formatter)
    if percent_columns:
        styler = styler.map(percentile_style, subset=percent_columns)
    return styler
