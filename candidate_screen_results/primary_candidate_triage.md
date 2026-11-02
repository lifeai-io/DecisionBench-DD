# ADMET-adjacent and scaffold-diversity triage: 16 primary candidate-screen passers

Scope: physicochemical drug-likeness (QED/SA/MW/cLogP/TPSA/HBD/HBA, all already computed in Experiment A) and structural diversity (Murcko scaffold, ECFP4 clustering at the protocol's frozen 0.60 Tanimoto cutoff), plus a docking-derived ligand-efficiency PROXY (CNNaffinity / heavy-atom count -- not a validated LE metric, since CNNaffinity is a learned score, not experimental pKd/pKi).

Predictive ADMET (hERG/AMES/DILI/BBB/CYP450/clearance/etc., via ADMET-AI) and an exact-structure patent-literature/purchasable-catalog membership check (via molbloom/SureChEMBL) are separate deliverables: see admet_predictions.md and patent_membership.md. The latter is explicitly NOT a similarity-based patent-proximity search or a freedom-to-operate opinion -- see that file's own scope note.

All 16 candidates advance (protocol section 11: 'If 20 or fewer candidates pass, advance all.'). They span 8 ECFP4 clusters (0.60 Tanimoto cutoff) and 10 distinct Murcko scaffolds -- see primary_candidate_triage.csv for the full per-candidate table, ranked by CNNaffinity desc / CNNscore desc / minimizedAffinity asc / candidate ID (protocol section 11's ranking rule).

| Rank | Candidate | Tool | CNNaffinity | LE proxy | QED | SA | MW | cLogP | Ro5 violations | Scaffold cluster |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | GM_015 | genmol | 7.370 | 0.283 | 0.6242 | 3.7223 | 485.22 | 4.124 | 0 | 0 |
| 2 | GM_054 | genmol | 7.060 | 0.272 | 0.5532 | 3.876 | 490.28 | 3.243 | 0 | 5 |
| 3 | GM_035 | genmol | 7.017 | 0.351 | 0.671 | 3.666 | 408.13 | 2.812 | 0 | 3 |
| 4 | MM_002 | molmim | 6.924 | 0.364 | 0.7581 | 3.1752 | 409.19 | 4.355 | 0 | 7 |
| 5 | GM_064 | genmol | 6.823 | 0.284 | 0.5837 | 2.9659 | 454.21 | 4.776 | 0 | 6 |
| 6 | GM_007 | genmol | 6.727 | 0.306 | 0.694 | 3.6745 | 436.19 | 3.544 | 0 | 0 |
| 7 | GM_033 | genmol | 6.688 | 0.319 | 0.7144 | 3.668 | 422.16 | 3.466 | 0 | 3 |
| 8 | GM_034 | genmol | 6.583 | 0.346 | 0.6914 | 3.5906 | 392.14 | 3.433 | 0 | 4 |
| 9 | GM_057 | genmol | 6.571 | 0.299 | 0.5331 | 3.7012 | 436.14 | 2.888 | 0 | 3 |
| 10 | GM_047 | genmol | 6.514 | 0.326 | 0.601 | 4.4984 | 404.1 | 2.978 | 0 | 2 |
| 11 | GM_031 | genmol | 6.503 | 0.342 | 0.778 | 4.6823 | 390.12 | 3.451 | 0 | 2 |
| 12 | GM_055 | genmol | 6.491 | 0.250 | 0.549 | 3.5789 | 487.21 | 4.35 | 0 | 5 |
| 13 | GM_024 | genmol | 6.445 | 0.230 | 0.5645 | 3.4403 | 517.31 | 4.912 | 1 | 1 |
| 14 | GM_053 | genmol | 6.424 | 0.306 | 0.5599 | 3.6623 | 422.12 | 2.498 | 0 | 3 |
| 15 | GM_039 | genmol | 6.261 | 0.298 | 0.6443 | 3.7344 | 420.19 | 4.069 | 0 | 3 |
| 16 | GM_032 | genmol | 6.251 | 0.313 | 0.758 | 4.7642 | 406.12 | 3.177 | 0 | 2 |
