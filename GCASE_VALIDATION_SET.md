The next milestone can now be frozen as **“Assemble GCase structural validation set — COMPLETE.”** I recommend using **14 non-covalent human GCase co-crystal structures** rather than the minimum 8. This gives enough cases for GNINA vs DiffDock while adding binding-site and chemotype diversity.

## Frozen GCase redocking set v1.0

| PDB      | Resolution | Ligand class / role                   | Site stratum | Include |
| -------- | ---------: | ------------------------------------- | ------------ | ------- |
| **9F9Z** |     2.28 Å | fragment/allosteric modulator         | Allosteric   | ✅       |
| **9FA3** |     1.36 Å | fragment/allosteric modulator         | Allosteric   | ✅       |
| **9FA6** |     1.49 Å | fragment/allosteric modulator         | Allosteric   | ✅       |
| **9FAD** |     1.80 Å | fragment/allosteric modulator         | Allosteric   | ✅       |
| **9FAL** |     1.39 Å | fragment/allosteric modulator         | Allosteric   | ✅       |
| **9FAY** |     1.40 Å | fragment/allosteric modulator         | Allosteric   | ✅       |
| **9FAZ** |     1.63 Å | fragment/allosteric modulator         | Allosteric   | ✅       |
| **9FB2** |     1.14 Å | fragment/allosteric modulator         | Allosteric   | ✅       |
| **9FDI** |     1.41 Å | fragment/allosteric modulator         | Allosteric   | ✅       |
| **8P3E** |     1.75 Å | positive allosteric activator         | Allosteric   | ✅       |
| **8P41** |     1.83 Å | positive allosteric activator         | Allosteric   | ✅       |
| **3GXF** |     2.40 Å | isofagomine pharmacological chaperone | Active site  | ✅       |
| **6Q1N** |     2.53 Å | IMX8 pharmacological chaperone        | Active site  | ✅       |
| **6Q1P** |     2.80 Å | norIMX8 pharmacological chaperone     | Active site  | ✅       |

The nine `9F*` structures all come from the same 2024 fragment-based GCase campaign. The authors identified crystallographic fragments and developed compounds with nanomolar GCase binding and positive cellular modulation; RCSB lists all nine structures as related deposits from that work. ([ACS Publications][1])

The series is particularly useful because it is **human wild-type GCase**, X-ray determined, and exceptionally high resolution—down to 1.14 Å for 9FB2. ([RCSB PDB][2])

### Why I would not use only those nine

If we benchmark only the Astex series, we risk testing:

> “Can the docking method reproduce one particular GCase allosteric pocket?”

rather than:

> “Can the method reproduce experimentally observed GCase–ligand poses?”

So the validation set deliberately adds other chemical series and an active-site stratum.

`8P3E` and `8P41` contain two distinct chemotypes of experimentally characterized positive allosteric GCase modulators, at 1.75 and 1.83 Å respectively. ([RCSB PDB][3])

`3GXF` is particularly valuable because it contains **isofagomine**, a pharmacological chaperone bound at the GCase active site; RCSB reports 2.40 Å resolution and BindingDB Ki annotations of roughly 5–23 nM. ([RCSB PDB][4])

`6Q1N` and `6Q1P` add the pH-switching pharmacological-chaperone series IMX8/norIMX8. RCSB identifies them as human GCase complexes at 2.53 and 2.80 Å respectively. ([RCSB PDB][5])

This gives:

```text
14 total redocking cases

11 allosteric
3 active-site / pharmacological-chaperone

Resolution range:
1.14–2.80 Å
```

## Frozen inclusion criteria

Before docking, each case must satisfy all of these:

1. **Human GCase/GBA1**.
2. Experimentally determined by **X-ray crystallography**.
3. Resolution **≤3.0 Å**.
4. Explicit small-molecule ligand of interest.
5. Non-covalent binding.
6. Ligand coordinates present.
7. Protein residues surrounding the ligand sufficiently resolved.
8. Ligand is not simply solvent, ion, buffer, glycan or crystallization additive.
9. Structure retained regardless of whether GNINA or DiffDock later performs badly.

RCSB explicitly distinguishes functional ligands/ligands-of-interest from salts, solvents and other small molecules; this is useful for making the ligand-selection rule reproducible. ([RCSB PDB][6])

## Important rule for structures with multiple ligand instances

Do **not** manually choose the easiest-looking ligand pose.

For each PDB, use exactly one primary redocking case.

If the PDB contains multiple copies of the same LOI:

> choose the ligand instance with the best experimental ligand-quality evidence.

Frozen hierarchy:

```text
Highest RSCC
   ↓ tie
Lowest RSR
   ↓ tie
Highest occupancy
   ↓ tie
Lowest ligand B-factor
   ↓ tie
lowest chain/instance identifier
```

This choice is made **before GNINA/DiffDock are run**.

RCSB ligand validation provides experimental-fit metrics such as RSCC and RSR specifically for selecting reliable ligand instances. ([RCSB PDB][7])

For a structure such as **9FA6**, which contains more than one RCSB-designated ligand of interest, only one ligand instance will contribute to the primary 14-case statistic; additional LOIs can be reported as supplementary redocking cases. ([RCSB PDB][8])

## Explicit exclusions

I would freeze these exclusions now.

**9ELB — exclude.** It is explicitly a **covalent inhibitor** complex. Standard GNINA/DiffDock redocking is not an appropriate apples-to-apples test for covalent binding. ([RCSB PDB][9])

**5LVX — exclude.** Its quinazoline modulator is covalently attached to Lys346, so it belongs in a separate covalent-docking benchmark. ([RCSB PDB][10])

**3KE0 / 3KEH — exclude from redocking.** These N370S structures are biologically important for the Ambroxol project, but their listed small molecules are glycans, sulfate, glycerol, etc.; they do not provide an appropriate drug-like experimental ligand pose for this benchmark. ([RCSB PDB][11])

**3GXI — exclude from redocking.** It is an apo GCase structure at acidic pH; use it later for receptor-state experiments, not pose-recovery validation. The ligand-bound neutral-pH counterpart is **3GXF**. ([RCSB PDB][12])

That distinction is useful later because 3KE0/3KEH/3GXI can become the **receptor-state robustness experiment**, rather than contaminating the pose-recovery benchmark.

---

# Frozen evaluation design

The experiment should now be:

```text
14 experimental GCase complexes
              ↓
      extract crystal ligand
              ↓
         remove ligand
              ↓
   identical receptor preparation
         ↙             ↘
      GNINA          DiffDock-L
         ↓              ↓
     Top 1–5 poses   Top 1–5 poses
         ↘              ↙
        symmetry-aware RMSD
                 ↓
             RESULTS
```

### Primary endpoint

Still unchanged from the frozen benchmark:

[
Success@1_{2Å}
==============

\frac{#{RMSD_{top1}\le2.0Å}}
{14}
]

### Secondary endpoints

Report:

* Success@5 at 2 Å;
* median Top-1 RMSD;
* best-of-5 RMSD;
* failure rate;
* structurally invalid pose rate;
* observed API/runtime per complex.

I would add one important **pre-specified stratified analysis**:

| Stratum               |      N | Report               |
| --------------------- | -----: | -------------------- |
| Allosteric            |     11 | Success@1, Success@5 |
| Active-site chaperone |      3 | Success@1, Success@5 |
| Overall               | **14** | primary result       |

Do **not** use the three-case active-site result to make strong statistical claims. Its purpose is to check whether the conclusion is obviously site-dependent.

---

# One methodological issue for DiffDock

For the primary comparison, both tools need to solve the same task.

Therefore DiffDock must **not be told the crystal ligand coordinates or pocket center derived from those coordinates** if GNINA is being asked to perform blind docking—or vice versa.

We should actually define two possible tasks:

```text
A. Pocket-conditioned redocking
   known experimental binding site

B. Blind docking
   whole protein
```

For this paper, I recommend **A: pocket-conditioned redocking**.

Why?

Our question is primarily:

> Once a drug-discovery workflow has selected a target pocket, which pose-generation method more reliably recovers the ligand pose?

It is more controlled, less confounded by pocket-finding ability, and feasible on 14 structures.

The experimental ligand can be used **only to define the evaluation pocket before it is removed**, not as pose information supplied to the model.

For GNINA:

```text
box center =
centroid of crystal ligand

box size =
crystal ligand extent + fixed padding
```

Freeze one padding value, e.g. **6 Å on each side**.

For DiffDock, if the implementation being evaluated is blind by design, we should not artificially give it ligand coordinates. In that case, we need to label the comparison as:

> GNINA pocket-conditioned vs DiffDock blind

which mixes tasks.

So the **next action item should explicitly settle the docking task/configuration before running anything**.

---

## Structural-set status

**Assemble GCase structural validation set — ✅ COMPLETE / FROZEN**

```text
Primary set: 14 PDB structures

9F9Z
9FA3
9FA6
9FAD
9FAL
9FAY
9FAZ
9FB2
9FDI
8P3E
8P41
3GXF
6Q1N
6Q1P
```

No structure can be dropped later because one model fails on it. A structure can only be removed for a **predefined technical exclusion** discovered during preparation—e.g. missing LOI coordinates or unusable experimental ligand density—and such a removal must be logged before any docking result is inspected.

The next timeline item should therefore be **“Prepare proteins/ligands + freeze GNINA/DiffDock redocking protocol.”** That is where I would define the exact receptor cleanup, protonation, glycan/water handling, ligand preparation, docking box, number of poses, DiffDock settings, and symmetry-aware RMSD calculation before the first docking run.

[1]: https://pubs.acs.org/doi/10.1021/acs.jmedchem.4c00702?utm_source=chatgpt.com "Fragment-Based Discovery of a Series of Allosteric-Binding Site Modulators of β‑Glucocerebrosidase | Journal of Medicinal Chemistry | ACS Publications"
[2]: https://www.rcsb.org/structure/9FB2?utm_source=chatgpt.com "RCSB PDB - 9FB2: Gcase in complex with small molecule inhibitor 1"
[3]: https://www.rcsb.org/structure/8P3E?utm_source=chatgpt.com "RCSB PDB - 8P3E: Crystal structure of glucocerebrosidase in complex with allosteric activator"
[4]: https://www.rcsb.org/structure/3GXF?utm_source=chatgpt.com "RCSB PDB - 3GXF: Crystal structure of acid-beta-glucosidase with isofagomine at neutral pH"
[5]: https://www.rcsb.org/structure/6Q1N?utm_source=chatgpt.com "RCSB PDB - 6Q1N: Glucocerebrosidase in complex with pharmacological chaperone IMX8"
[6]: https://www.rcsb.org/docs/exploring-a-3d-structure/structure-summary-page?utm_source=chatgpt.com "Structure Summary Page"
[7]: https://rcsb.org/docs/general-help/ligand-structure-quality-in-pdb-structures?utm_source=chatgpt.com "Ligand Structure Quality in PDB Structures"
[8]: https://www.rcsb.org/structure/9FA6?utm_source=chatgpt.com "RCSB PDB - 9FA6: Gcase in complex with small molecule inhibitor 1"
[9]: https://www.rcsb.org/structure/9ELB?utm_source=chatgpt.com "RCSB PDB - 9ELB: Structure of glucocerebrosidase in complex with a covalent inhibitor"
[10]: https://www.rcsb.org/structure/5LVX?utm_source=chatgpt.com "RCSB PDB - 5LVX: Crystal structure of glucocerebrosidase with an inhibitory quinazoline modulator"
[11]: https://rcsb.org/structure/3KE0?utm_source=chatgpt.com "RCSB PDB - 3KE0: Crystal structure of N370S Glucocerebrosidase at acidic pH."
[12]: https://www.rcsb.org/structure/3GXI?utm_source=chatgpt.com "RCSB PDB - 3GXI: Crystal structure of acid-beta-glucosidase at pH 5.5"
