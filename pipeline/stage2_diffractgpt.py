"""Stage 2: generative structure prediction via DiffractGPT.

The prompt is the top-N peak list (sorted by intensity, default N=20) plus
the chemical formula token. The Mistral-7B fine-tune emits a complete
structural description (lattice parameters, space group, fractional atomic
coordinates) which is returned as a POSCAR string.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy.signal import find_peaks

from .client import Client


TOP_K_PEAKS = 20
PEAK_HEIGHT = 0.05
PEAK_PROMINENCE = 0.02


def extract_peaks(
    two_theta: np.ndarray,
    intensity: np.ndarray,
    top_k: int = TOP_K_PEAKS,
) -> list[tuple[float, float]]:
    """Extract the top-k peaks (by intensity) from a binned XRD pattern."""
    intensity = np.asarray(intensity, dtype=float)
    if intensity.max() > 0:
        norm = intensity / intensity.max()
    else:
        norm = intensity
    distance = max(1, len(intensity) // 200)
    idx, _ = find_peaks(
        norm,
        height=PEAK_HEIGHT,
        prominence=PEAK_PROMINENCE,
        distance=distance,
    )
    if len(idx) == 0:
        return []
    order = np.argsort(-norm[idx])[:top_k]
    return [(float(two_theta[i]), float(norm[i])) for i in idx[order]]


def diffractgpt_predict(
    formula: str,
    peaks: list[tuple[float, float]] | str,
    *,
    client: Client,
) -> dict[str, Any]:
    """Call the DiffractGPT endpoint with a peak list and chemical formula."""
    if isinstance(peaks, list):
        peaks_str = "\n".join(f"{tt:.4f} {h:.4f}" for tt, h in peaks)
    else:
        peaks_str = peaks

    try:
        result = client.request(
            "diffractgpt/query",
            {"formula": formula, "peaks": peaks_str},
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    if isinstance(result, dict):
        return {
            "status": "success",
            "predicted_poscar": result.get("POSCAR"),
            "formula": formula,
            "raw": result,
        }
    if isinstance(result, str):
        return {
            "status": "success",
            "predicted_poscar": result,
            "formula": formula,
        }
    return {"status": "error", "error": "Unexpected response type"}
