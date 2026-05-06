# Dataset card: AGAPI-XRD evaluation splits

This card documents the two benchmark splits used in *AGAPI-XRD* (NeurIPS 2026 Main Track submission). Both splits are derived from public sources; this supplementary does not redistribute raw data or enumerate identifier lists. Instead, it documents the selection procedure that defines each split so a reviewer can reproduce it from the same upstream sources.

## RRUFF-276 (experimental)

- **Source.** RRUFF Project mineral powder XRD data, accessed through the JARVIS figshare RRUFF snapshot (Cu K$\alpha$, $\lambda = 1.54184$~\AA).
- **Selection rule.** Start from the 1{,}362-entry JARVIS-RRUFF snapshot; deduplicate by mineral name (yielding 803 unique minerals); drop entries with unparseable or HTML-encoded formulas; filter to minerals whose RRUFF-reported lattice parameters satisfy $a, b, c \le 10$~\AA. The final benchmark is the 276 minerals that pass all four filters.
- **Crystal-system distribution.** 217 of the 276 minerals carry a RRUFF crystal-system label; their distribution is cubic (50), orthorhombic (44), monoclinic (43), triclinic (26), hexagonal (26), tetragonal (21), rhombohedral (7).
- **Per-entry fields.** Continuous intensity profile ($\sim$8{,}501 points, $20^\circ$--$95^\circ$ at $0.02^\circ$), reference lattice parameters with uncertainties, crystal system, chemical formula. Atomic coordinates are not provided by RRUFF; the benchmark therefore tests lattice-level rather than full-structure agreement.
- **Intended use.** Evaluation only. Not for training.
- **Known biases.** Skewed toward common rock-forming elements (O, Si, Ca, Fe, Al, Na, Mg, S); skewed toward higher-symmetry crystal systems; biased away from synthetic and metastable phases.

## Alexandria-XRD (simulated)

- **Source.** Alexandria PBE-hull structures (CC-BY 4.0), filtered to the convex hull ($E_{\mathrm{hull}} = 0$~eV/atom), yielding $\sim$117{,}000 thermodynamically stable structures. Powder XRD patterns are simulated on a fixed $2\theta$ grid using the kinematic-diffraction module of the JARVIS toolkit (the same simulator used in Stage 1 of AGAPI-XRD).
- **Workflow splits.** Six end-to-end runs differing in refinement engine and ALIGNN-FF use: `none`, `none + alignnff`, `bgmn`, `bgmn + alignnff`, `gsasii`, `gsasii + alignnff`. Per-workflow row counts after the cell-matching protocol: 9{,}328 / 10{,}939 / 11{,}364 / 12{,}060 / 10{,}299 / 11{,}419 (entries processed); 8{,}857 / 10{,}445 / 10{,}805 / 11{,}545 / 9{,}770 / 10{,}989 (entries with complete reference-and-predicted lattice parameters).
- **Per-entry fields.** Alexandria entry ID, reference (DFT-relaxed) $a, b, c, \alpha, \beta, \gamma$, simulated XRD pattern (intensity vector on the fixed grid), chemical formula. Crystal-system labels are not provided by Alexandria for these entries; we therefore stratify by crystal system on RRUFF only.
- **Intended use.** Evaluation only. The same simulator is used for ground-truth XRD generation and for Stage 1 pattern matching, so the simulated benchmark cannot detect simulator-specific biases. We treat it as a coverage-and-scaling test, complementing the experimental RRUFF evaluation.
- **Known biases.** Restricted to the PBE convex hull, so excludes metastable phases of practical interest. DFT-PBE systematically overestimates lattice constants by 1--3% for many systems, which we do not attempt to correct.

## Reproducing the splits

The selection rules above are deterministic given the upstream snapshots. A reviewer can reproduce both splits by (i) fetching the JARVIS-RRUFF snapshot from figshare and applying the four filters above, and (ii) querying the Alexandria PBE-hull download mirror for entries with $E_{\mathrm{hull}} = 0$. Identifier lists are not redistributed in this supplementary.

## Licensing

| Data source         | License       |
|---------------------|---------------|
| RRUFF               | Public access |
| JARVIS-DFT          | Public domain |
| COD                 | CC0           |
| Alexandria PBE-hull | CC-BY 4.0     |
