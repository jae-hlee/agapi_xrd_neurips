"""Stage 3: optional ALIGNN-FF structural relaxation.

Reduces local geometric artifacts in candidate structures (especially
DiffractGPT outputs) before they seed Stage 4 Rietveld refinement.
"""
from __future__ import annotations

from typing import Any

from .client import Client


def alignnff_relax(
    poscar: str,
    *,
    relax_cell: bool = True,
    fmax: float = 0.05,
    max_steps: int = 200,
    client: Client,
) -> dict[str, Any]:
    """Relax a structure with ALIGNN-FF.

    The fmax / max_steps defaults below mirror common ALIGNN-FF reference
    settings; the paper does not pin these to specific values, so override
    per-call if needed.
    """
    try:
        result = client.request(
            "alignn_ff/relax",
            {
                "poscar": poscar,
                "relax_cell": relax_cell,
                "fmax": fmax,
                "max_steps": max_steps,
            },
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    if isinstance(result, dict):
        return {
            "status": "success",
            "relaxed_poscar": result.get("POSCAR") or result.get("relaxed_poscar"),
            "n_steps": result.get("n_steps"),
            "max_force": result.get("max_force"),
            "raw": result,
        }
    if isinstance(result, str):
        return {"status": "success", "relaxed_poscar": result}
    return {"status": "error", "error": "Unexpected response type"}
