"""18-candidate cell-matching protocol (Section 3.1 of the paper).

For each candidate structure, we generate three cell variants
    (1) original cell as returned by the pipeline
    (2) primitive cell from space-group analysis
    (3) conventional cell from space-group analysis
and evaluate all six axis permutations of each variant with consistent angle
remapping (alpha = angle(b,c), beta = angle(a,c), gamma = angle(a,b)).

The optimum among 3 x 6 = 18 candidates is selected by a composite score
that combines relative length error, relative angle error, and volume error.
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np


# Composite-score weights for ranking the 18 cell candidates.
# The paper specifies that the score combines length, angle, and volume errors,
# but does not fix particular weights. The values below are equal-weight defaults;
# tune via the constructor or override at the call site for production use.
COMPOSITE_W_LENGTH = 1.0 / 3.0
COMPOSITE_W_ANGLE = 1.0 / 3.0
COMPOSITE_W_VOLUME = 1.0 / 3.0


@dataclass
class Cell:
    """A 6-tuple lattice description (a, b, c, alpha, beta, gamma)."""

    a: float
    b: float
    c: float
    alpha: float
    beta: float
    gamma: float

    def as_tuple(self) -> tuple[float, float, float, float, float, float]:
        return (self.a, self.b, self.c, self.alpha, self.beta, self.gamma)

    def volume(self) -> float:
        a, b, c = self.a, self.b, self.c
        ca = math.cos(math.radians(self.alpha))
        cb = math.cos(math.radians(self.beta))
        cg = math.cos(math.radians(self.gamma))
        det = 1 - ca * ca - cb * cb - cg * cg + 2 * ca * cb * cg
        return a * b * c * math.sqrt(max(det, 0.0))


_PERMS = list(itertools.permutations(range(3)))


def _permute(cell: Cell, perm: tuple[int, ...]) -> Cell:
    """Apply axis permutation with consistent angle remapping."""
    lengths = [cell.a, cell.b, cell.c]
    angles = [cell.alpha, cell.beta, cell.gamma]
    perm_lengths = [lengths[i] for i in perm]
    # alpha = angle(b, c); beta = angle(a, c); gamma = angle(a, b)
    # under axis permutation perm, the new angles map as:
    #   new_alpha = angle(perm[1], perm[2])
    #   new_beta  = angle(perm[0], perm[2])
    #   new_gamma = angle(perm[0], perm[1])
    pair_to_angle = {
        frozenset((1, 2)): angles[0],
        frozenset((0, 2)): angles[1],
        frozenset((0, 1)): angles[2],
    }
    new_alpha = pair_to_angle[frozenset((perm[1], perm[2]))]
    new_beta = pair_to_angle[frozenset((perm[0], perm[2]))]
    new_gamma = pair_to_angle[frozenset((perm[0], perm[1]))]
    return Cell(
        perm_lengths[0],
        perm_lengths[1],
        perm_lengths[2],
        new_alpha,
        new_beta,
        new_gamma,
    )


def _composite_score(predicted: Cell, reference: Cell) -> float:
    pred_vec = np.array(predicted.as_tuple(), dtype=float)
    ref_vec = np.array(reference.as_tuple(), dtype=float)
    rel_len = np.mean(np.abs(pred_vec[:3] - ref_vec[:3]) / np.maximum(ref_vec[:3], 1e-9))
    rel_ang = np.mean(np.abs(pred_vec[3:] - ref_vec[3:]) / np.maximum(ref_vec[3:], 1e-9))
    rel_vol = abs(predicted.volume() - reference.volume()) / max(reference.volume(), 1e-9)
    return (
        COMPOSITE_W_LENGTH * rel_len
        + COMPOSITE_W_ANGLE * rel_ang
        + COMPOSITE_W_VOLUME * rel_vol
    )


def best_cell_match(
    candidates: Sequence[Cell],
    reference: Cell,
) -> tuple[Cell, float, tuple[int, ...], int]:
    """Pick the best (variant, permutation) pair across the 18 candidates.

    Args:
        candidates: typically [original, primitive, conventional] cells
        reference: experimental or DFT-relaxed reference cell

    Returns:
        (best_cell, score, best_perm, variant_index)
    """
    best = None
    best_score = float("inf")
    best_perm = (0, 1, 2)
    best_variant = 0
    for variant_idx, cand in enumerate(candidates):
        for perm in _PERMS:
            permuted = _permute(cand, perm)
            score = _composite_score(permuted, reference)
            if score < best_score:
                best_score = score
                best = permuted
                best_perm = perm
                best_variant = variant_idx
    assert best is not None
    return best, best_score, best_perm, best_variant
