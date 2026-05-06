"""AGAPI-XRD pipeline: Stage 1 (pattern matching) -> Stage 2 (DiffractGPT) ->
Stage 3 (ALIGNN-FF, optional) -> Stage 4 (Rietveld refinement).

All stages call a hosted REST endpoint; the URL is read from the
AGAPI_XRD_ENDPOINT environment variable so this code can be pointed at the
anonymous review mirror or a private mirror without source-level changes.
"""

from .api import analyze
from .client import Client
from .cell_match import best_cell_match

__all__ = ["analyze", "Client", "best_cell_match"]
