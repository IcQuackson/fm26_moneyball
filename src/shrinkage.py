from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.constants import BINOMIAL_PRIMITIVES, NORMAL_PRIMITIVES, RATE_PRIMITIVES


def estimate_beta_prior(successes: pd.Series, attempts: pd.Series) -> tuple[float, float]:
    mask = attempts.gt(0) & successes.notna()
    if mask.sum() < 2:
        return 1.0, 1.0
    y = successes[mask].astype(float)
    n = attempts[mask].astype(float)
    p = y / n
    weights = n / n.sum()
    mean_p = float((weights * p).sum())
    var_p = float((weights * (p - mean_p) ** 2).sum())
    var_floor = mean_p * (1.0 - mean_p) / (n.mean() + 1.0)
    adjusted_var = max(var_p, var_floor + 1e-6)
    total = max(mean_p * (1.0 - mean_p) / adjusted_var - 1.0, 2.0)
    alpha = max(mean_p * total, 1e-3)
    beta = max((1.0 - mean_p) * total, 1e-3)
    return alpha, beta


def estimate_gamma_poisson_strength(rate: pd.Series, exposure: pd.Series) -> tuple[float, float]:
    mask = rate.notna() & exposure.gt(0)
    if mask.sum() < 2:
        return 5.0, float(rate[mask].mean()) if mask.any() else 0.0
    rates = rate[mask].astype(float)
    exp = exposure[mask].astype(float)
    mu = float(np.average(rates, weights=exp))
    if math.isclose(mu, 0.0):
        return 5.0, 0.0
    observed_var = float(np.average((rates - mu) ** 2, weights=exp))
    poisson_noise = float(np.mean(mu / np.maximum(exp, 1e-6)))
    overdispersion = max(observed_var - poisson_noise, 1e-6)
    k = float(np.clip(mu / overdispersion, 0.1, 10_000.0))
    return k, mu


def estimate_normal_tau(values: pd.Series, exposure: pd.Series) -> tuple[float, float]:
    mask = values.notna() & exposure.gt(0)
    if mask.sum() < 2:
        return 1.0, float(values[mask].mean()) if mask.any() else 0.0
    vals = values[mask].astype(float)
    exp = exposure[mask].astype(float)
    mean_val = float(np.average(vals, weights=exp))
    total_var = float(np.average((vals - mean_val) ** 2, weights=exp))
    noise_proxy = float(np.average(np.abs(vals - mean_val), weights=1.0 / np.maximum(exp, 1e-6)) ** 2)
    signal = max(total_var - noise_proxy, 1e-6)
    tau = float(np.clip(np.median(exp) * noise_proxy / signal, 1e-3, 10_000.0))
    return tau, mean_val


def shrink_role_primitives(role_df: pd.DataFrame, primitive_columns: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    shrunk = pd.DataFrame(index=role_df.index, columns=primitive_columns, dtype=float)
    shrink_delta = pd.DataFrame(index=role_df.index, columns=primitive_columns, dtype=float)
    metadata: dict[str, dict] = {}
    exposure = role_df["E"].astype(float)

    for primitive in primitive_columns:
        if primitive == "E":
            shrunk[primitive] = exposure
            shrink_delta[primitive] = 0.0
            continue

        if primitive in BINOMIAL_PRIMITIVES:
            success_col, attempt_col = BINOMIAL_PRIMITIVES[primitive]
            successes = role_df[success_col].astype(float)
            attempts = role_df[attempt_col].astype(float)
            alpha, beta = estimate_beta_prior(successes, attempts)
            value = (successes + alpha) / (attempts + alpha + beta)
            value = value.where(attempts.gt(0))
            metadata[primitive] = {"model": "beta_binomial", "alpha": alpha, "beta": beta}
        elif primitive in RATE_PRIMITIVES:
            rate = role_df[primitive].astype(float)
            k, mu = estimate_gamma_poisson_strength(rate, exposure)
            implied_count = rate * exposure
            value = (implied_count + k * mu) / (exposure + k)
            metadata[primitive] = {"model": "gamma_poisson", "k": k, "mu": mu}
        else:
            raw = role_df[primitive].astype(float)
            tau, mean_val = estimate_normal_tau(raw, exposure)
            weight = exposure / (exposure + tau)
            value = weight * raw + (1.0 - weight) * mean_val
            metadata[primitive] = {"model": "normal", "tau": tau, "mean": mean_val}

        shrunk[primitive] = value
        shrink_delta[primitive] = (role_df[primitive].astype(float) - value).abs()

    return shrunk, shrink_delta, metadata
