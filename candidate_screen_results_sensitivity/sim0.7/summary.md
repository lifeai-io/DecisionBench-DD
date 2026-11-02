# DecisionBench-DD candidate screen summary

Ambroxol CNNaffinity @ 3KEH (pass/fail threshold for all candidates) = 6.205

Control neutral-minus-acidic CNNaffinity deltas (positive = favors neutral/3KEH):
  - Ambroxol: +0.029
  - Isofagomine (IFM): -0.174
  - P9V: -0.046
  - P8Y: -0.141

pH-sensitivity endpoint status: **exploratory_unvalidated**. Ambroxol's own directional sanity check passes (positive neutral-minus-acidic CNNaffinity delta), but this does not by itself validate the pH-sensitivity endpoint: only 0/3 of the other controls (isofagomine, P9V, P8Y) agree, and only 3/6 interpretable candidates favor the neutral state. Status is reported as 'exploratory_unvalidated': these score differences may inform exploratory prioritization but do not establish pH-dependent binding, lysosomal release, or pharmacological-chaperone behavior. The primary neutral-state structural-proxy endpoint is unaffected and remains the frozen primary result.

## genmol
- Chemically qualified: 0
- Structural-proxy pass: 0 (R_structural|chemical = None)
- Y_structural_proxy = 0.00% (95% exact binomial CI (0.0, 0.0122))

## molmim
- Chemically qualified: 10
- Structural-proxy pass: 2 (R_structural|chemical = 0.2)
- Y_structural_proxy = 0.67% (95% exact binomial CI (0.0008, 0.0239))
