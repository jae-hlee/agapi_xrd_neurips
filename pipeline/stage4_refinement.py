"""Stage 4: automated Rietveld refinement (GSAS-II or BGMN).

Sequential cumulative parameter release:
    background (12-term Chebyshev)
        -> unit-cell parameters
        -> instrument zero point
        -> profile parameters (U, V, W, X, Y, SH/L)
        -> sample displacement
Optional March-Dollase preferred-orientation correction.
Convergence: relative change in R_wp < 1e-4 for two successive cycles.
"""
from __future__ import annotations

from typing import Any, Literal

from .client import Client

Engine = Literal["gsasii", "bgmn"]


def rietveld_refine(
    poscar: str,
    pattern: str,
    *,
    engine: Engine = "gsasii",
    wavelength: float = 1.54184,
    march_dollase: bool = False,
    client: Client,
) -> dict[str, Any]:
    """Run automated Rietveld refinement against a powder XRD pattern.

    Args:
        poscar: candidate structure as POSCAR string
        pattern: two-column 2theta/intensity data
        engine: "gsasii" or "bgmn"
        wavelength: X-ray wavelength in Å
        march_dollase: enable preferred-orientation correction
        client: REST client

    Returns:
        dict with refined_poscar, R_wp, R_p, refined lattice parameters, etc.
    """
    try:
        result = client.request(
            "rietveld/refine",
            {
                "poscar": poscar,
                "pattern": pattern,
                "engine": engine,
                "wavelength": wavelength,
                "march_dollase": march_dollase,
            },
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    if isinstance(result, dict):
        result.setdefault("status", "success")
        return result
    return {"status": "error", "error": "Unexpected response type"}
