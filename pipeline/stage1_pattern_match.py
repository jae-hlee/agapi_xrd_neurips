"""Stage 1: cosine-similarity pattern matching against JARVIS-DFT and COD.

Implements the procedure described in Section 3 of the paper:
    1. Re-bin experimental and simulated patterns onto a common 2theta grid
       (0--90 deg, 0.1 deg spacing).
    2. Compute cosine similarity between binned intensity vectors.
    3. Try formula-based search first; fall back to element-only search if
       no candidate exceeds the configured similarity threshold.
"""
from __future__ import annotations

from typing import Any

from .client import Client


# Cosine-similarity acceptance thresholds. The paper does not enumerate
# specific cut-offs; the values below are conservative defaults the user
# can override per-call. Lowering them increases recall at the cost of
# noisier matches.
FORMULA_THRESHOLD = 0.50
ELEMENT_THRESHOLD = 0.40
DEFAULT_WAVELENGTH = 1.54184  # Cu Kα in Å


def pattern_match(
    formula: str,
    pattern: str,
    wavelength: float = DEFAULT_WAVELENGTH,
    *,
    client: Client,
) -> dict[str, Any]:
    """Run Stage 1 pattern matching for one query.

    Args:
        formula: chemical formula (e.g. "LaB6") or comma-separated element list
                 ("La,B" for the element-only fallback search)
        pattern: two-column XRD data string ("2theta intensity" per line)
        wavelength: X-ray wavelength in Å
        client: REST client

    Returns:
        dict with keys:
            status, matched_poscar, similarity, source ("formula" or "elements"),
            top_k (list of (jid, score) tuples)
    """
    full_pattern = f"{formula};{wavelength}\n{pattern}"
    try:
        result = client.request("pxrd/query", {"pattern": full_pattern})
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        return {
            "status": "success",
            "matched_poscar": result,
            "source": "formula",
        }
    return {"status": "error", "error": "Unexpected response type"}


def pattern_match_with_fallback(
    formula: str,
    elements: str,
    pattern: str,
    wavelength: float = DEFAULT_WAVELENGTH,
    *,
    client: Client,
) -> dict[str, Any]:
    """Try formula-based pattern matching; fall back to element-only search."""
    primary = pattern_match(formula, pattern, wavelength, client=client)
    sim = primary.get("similarity", 0.0) or 0.0
    if primary.get("status") == "success" and sim >= FORMULA_THRESHOLD:
        primary["source"] = "formula"
        return primary

    fallback = pattern_match(elements, pattern, wavelength, client=client)
    if fallback.get("status") == "success" and (fallback.get("similarity", 0.0) or 0.0) >= ELEMENT_THRESHOLD:
        fallback["source"] = "elements"
        return fallback

    return {"status": "no_match", "primary": primary, "fallback": fallback}
