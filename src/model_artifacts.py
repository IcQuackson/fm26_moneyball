from __future__ import annotations

import pickle
from pathlib import Path

from src.constants import ARTIFACT_VERSION


ARTIFACT_DIR = Path("artifacts")


def artifact_path(file_hash: str) -> Path:
    ARTIFACT_DIR.mkdir(exist_ok=True)
    return ARTIFACT_DIR / f"{file_hash}.pkl"


def load_artifact(file_hash: str):
    path = artifact_path(file_hash)
    if not path.exists():
        return None
    payload = pickle.loads(path.read_bytes())
    if payload.get("artifact_version") != ARTIFACT_VERSION:
        return None
    return payload


def save_artifact(file_hash: str, payload) -> None:
    payload = dict(payload)
    payload["artifact_version"] = ARTIFACT_VERSION
    artifact_path(file_hash).write_bytes(pickle.dumps(payload))
