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
        return "#f3f4f6"
    value = float(value)
    if value >= 90:
        return "#0f766e"
    if value >= 75:
        return "#16a34a"
    if value >= 60:
        return "#65a30d"
    if value >= 40:
        return "#ca8a04"
    if value >= 25:
        return "#ea580c"
    return "#dc2626"


def percentile_style(value: float | int | None) -> str:
    color = percentile_color(value)
    text = "#ffffff" if color not in {"#f3f4f6", "#ca8a04"} else "#111827"
    return f"background-color: {color}; color: {text}; font-weight: 600;"
