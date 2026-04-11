from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.decomposition import PCA

from src.constants import SEED


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    numerator = numerator.astype(float)
    denominator = denominator.astype(float)
    result = numerator / denominator.replace(0.0, np.nan)
    return result.replace([np.inf, -np.inf], np.nan)


def percentile_rank(series: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=series.index, dtype=float)
    mask = series.notna().to_numpy()
    valid = series.loc[mask]
    if valid.empty:
        return out
    ranks = valid.rank(method="average")
    out.iloc[np.flatnonzero(mask)] = (100.0 * ((ranks - 0.5) / len(valid))).to_numpy()
    return out


def zscore_series(series: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=series.index, dtype=float)
    mask = series.notna().to_numpy()
    valid = series.loc[mask]
    if len(valid) < 2:
        if len(valid) == 1:
            out.iloc[np.flatnonzero(mask)] = 0.0
        return out
    std = valid.std(ddof=0)
    if math.isclose(std, 0.0):
        out.iloc[np.flatnonzero(mask)] = 0.0
        return out
    out.iloc[np.flatnonzero(mask)] = ((valid - valid.mean()) / std).to_numpy()
    return out


def inverse_normal_rank(series: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=series.index, dtype=float)
    mask = series.notna().to_numpy()
    valid = series.loc[mask]
    if valid.empty:
        return out
    ranks = valid.rank(method="average")
    transformed = norm.ppf((ranks - 0.5) / len(valid))
    out.iloc[np.flatnonzero(mask)] = np.asarray(transformed, dtype=float)
    return out


def fit_single_component_pca(frame: pd.DataFrame, positive_reference: pd.Series) -> tuple[pd.Series, np.ndarray, float]:
    pca = PCA(n_components=1, random_state=SEED)
    scores = pca.fit_transform(frame.values.astype(float)).ravel()
    loadings = pca.components_[0].copy()
    ref = positive_reference.values.astype(float)
    if np.nanstd(ref) > 0 and np.nanstd(scores) > 0:
        corr = np.corrcoef(scores, ref)[0, 1]
        if np.isfinite(corr) and corr < 0:
            scores *= -1.0
            loadings *= -1.0
    return pd.Series(scores, index=frame.index, dtype=float), loadings, float(pca.explained_variance_ratio_[0])


def nonconstant_columns(frame: pd.DataFrame) -> list[str]:
    cols: list[str] = []
    for column in frame.columns:
        valid = frame[column].dropna()
        if not valid.empty and valid.nunique() > 1:
            cols.append(column)
    return cols


def flatten(values: Iterable[Iterable[str]]) -> list[str]:
    output: list[str] = []
    for chunk in values:
        output.extend(chunk)
    return output
