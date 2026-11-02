# Patent-literature and purchasable-catalog membership: 16 primary candidates

Exact-structure membership only (molbloom/SureChEMBL Bloom filter, FPR 0.000025), NOT a similarity-based patent-proximity search, freedom-to-operate opinion, or claim-scope analysis. Sanity-checked against Ambroxol (a marketed patented drug), which correctly returns True.

SureChEMBL filter provenance: /home/user/DecisionBench-DD/.cache/molbloom/surechembl.bloom (SHA-256: fba90fba019230c857260adc691783f36020ab474383a8dccdd898f650e99786). This is a downloaded, externally-hosted artifact, not re-derivable from source; record this hash to know if a later run used a different filter version.

Ambroxol control: in_surechembl=True (sanity check passed).
Of the 16 primary candidates: 0/16 found in SureChEMBL (exact-structure patent-literature hit), 1/16 found in ZINC in-stock (known purchasable compound).
15/16 candidates are in NEITHER database: GM_007, GM_015, GM_024, GM_032, GM_033, GM_034, GM_035, GM_039, GM_047, GM_053, GM_054, GM_055, GM_057, GM_064, MM_002. Per external review, this must be read narrowly as: **no exact-structure membership detected in the tested SureChEMBL Bloom-filter snapshot (or ZINC in-stock)**. A Bloom filter is a membership mechanism, not a similarity, Markush-claim, tautomer/salt, or freedom-to-operate search; canonicalization choices and database coverage gaps can still cause relevant prior art to be missed. This is NOT a novelty or patentability claim.

GM_031 (ZINC in-stock hit) being purchasable is operationally useful for rapid assay procurement, but that also specifically warrants a direct compound-identity and prior-art check before treating it as available for unencumbered use.

| Candidate | In SureChEMBL (patent lit.) | In ZINC in-stock (purchasable) |
| --- | :---: | :---: |
| CTRL_AMBROXOL | True | True |
| GM_007 | False | False |
| GM_015 | False | False |
| GM_024 | False | False |
| GM_031 | False | True |
| GM_032 | False | False |
| GM_033 | False | False |
| GM_034 | False | False |
| GM_035 | False | False |
| GM_039 | False | False |
| GM_047 | False | False |
| GM_053 | False | False |
| GM_054 | False | False |
| GM_055 | False | False |
| GM_057 | False | False |
| GM_064 | False | False |
| MM_002 | False | False |
