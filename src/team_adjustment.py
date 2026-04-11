from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor, LinearRegression

from src.utils import zscore_series


def adjust_role_metrics(role_df: pd.DataFrame, primitive_columns: list[str]) -> tuple[pd.DataFrame, dict, list[str]]:
    adjusted = pd.DataFrame(index=role_df.index, columns=primitive_columns, dtype=float)
    metadata: dict[str, dict] = {}
    warnings: list[str] = []

    pts_z = zscore_series(role_df["Pts/Gm"].astype(float))
    unique_pts = role_df["Pts/Gm"].dropna().nunique()
    use_fallback = unique_pts < 2 or pts_z.dropna().empty
    if use_fallback:
        warnings.append("Pts/Gm has insufficient variance for robust team adjustment; standardized metrics were used directly.")

    for primitive in primitive_columns:
        values = role_df[primitive].astype(float)
        if use_fallback or values.dropna().shape[0] < 3:
            adjusted[primitive] = values
            metadata[primitive] = {"used_adjustment": False}
            continue

        mask = values.notna() & pts_z.notna()
        if mask.sum() < 3:
            adjusted[primitive] = values
            metadata[primitive] = {"used_adjustment": False}
            continue

        x = pts_z.loc[mask].to_numpy().reshape(-1, 1)
        y = values.loc[mask].to_numpy()
        estimator_name = "huber"
        try:
            model = HuberRegressor(max_iter=500)
            model.fit(x, y)
        except ValueError as exc:
            warnings.append(
                f"{primitive}: Huber team adjustment failed ({exc}); falling back to linear regression."
            )
            model = LinearRegression()
            model.fit(x, y)
            estimator_name = "linear_regression_fallback"

        pred = pd.Series(model.predict(x), index=values.loc[mask].index)
        residual_values = values.loc[mask] - pred
        pts_used = pts_z.loc[mask]
        pts_variance = float(np.var(pts_used))
        if pts_variance > 0:
            slope = float(np.cov(residual_values, pts_used, ddof=0)[0, 1] / pts_variance)
            residual_values = residual_values - slope * pts_used
        residual_values = residual_values - residual_values.mean()

        residuals = pd.Series(np.nan, index=values.index, dtype=float)
        residuals.loc[mask] = residual_values
        adjusted[primitive] = residuals.fillna(values)
        metadata[primitive] = {
            "used_adjustment": True,
            "estimator": estimator_name,
            "intercept": float(model.intercept_),
            "coef": float(np.ravel(model.coef_)[0]),
        }
    return adjusted, metadata, warnings
