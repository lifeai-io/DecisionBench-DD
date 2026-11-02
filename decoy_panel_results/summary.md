# DecisionBench-DD candidate screen summary

Ambroxol CNNaffinity @ 3KEH (pass/fail threshold for all candidates) = 6.205

Control neutral-minus-acidic CNNaffinity deltas (positive = favors neutral/3KEH):
  - Ambroxol: +0.029
  - Isofagomine (IFM): -0.174
  - P9V: -0.046
  - P8Y: -0.141

pH-sensitivity endpoint status: **exploratory_unvalidated**. Ambroxol's own directional sanity check passes (positive neutral-minus-acidic CNNaffinity delta), but this does not by itself validate the pH-sensitivity endpoint: only 0/3 of the other controls (isofagomine, P9V, P8Y) agree, and only 102/272 interpretable candidates favor the neutral state. Status is reported as 'exploratory_unvalidated': these score differences may inform exploratory prioritization but do not establish pH-dependent binding, lysosomal release, or pharmacological-chaperone behavior. The primary neutral-state structural-proxy endpoint is unaffected and remains the frozen primary result.

## genmol
- Chemically qualified: 66
- Structural-proxy pass: 23 (R_structural|chemical = 0.3485)
- Y_structural_proxy = 7.67% (95% exact binomial CI (0.0492, 0.1128))

## molmim
- Chemically qualified: 3
- Structural-proxy pass: 1 (R_structural|chemical = 0.3333)
- Y_structural_proxy = 0.33% (95% exact binomial CI (0.0001, 0.0184))
