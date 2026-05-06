"""Evaluation metrics used in the AGAPI-XRD paper.

MAE, RMSE, R^2, skill score, and Jensen-Shannon divergence with Laplace
smoothing for histogram-level comparisons.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Metrics:
    mae: float
    rmse: float
    r2: float
    median_abs: float
    mad_exp: float
    skill: float
    jsd: float


def _to_array(values) -> np.ndarray:
    return np.asarray(values, dtype=float)


def mae(predicted, reference) -> float:
    p, r = _to_array(predicted), _to_array(reference)
    return float(np.mean(np.abs(p - r)))


def rmse(predicted, reference) -> float:
    p, r = _to_array(predicted), _to_array(reference)
    return float(np.sqrt(np.mean((p - r) ** 2)))


def r2(predicted, reference) -> float:
    p, r = _to_array(predicted), _to_array(reference)
    ss_res = float(np.sum((p - r) ** 2))
    ss_tot = float(np.sum((r - np.mean(r)) ** 2))
    if ss_tot == 0.0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


def median_abs(predicted, reference) -> float:
    p, r = _to_array(predicted), _to_array(reference)
    return float(np.median(np.abs(p - r)))


def mad(values) -> float:
    v = _to_array(values)
    return float(np.mean(np.abs(v - np.mean(v))))


def skill_score(predicted, reference) -> float:
    """Skill = 1 - MAE / MAD(reference). Positive values beat the mean predictor."""
    m = mae(predicted, reference)
    d = mad(reference)
    if d == 0.0:
        return float("nan")
    return 1.0 - m / d


def jsd(predicted, reference, n_bins: int = 50, alpha: float = 1.0) -> float:
    """Jensen-Shannon divergence between two distributions with Laplace smoothing."""
    p_arr = _to_array(predicted)
    r_arr = _to_array(reference)
    lo = float(min(p_arr.min(), r_arr.min()))
    hi = float(max(p_arr.max(), r_arr.max()))
    edges = np.linspace(lo, hi, n_bins + 1)

    p_hist, _ = np.histogram(p_arr, bins=edges)
    r_hist, _ = np.histogram(r_arr, bins=edges)

    p_smooth = (p_hist + alpha) / np.sum(p_hist + alpha)
    r_smooth = (r_hist + alpha) / np.sum(r_hist + alpha)
    m = 0.5 * (p_smooth + r_smooth)

    def _kl(a: np.ndarray, b: np.ndarray) -> float:
        mask = a > 0
        return float(np.sum(a[mask] * np.log(a[mask] / b[mask])))

    return 0.5 * _kl(p_smooth, m) + 0.5 * _kl(r_smooth, m)


def all_metrics(predicted, reference, n_bins: int = 50) -> Metrics:
    return Metrics(
        mae=mae(predicted, reference),
        rmse=rmse(predicted, reference),
        r2=r2(predicted, reference),
        median_abs=median_abs(predicted, reference),
        mad_exp=mad(reference),
        skill=skill_score(predicted, reference),
        jsd=jsd(predicted, reference, n_bins=n_bins),
    )
