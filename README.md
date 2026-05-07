# AGAPI-XRD

Anonymized companion code for the NeurIPS 2026 Main Track submission *AGAPI-XRD: A Hybrid Generative-Pattern-Matching-Rietveld Pipeline and Benchmark for Automated X-ray Diffraction Analysis*.

> **Anonymity.** Author names, affiliations, internal hostnames, and the public deployment URL have been stripped from this snapshot. The endpoint URL is configured via the `AGAPI_XRD_ENDPOINT` environment variable so reviewers can point at the anonymous web demo (URL listed in `WEB_DEMO_URL.txt`) or a local mirror.

## What this repo contains

The end-to-end XRD-to-structure pipeline benchmarked in the paper:

1. **Stage 1**: cosine-similarity pattern matching against JARVIS-DFT (~76,000 entries) and COD (~400,000 entries).
2. **Stage 2**: generative structure prediction via DiffractGPT (Mistral-7B fine-tune from prior work).
3. **Stage 3**: optional ALIGNN-FF structural relaxation.
4. **Stage 4**: automated Rietveld refinement (GSAS-II or BGMN) with sequential parameter release.

Plus the cell-matching protocol, evaluation metrics, and the scripts that reproduce Tables 1, 2, 3, 4 and Figures 2, 3, 4 in the paper.

## Layout

```
agapi_xrd_neurips/
├── README.md                          # this file
├── LICENSE                            # MIT (copyright holder redacted)
├── requirements.txt                   # pinned Python dependencies
├── WEB_DEMO_URL.txt                   # anonymous web demo URL (placeholder)
├── pipeline/
│   ├── client.py                      # REST client; reads endpoint from env
│   ├── stage1_pattern_match.py        # JARVIS-DFT + COD cosine-similarity search
│   ├── stage2_diffractgpt.py          # DiffractGPT inference wrapper
│   ├── stage3_alignnff.py             # ALIGNN-FF relaxation wrapper
│   ├── stage4_refinement.py           # GSAS-II / BGMN Rietveld driver
│   ├── cell_match.py                  # 18-candidate cell-matching protocol
│   └── api.py                         # unified end-to-end driver
├── eval/
│   ├── metrics.py                     # MAE, RMSE, R^2, skill, JSD with Laplace smoothing
│   ├── benchmark_rruff.py             # reproduces Tables 1, 2, 4
│   ├── benchmark_alexandria.py        # reproduces Table 3 + Figure 4
│   └── figures.py                     # Figures 2 (composition), 3 (distributions)
└── data/
    └── dataset_card.md                # datasheet for the RRUFF-276 and Alexandria-XRD splits, including the deterministic selection rules a reviewer can re-apply to the upstream JARVIS-RRUFF figshare snapshot and the Alexandria PBE-hull download mirror
```

## Quick start

```bash
# 1. Set the anonymous endpoint URL (see WEB_DEMO_URL.txt)
export AGAPI_XRD_ENDPOINT="https://<anonymous-mirror>.example/api"
export AGAPI_XRD_KEY="<your-key-if-required>"

# 2. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Fetch the public benchmark data yourself, applying the selection rules in
#    data/dataset_card.md to the JARVIS-RRUFF figshare snapshot (276 minerals
#    after the four filters) and to the Alexandria PBE-hull download mirror
#    (entries with E_hull = 0).

# 4. Reproduce the headline numbers
python eval/benchmark_rruff.py --output_dir results/rruff
for wf in none none_alignnff bgmn bgmn_alignnff gsasii gsasii_alignnff; do
    python eval/benchmark_alexandria.py --workflow $wf --output_dir results/alexandria/$wf
done
python eval/figures.py --results_root results
```

Wall-clock budget on the reference hardware (16-core Xeon + 1x A100-40GB):

- RRUFF benchmark: ~2 CPU-hours + ~30 GPU-minutes
- Each Alexandria workflow: ~50-120 CPU-hours + ~8-12 GPU-hours
- Total Alexandria across 6 workflows: ~500 CPU-hours + ~60 GPU-hours

## Reproduction sanity check

After running the full benchmark you should see (within run-to-run noise):

- **RRUFF**: 96.7% combined coverage; 84.1% pattern-matching coverage; 83-85% DiffractGPT coverage; lattice MAE 0.73-0.81 Å (pattern matching), 1.72-2.19 Å (DiffractGPT); skill scores +0.51 to +0.55 for pattern-matched structures.
- **Alexandria** (6 workflows): 94.9-96.2% combined coverage; lattice MAE 0.72-0.77 Å for a, b and 1.22-1.28 Å for c; cross-workflow ranges 0.024 / 0.040 / 0.062 Å for a / b / c.

## How the anonymity works

The pipeline calls a hosted REST endpoint (Stage 1 cosine matching, Stage 2 DiffractGPT, Stage 3 ALIGNN-FF, Stage 4 Rietveld refinement). The endpoint URL is configured exclusively via the `AGAPI_XRD_ENDPOINT` environment variable, never hard-coded; `WEB_DEMO_URL.txt` carries the anonymous mirror to use during review.

The recommended reviewer workflow is to access the live demo through `https://anonymous.4open.science/r/<this-repo>/` so the GitHub username is masked at the URL level.

## Reused third-party assets

| Asset            | Use                              | License                |
|------------------|----------------------------------|------------------------|
| RRUFF            | Experimental benchmark           | Public access          |
| JARVIS-DFT       | Stage 1 database, simulated XRD  | Public domain          |
| COD              | Stage 1 database                 | CC0                    |
| Alexandria       | Simulated XRD benchmark          | CC-BY 4.0              |
| GSAS-II          | Stage 4 Rietveld engine          | BSD                    |
| BGMN             | Stage 4 Rietveld engine          | Free for academic use  |
| ALIGNN, ALIGNN-FF| Property prediction, relaxation  | MIT                    |
| DiffractGPT      | Stage 2 generative model         | Public weights         |
| Mistral-7B       | DiffractGPT backbone             | Apache 2.0             |

## License

MIT (anonymized). The camera-ready release will restore the copyright holder.

## Contact

Anonymous for review. Camera-ready will list authors and a maintenance contact.
