# CodeBERT experiments

Checkpoint microsoft/codebert-base; scrub-v1;
lr 2e-5, batch 8, 3 epochs, 512-token windows stride 256, mean-logit
aggregation; seeds 42/1337/2026. Margin-based pair discrimination: a pair
counts when the vulnerable member's logit margin exceeds the repaired one's
(strict greater-than; ties count against).

## within_source/ (completed 2026-10-04)
Leakage-sensitivity control on 171 RustXec pairs (93 lineages): permissive
C2, lineage-purged C3, 20 matched-size controls per seed (66 runs), plus a
label-injection positive control (1.000 on 171 pairs). Results in
codebert_results.txt. Rerun: python3 analyze_v2.py manifest.json predictions/

## transfer/ (completed 2026-10-14)
RX/HR/NU/ID conditions evaluated on 21 frozen RustMizan function-level pairs
(15 advisory entities). AR/MC await the two-reviewer audit; Delta_rec not
computable. Results in transfer_results.txt.
Rebuild manifest: python3 build_transfer_manifest.py <advisory-db> <CVE_Samples> transfer_manifest.json
(pins: advisory-db f23b7682, CVE_Samples b97396b4)
Analyze: python3 analyze_transfer.py transfer_manifest.json predictions/