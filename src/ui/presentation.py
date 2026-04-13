from __future__ import annotations

import json
from functools import lru_cache
import html
from pathlib import Path

import pandas as pd
import streamlit as st


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

CATEGORY_ICONS = {
    "Shot Stopping": "target",
    "Goal Prevention": "shield",
    "Distribution": "arrow-right-left",
    "Ball Winning": "shield-check",
    "Box Defending": "shield",
    "Aerial Defending": "radar",
    "Progression": "arrow-right-left",
    "Defensive Security": "shield-check",
    "Defending": "shield",
    "Chance Creation": "sparkles",
    "Work Rate": "footprints",
    "Ball Retention": "brain-circuit",
    "Shooting": "circle-dot",
    "Finishing": "target",
    "Pressing": "zap",
    "Ball Security": "shield-check",
    "Shot Volume": "circle-dot",
    "Aerial Presence": "radar",
}

CATEGORY_HELP = {
    "Shot Stopping": "How well the keeper stops shots. This score is driven by saves, save rates, post-shot expected goals faced, and penalty-saving output.",
    "Goal Prevention": "How well the keeper prevents goals across handling and concession outcomes. It looks at handling events, goals conceded, and clean-sheet rate.",
    "Distribution": "How safely and effectively the keeper moves the ball. It uses passing volume, pass completion, passing progression, and progressive passes.",
    "Ball Winning": "How often the player breaks up play and wins the ball back. It is built from pressures won, possessions won, key tackles, interceptions, total tackles, and tackle success.",
    "Box Defending": "How much the player protects the penalty area. It focuses on clearances, blocks, and shots blocked.",
    "Aerial Defending": "How strong the player is in defensive aerial duels. It uses headers won, header win rate, key headers, aerial attempts, and avoids rewarding headers lost.",
    "Progression": "How well the player helps move the ball forward. It is based on passing progression, progressive passes, passing volume, and in some roles dribbling or key-pass involvement.",
    "Defensive Security": "How safely the player defends without giving away cheap damage. It is driven by fouls, yellow cards, red cards, and mistakes leading to goals, with fewer negatives scoring better.",
    "Defending": "How much the player wins defensive actions in wide areas. It uses possessions won, key tackles, interceptions, total tackles, and tackle success.",
    "Chance Creation": "How much the player creates shots and good chances for teammates. It uses key passes, open-play key passes, chances created, clear-cut chances, expected assists, and assists.",
    "Work Rate": "How much ground and repeated running the player contributes. It is based on sprints and distance covered.",
    "Ball Retention": "How well the player keeps possession under control. It rewards secure passing and penalizes losing the ball.",
    "Shooting": "How much the player contributes as a shooter from midfield. It combines shot volume, shots on target, expected goals, shot quality, and goals versus expected goals.",
    "Finishing": "How well the player turns shots into goals and dangerous shooting outcomes. It combines shot accuracy, conversion, shot quality, goals, and goals versus expected goals.",
    "Pressing": "How much the player contributes to pressing and regaining the ball high or early. It uses pressure attempts, pressure wins, and in some roles possessions won.",
    "Ball Security": "How safely the player handles the ball and avoids cheap mistakes in attacking roles. It penalizes losing possession, offsides, fouls, cards, and mistakes leading to goals.",
    "Shot Volume": "How often the player gets shots away and tests the goal. It is driven by shots, shots on target, and expected-goal volume.",
    "Aerial Presence": "How much the player offers in the air. It uses headers won, header win rate, key headers, and total aerial involvement.",
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

COLUMN_HELP = {
    "Rank": "Placement in this table after sorting by overall score within the selected league and role.",
    "Player": "Player name from the FM export.",
    "League": "Division detected from the uploaded data.",
    "Position": "Raw FM position string from the export.",
    "Club": "Player club from the export.",
    "Role": "Broad role cohort used for scoring.",
    "Age": "Player age from the export.",
    "Minutes": "League minutes used for shrinkage and uncertainty.",
    "Goals": "Raw goal total from the export. This is a season count, not adjusted.",
    "Assists": "Raw assist total from the export. This is a season count, not adjusted.",
    "Transfer Value": "Parsed FM transfer value. Used for cost scoring, not performance scoring.",
    "Performance": "Overall score for this role. It combines the role-trait scores after smoothing noisy stats and adjusting for team strength. Higher is better.",
    "Performance Grade": "Simple label for the Performance score, such as Elite, Strong, or Average.",
    "Top Trait": "The role trait where this player scores highest.",
    "Trait Score": "Score for the player's strongest role trait. Higher means that part of the game stands out more versus same-role players.",
    "Trait Grade": "Text band for the trait score.",
    "Standout Trait": "Highest family score for this player inside the selected role.",
    "Value Pick": "Moneyball score. Higher means better performance for the price.",
    "Value Grade": "Text band for the Value Pick score.",
    "Price Level": "Cost score from transfer value and wage. Higher means more expensive versus same-role players.",
    "Scout Confidence": "Simple confidence label derived from uncertainty. Higher uncertainty means lower confidence.",
    "Confidence": "Simple confidence label derived from uncertainty. Higher uncertainty means lower confidence.",
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


def trait_icon(label: str) -> str:
    return CATEGORY_ICONS.get(label, "circle-dot")


def label_with_icon(label: str) -> str:
    return f"{trait_icon(label)} {label}"


def strip_icon_prefix(label: str) -> str:
    for category_label in CATEGORY_LABELS.values():
        prefixed = label_with_icon(category_label)
        if label == prefixed:
            return category_label
    for category_label in CATEGORY_LABELS.values():
        icon_prefix = f"{trait_icon(category_label)} "
        long_prefix = f"{icon_prefix}{category_label} | "
        if label.startswith(long_prefix):
            return category_label
        short_prefix = f"{icon_prefix}"
        if label.startswith(short_prefix):
            remainder = label[len(short_prefix):]
            if remainder == category_label:
                return category_label
    return label


def column_help_text(column: str) -> str | None:
    normalized = strip_icon_prefix(column)
    if normalized in COLUMN_HELP:
        return COLUMN_HELP[normalized]
    if normalized in CATEGORY_HELP:
        return CATEGORY_HELP[normalized]
    return None


@lru_cache(maxsize=None)
def svg_icon_markup(icon_name: str) -> str:
    path = Path("assets") / "icons" / f"{icon_name}.svg"
    if not path.exists():
        return ""
    svg = path.read_text(encoding="utf-8")
    svg = svg.replace("<svg", '<svg class="league-trait-icon"')
    return svg


def _custom_table_cell_value(column: str, value, percent_columns: set[str], money_columns: set[str]) -> str:
    if column in percent_columns:
        text = percentile_text(value)
    elif column in money_columns:
        text = money_text(value)
    elif value is None or pd.isna(value):
        text = "NA"
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        text = whole_number_text(value)
    else:
        text = str(value)
    return html.escape(text)


def render_icon_table(
    frame: pd.DataFrame,
    *,
    icon_headers: dict[str, tuple[str, str | None]] | None = None,
    percent_columns: list[str] | None = None,
    money_columns: list[str] | None = None,
) -> str:
    percent_columns = set(percent_columns or [])
    money_columns = set(money_columns or [])
    icon_headers = icon_headers or {}

    headers_html: list[str] = []
    for column in frame.columns:
        icon_name, help_text = icon_headers.get(column, ("", column_help_text(column)))
        icon_markup = svg_icon_markup(icon_name) if icon_name else ""
        title_attr = f' title="{html.escape(help_text)}"' if help_text else ""
        header_label = html.escape(column)
        if icon_markup:
            header_html = (
                f'<th{title_attr}><div class="league-trait-header">'
                f'<span class="league-trait-header-icon">{icon_markup}</span>'
                f'<span>{header_label}</span>'
                f"</div></th>"
            )
        else:
            header_html = f"<th{title_attr}>{header_label}</th>"
        headers_html.append(header_html)

    rows_html: list[str] = []
    for _, row in frame.iterrows():
        cells: list[str] = []
        for column in frame.columns:
            classes = ["league-trait-cell"]
            inline_style = ""
            if column in percent_columns:
                inline_style = f' style="{percentile_style(row[column])}"'
            cells.append(f'<td class="{" ".join(classes)}"{inline_style}>{_custom_table_cell_value(column, row[column], percent_columns, money_columns)}</td>')
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    return (
        '<div class="league-trait-table-wrap">'
        '<table class="league-trait-table">'
        f"<thead><tr>{''.join(headers_html)}</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        "</table></div>"
    )


def column_config_for(frame: pd.DataFrame) -> dict[str, object]:
    config: dict[str, object] = {}
    for column in frame.columns:
        help_text = column_help_text(column)
        if help_text:
            config[column] = st.column_config.Column(column, help=help_text)
    return config


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
        return "rgba(71, 85, 105, 0.38)"
    value = float(value)
    if value >= 90:
        return "rgba(34, 211, 238, 0.32)"
    if value >= 75:
        return "rgba(59, 130, 246, 0.30)"
    if value >= 60:
        return "rgba(16, 185, 129, 0.28)"
    if value >= 40:
        return "rgba(14, 116, 144, 0.24)"
    if value >= 25:
        return "rgba(249, 115, 22, 0.22)"
    return "rgba(239, 68, 68, 0.24)"


def percentile_style(value: float | int | None) -> str:
    color = percentile_color(value)
    return f"background-color: {color}; color: #e0f2fe; font-weight: 600;"


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
