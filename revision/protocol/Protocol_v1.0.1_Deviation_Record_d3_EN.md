# Experiment protocol v1.0.1: deviation record d3 (analysis and reporting)

English translation of `Deney_Protokolu_v1.0.1_Sapma_Kaydi_d3.md`. If the two differ, the Turkish record is authoritative.

**Related documents:**
- `Deney_Protokolu_v1.0.1.md` (SHA-256 `4dc90062…4ab8`)
- `Deney_Protokolu_v1.0.1_Ek_E5b.md` (SHA-256 `620fdc22…e55b`)

Neither document was **changed**; their historical versions are kept as they are. This record documents deviations and additions made in the analysis and reporting layer after the experiments were completed. The run matrix, the runs, the algorithm code and the prespecified test families did not change.

**First recorded:** 2026-11-12 (internal project document).  
**Published in the repository:** 2026-11-14.  
All decisions in this record were made after the E1–E5b results were seen; the publication date does not indicate otherwise.

| Code | Protocol reference | Deviation or addition | Reason | Information state | Affected results |
|---|---|---|---|---|---|
| d3-1 | §6.5, last item: "The Brown–Forsythe test is reported as supplementary information only. It is stated that the test treats paired data as independent." | The supplementary Brown–Forsythe analysis was not performed. The prespecified paired instance-level SD comparisons (6 tests, Holm) were retained. No other analysis was added in its place. | The protocol foresaw this test only as supplementary information and already stated that it ignores the paired structure. The confirmatory answer to the variability question is the prespecified SD-difference tests. Brown–Forsythe had not been implemented in the analysis-v3 scripts; this was noticed while revising the manuscript. | The decision was recorded after the E1–E5b results were seen. No confirmatory result depends on it. | The prespecified numerical comparisons did not change. Brown–Forsythe statements and the `levene1960` citation are removed from the manuscript. |
| d3-2 | Not in the protocol | **Post-hoc geometric audit:** full-coverage attainability of the S2 instances (13 environments) was witnessed with a matching construction (`revision/analysis_v4/s2_full_coverage_witness.py`, with witness coordinates). In S1 and S3, N ≥ M, so full coverage holds in general. | During the manuscript revision it was noticed that the optimum of the studied instances is known. | After the results were seen. | The prespecified numerical comparisons did not change; the interpretive scope and limitations of the findings were updated. Because the optimum is known and attainable with a simple geometric construction, the practical contribution claimed in the manuscript was narrowed. The audit is reported separately from the confirmatory family, as a post-hoc check. |
| d3-3 | §5.1 (primary outcome: number of covered targets) | **Reporting transformation:** the gap to the optimum, Gap = M − K, is derived from the same runs and reported (analysis-v4). Mean Gap = M − mean K. | Eases interpretation given the known optimum (d3-2). | After the results were seen. | The prespecified numerical comparisons did not change. Gap is not a new success measure or test family; it expresses K in the opposite direction and lets results be read against the optimum. |
| d3-4 | §4, "Known dependence": S1 and S2 share the same target layout (K9) | **Additional observation:** for the same seed, the first 75 targets of S3 also coincide with the S1/S2 targets. Verified for all 13 seeds. | Targets are drawn first from the same random-number stream. | Noticed during the revision. | The prespecified numerical comparisons did not change; the interpretive scope and limitations were updated. Analyses treat scenarios separately; no independence or independent replication across scenarios is claimed. |
