"""End-to-end driver: Stage 1 -> 2 -> 3 -> 4 with the same interface as the
hosted REST endpoint, useful for batch evaluation runs.
"""
from __future__ import annotations

from typing import Any, Literal

from .client import Client
from .stage1_pattern_match import pattern_match_with_fallback
from .stage2_diffractgpt import diffractgpt_predict, extract_peaks
from .stage3_alignnff import alignnff_relax
from .stage4_refinement import rietveld_refine

Engine = Literal["none", "gsasii", "bgmn"]


def analyze(
    formula: str,
    elements: str,
    pattern: str,
    *,
    wavelength: float = 1.54184,
    use_diffractgpt: bool = True,
    use_alignnff: bool = False,
    refinement: Engine = "none",
    client: Client | None = None,
) -> dict[str, Any]:
    """Run the full AGAPI-XRD pipeline.

    Args:
        formula: chemical formula (e.g. "LaB6")
        elements: comma-separated element fallback (e.g. "La,B")
        pattern: two-column XRD data ("2theta intensity\\n...")
        wavelength: X-ray wavelength in Å (default Cu Kα)
        use_diffractgpt: run Stage 2 if Stage 1 fails
        use_alignnff: run Stage 3 between Stages 2 and 4
        refinement: Stage 4 engine ("none", "gsasii", or "bgmn")
        client: REST client; defaults to Client()

    Returns:
        dict with stage-by-stage results and the final candidate POSCAR.
    """
    if client is None:
        client = Client()

    output: dict[str, Any] = {"formula": formula, "stages": {}}

    s1 = pattern_match_with_fallback(formula, elements, pattern, wavelength, client=client)
    output["stages"]["stage1"] = s1

    candidate = s1.get("matched_poscar") if s1.get("status") == "success" else None
    source = s1.get("source") if s1.get("status") == "success" else None

    if candidate is None and use_diffractgpt:
        from io import StringIO
        import numpy as np

        data = np.loadtxt(StringIO(pattern.replace("\\n", "\n")))
        peaks = extract_peaks(data[:, 0], data[:, 1])
        s2 = diffractgpt_predict(formula, peaks, client=client)
        output["stages"]["stage2"] = s2
        if s2.get("status") == "success":
            candidate = s2.get("predicted_poscar")
            source = "diffractgpt"

    if candidate is None:
        output["status"] = "no_match"
        return output

    if use_alignnff:
        s3 = alignnff_relax(candidate, client=client)
        output["stages"]["stage3"] = s3
        if s3.get("status") == "success" and s3.get("relaxed_poscar"):
            candidate = s3["relaxed_poscar"]

    if refinement != "none":
        s4 = rietveld_refine(
            candidate, pattern, engine=refinement, wavelength=wavelength, client=client
        )
        output["stages"]["stage4"] = s4
        if s4.get("status") == "success" and s4.get("refined_poscar"):
            candidate = s4["refined_poscar"]

    output["status"] = "success"
    output["source"] = source
    output["final_poscar"] = candidate
    return output
