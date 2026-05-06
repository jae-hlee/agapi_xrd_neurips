"""Reproduce Table 3 + Figure 4 in the paper from the Alexandria PBE-hull split.

Run once per workflow:
    python eval/benchmark_alexandria.py --workflow none
    python eval/benchmark_alexandria.py --workflow none_alignnff
    python eval/benchmark_alexandria.py --workflow bgmn
    python eval/benchmark_alexandria.py --workflow bgmn_alignnff
    python eval/benchmark_alexandria.py --workflow gsasii
    python eval/benchmark_alexandria.py --workflow gsasii_alignnff
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


_WORKFLOWS = {
    "none": dict(use_alignnff=False, refinement="none"),
    "none_alignnff": dict(use_alignnff=True, refinement="none"),
    "bgmn": dict(use_alignnff=False, refinement="bgmn"),
    "bgmn_alignnff": dict(use_alignnff=True, refinement="bgmn"),
    "gsasii": dict(use_alignnff=False, refinement="gsasii"),
    "gsasii_alignnff": dict(use_alignnff=True, refinement="gsasii"),
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--workflow", required=True, choices=sorted(_WORKFLOWS))
    p.add_argument("--manifest", required=True,
                   help="user-provided Alexandria benchmark CSV with a 'workflow' "
                        "column; see data/dataset_card.md for the selection rules")
    p.add_argument("--raw_dir", default="raw/alexandria")
    p.add_argument("--output_dir", default="results/alexandria")
    p.add_argument("--hull_threshold", type=float, default=0.0)
    return p.parse_args()


def load_pattern(raw_dir: Path, alexandria_id: str) -> str:
    path = raw_dir / f"{alexandria_id}.txt"
    if not path.exists():
        raise FileNotFoundError(f"missing pattern for {alexandria_id}: {path}")
    return path.read_text()


def main() -> None:
    args = parse_args()
    cfg = _WORKFLOWS[args.workflow]
    manifest = pd.read_csv(args.manifest, comment="#")
    manifest = manifest.loc[manifest["workflow"] == args.workflow].reset_index(drop=True)

    out = Path(args.output_dir) / args.workflow
    out.mkdir(parents=True, exist_ok=True)

    client = Client()
    refs: dict[str, list[float]] = {k: [] for k in ("a", "b", "c", "alpha", "beta", "gamma")}
    preds: dict[str, list[float]] = {k: [] for k in refs}
    success = 0

    for _, row in tqdm(manifest.iterrows(), total=len(manifest)):
        pattern = load_pattern(Path(args.raw_dir), row["alexandria_id"])
        result = analyze(
            formula=row["formula"],
            elements=",".join(_elements_from_formula(row["formula"])),
            pattern=pattern,
            **cfg,
            client=client,
        )
        if result.get("status") != "success":
            continue
        success += 1
        # In a real pipeline, parse refined cell from result["final_poscar"];
        # the manifest carries reference lattice parameters in the *_ref columns.
        for k in refs:
            refs[k].append(float(row[f"{k}_ref"]))
            preds[k].append(_extract_lattice(result, k))

    coverage = success / len(manifest) if len(manifest) else 0.0
    summary = {
        "workflow": args.workflow,
        "n_entries": len(manifest),
        "n_lat": success,
        "coverage": coverage,
    }

    if success:
        with (out / "metrics.csv").open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["param", "MAE", "RMSE", "R2", "median_abs", "MAD_exp", "skill", "JSD"])
            for k in refs:
                m = all_metrics(np.array(preds[k]), np.array(refs[k]))
                w.writerow([k, m.mae, m.rmse, m.r2, m.median_abs, m.mad_exp, m.skill, m.jsd])
                if k in ("a", "b", "c"):
                    summary[f"MAE({k})"] = m.mae

    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"wrote results to {out}")


def _elements_from_formula(formula: str) -> list[str]:
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


def _extract_lattice(result: dict, key: str) -> float:
    """Best-effort extractor for refined lattice parameters from the pipeline result."""
    s4 = result.get("stages", {}).get("stage4", {})
    if isinstance(s4, dict) and key in s4:
        return float(s4[key])
    s3 = result.get("stages", {}).get("stage3", {})
    if isinstance(s3, dict) and key in s3:
        return float(s3[key])
    return float("nan")


if __name__ == "__main__":
    main()
