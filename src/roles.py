from __future__ import annotations

import re

import pandas as pd

from src.constants import ROLE_ORDER


def detect_roles(position: str) -> list[str]:
    text = (position or "").upper()
    roles: list[str] = []

    if "GK" in text:
        roles.append("GK")
    if re.search(r"\bD\s*\((?:C|LC|RC|LRC|RLC)\)", text):
        roles.append("CB")
    if re.search(r"\b(?:D|WB|D/WB)\s*\((?:L|R|LR|RL)\)", text):
        roles.append("FB_WB")
    if re.search(r"\bDM\b", text):
        roles.append("DM")
    if re.search(r"\bM\s*\(C\)", text) and "AM (C)" not in text and "DM" not in text:
        roles.append("CM")
    if any(token in text for token in ["AM (C)", "AM (L)", "AM (R)", "M (L)", "M (R)"]):
        roles.append("AM_W")
    if "ST" in text:
        roles.append("ST")

    ordered = [role for role in ROLE_ORDER if role in roles]
    return ordered


def expand_player_roles(df: pd.DataFrame) -> pd.DataFrame:
    expanded = df.copy()
    expanded["eligible_roles"] = expanded["Position__raw"].map(detect_roles)
    expanded = expanded.explode("eligible_roles").rename(columns={"eligible_roles": "broad_role"})
    expanded = expanded[expanded["broad_role"].notna()].copy()
    expanded["player_role_id"] = expanded["player_id"].astype(str) + "::" + expanded["broad_role"]
    return expanded.reset_index(drop=True)
