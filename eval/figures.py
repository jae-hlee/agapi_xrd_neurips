"""Generate Figures 2 (composition), 3 (distributions), 4 (refinement MAE bars).

Reads the per-workflow CSVs written by benchmark_rruff.py and benchmark_alexandria.py
and writes figures/<name>.png to disk.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--results_root", default="results")
    p.add_argument("--output_dir", default="results/figures")
    return p.parse_args()


def figure_refinement_mae(results_root: Path, output_dir: Path) -> None:
    """Figure 4: lattice MAE bars across 12 RRUFF + Alexandria workflows."""
    workflows = ["none", "none_alignnff", "bgmn", "bgmn_alignnff", "gsasii", "gsasii_alignnff"]
    benchmarks = ["rruff", "alexandria"]
    rows = []
    for bench in benchmarks:
        for wf in workflows:
            path = results_root / bench / wf / "metrics.csv"
            if not path.exists():
                continue
            df = pd.read_csv(path)
            for _, r in df.iterrows():
                rows.append({"benchmark": bench, "workflow": wf, "param": r["param"], "mae": r["MAE"]})

    if not rows:
        print("no metrics CSVs found; skipping Figure 4")
        return

    df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(11, 4))
    pivot = df.pivot_table(index=["benchmark", "workflow"], columns="param", values="mae")
    pivot.plot(kind="bar", ax=ax)
    ax.set_ylabel("MAE")
    ax.set_title("Lattice MAE across 12 RRUFF and Alexandria workflows")
    plt.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "refinement_mae.png", dpi=200)
    plt.close(fig)


def figure_coverage(results_root: Path, output_dir: Path) -> None:
    """Figure 2(b)-style summary of pattern-matching coverage on RRUFF."""
    coverage_path = results_root / "rruff" / "coverage.json"
    if not coverage_path.exists():
        print("no RRUFF coverage.json; skipping coverage figure")
        return
    coverage = json.loads(coverage_path.read_text())

    labels = list(coverage.keys())
    counts = [coverage[k] for k in labels]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(counts, labels=labels, autopct="%1.1f%%")
    ax.set_title("RRUFF structure-identification coverage")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "coverage_pie.png", dpi=200)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    results_root = Path(args.results_root)
    output_dir = Path(args.output_dir)
    figure_refinement_mae(results_root, output_dir)
    figure_coverage(results_root, output_dir)
    print(f"wrote figures to {output_dir}")


if __name__ == "__main__":
    main()
