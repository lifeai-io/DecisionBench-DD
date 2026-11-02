# DecisionBench-DD candidate screen summary

Ambroxol CNNaffinity @ 3KEH (pass/fail threshold for all candidates) = 6.206

Control neutral-minus-acidic CNNaffinity deltas (positive = favors neutral/3KEH):
  - Ambroxol: +0.057
  - Isofagomine (IFM): -0.189
  - P9V: -0.088
  - P8Y: -1.686

pH-sensitivity endpoint status: **exploratory_unvalidated**. Ambroxol's own directional sanity check passes (positive neutral-minus-acidic CNNaffinity delta), but this does not by itself validate the pH-sensitivity endpoint: only 0/3 of the other controls (isofagomine, P9V, P8Y) agree, and only 23/57 interpretable candidates favor the neutral state. Status is reported as 'exploratory_unvalidated': these score differences may inform exploratory prioritization but do not establish pH-dependent binding, lysosomal release, or pharmacological-chaperone behavior. The primary neutral-state structural-proxy endpoint is unaffected and remains the frozen primary result.

## genmol
- Chemically qualified: 66
- Structural-proxy pass: 15 (R_structural|chemical = 0.2273)
- Y_structural_proxy = 5.00% (95% exact binomial CI (0.0283, 0.0811))

## molmim
- Chemically qualified: 3
- Structural-proxy pass: 1 (R_structural|chemical = 0.3333)
- Y_structural_proxy = 0.33% (95% exact binomial CI (0.0001, 0.0184))
