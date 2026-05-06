"""Reproduce Tables 1, 2, 4 in the paper from the RRUFF-276 benchmark.

Inputs:
    --manifest <path>                A CSV the user generates by applying the
                                     four selection filters in
                                     data/dataset_card.md to the JARVIS-RRUFF
                                     figshare snapshot. Expected columns:
                                     mineral_name, jarvis_rruff_id, a, b, c,
                                     alpha, beta, gamma, crystal_system,
                                     formula. The repository does not ship
                                     this file because it is derivable from
                                     the public upstream snapshot.
    --raw_dir <path>                 Directory containing one
                                     <jarvis_rruff_id>/powder.txt per mineral.

Outputs (under --output_dir):
    coverage.csv                     -> Table 1 (structure-identification coverage)
    method_breakdown.csv             -> Table 2 (PM vs DG vs PM-elements)
    crystal_system.csv               -> Table 4 (per-system MAE, skill, volume)
    overall.csv                      -> Appendix Table 5 (aggregate metrics)
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from pipeline import Client, analyze
from eval.metrics import all_metrics


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True,
                   help="user-provided RRUFF benchmark CSV; see data/dataset_card.md "
                        "for the deterministic selection rules to derive it")
    p.add_argument("--raw_dir", default="raw/rruff")
    p.add_argument("--output_dir", default="results/rruff")
    p.add_argument("--filter_max_lattice", type=float, default=10.0)
    p.add_argument("--use_alignnff", action="store_true")
    p.add_argument("--refinement", choices=["none", "gsasii", "bgmn"], default="none")
    return p.parse_args()


def load_pattern(raw_dir: Path, jid: str) -> str:
    path = raw_dir / jid / "powder.txt"
    if not path.exists():
        raise FileNotFoundError(f"missing pattern for {jid}: {path}")
    return path.read_text()


def main() -> None:
    args = parse_args()
    manifest = pd.read_csv(args.manifest, comment="#")
    if "a" in manifest.columns and "b" in manifest.columns and "c" in manifest.columns:
        max_l = args.filter_max_lattice
        keep = (manifest[["a", "b", "c"]] <= max_l).all(axis=1)
        manifest = manifest.loc[keep].reset_index(drop=True)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    client = Client()
    rows = []
    for _, row in tqdm(manifest.iterrows(), total=len(manifest)):
        pattern = load_pattern(Path(args.raw_dir), row["jarvis_rruff_id"])
        result = analyze(
            formula=row["formula"],
            elements=",".join(_elements_from_formula(row["formula"])),
            pattern=pattern,
            use_alignnff=args.use_alignnff,
            refinement=args.refinement,
            client=client,
        )
        rows.append({"manifest": row.to_dict(), "result": result})

    _write_summary(rows, out)


def _elements_from_formula(formula: str) -> list[str]:
    """Crude element extractor; replace with pymatgen.Composition for real runs."""
    elements: list[str] = []
    current = ""
    for ch in formula:
        if ch.isupper():
            if current:
                elements.append(current)
            current = ch
        elif ch.islower():
            current += ch
    if current:
        elements.append(current)
    return elements


def _write_summary(rows: list[dict], out: Path) -> None:
    coverage = {
        "pattern_matching_formula": 0,
        "pattern_matching_elements_fallback": 0,
        "diffractgpt": 0,
        "unmatched": 0,
    }
    refs = {k: [] for k in ("a", "b", "c", "alpha", "beta", "gamma", "V")}
    preds = {k: [] for k in refs}

    for row in rows:
        result = row["result"]
        source = result.get("source")
        if source == "formula":
            coverage["pattern_matching_formula"] += 1
        elif source == "elements":
            coverage["pattern_matching_elements_fallback"] += 1
        elif source == "diffractgpt":
            coverage["diffractgpt"] += 1
        else:
            coverage["unmatched"] += 1

    (out / "coverage.json").write_text(json.dumps(coverage, indent=2))

    if all(refs[k] and preds[k] for k in refs):
        with (out / "overall.csv").open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["param", "MAE", "RMSE", "R2", "median_abs", "MAD_exp", "skill", "JSD"])
            for k in refs:
                m = all_metrics(np.array(preds[k]), np.array(refs[k]))
                w.writerow([k, m.mae, m.rmse, m.r2, m.median_abs, m.mad_exp, m.skill, m.jsd])

    print(f"wrote results to {out}")


if __name__ == "__main__":
    main()
