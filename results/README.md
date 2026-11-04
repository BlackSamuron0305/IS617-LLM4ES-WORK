# results

Small summary tables and logs, built from `data/raw/` with the pipeline. Everything here is committed; the large
per-answer tables (`data/processed/`) are not.

| folder | what | built from | written by |
|---|---|---|---|
| `audited_models/` | the three audited models (Qwen3 32B, Gemma 4 31B, Mistral Small 3.2 24B): tables by country, applicant profile, savings and variant; the confirmatory tests (`analyze_*.txt`, boundary set included); the cost measures; the judge's codes by country | `data/raw/02_audited_main_run`, `03_audited_boundary_applicants`, `04_audited_prompt_variants` | `pipeline/analysis/summarize.py`, `analyze_main.py`, `costs.py` |
| `extra_models/round_1_small_and_mid/` | nine more models, first round (deviation D5): Qwen2.5 7B, Falcon3 7B, Phi-3.5 mini, OLMo 2 7B, Mistral 7B, gpt-oss-120b | `data/raw/05_extra_models/round_1_small_and_mid` | `summarize.py` |
| `extra_models/round_2_large/` | second round (deviation D7): Qwen2.5 32B and 72B, Mistral Medium 3.5 128B | `data/raw/05_extra_models/round_2_large` | `summarize.py` |
| `deep_dive/ablations_reference_family/` | the deep dive (branch `bias-deep-dive`): ablations of the nationality lines, reference nationalities, Qwen family curve, negative applicants | `data/raw/06_deep_dive/*` and the audited main run | `pipeline/deep_dive/report.py` |
| `deep_dive/negative_applicants/` | negative applicants (blocks 7 and 8) for every model | `data/raw/06_deep_dive/negative_applicants` | `report.py` |
| `deep_dive/judge_lab/` | agreement between judge versions and judge models, and the codes by nationality group | the `lab_*` files in the batch folders | `pipeline/judge/lab_report.py` |
| `deep_dive/significance_tests/` | (to come) pair tests and gap tests with five repetitions | `06_deep_dive/five_repetitions`, `conflict_nationalities` | `pipeline/deep_dive/significance_tests.py` |

Pass the folder as `--name`, for example `--name deep_dive/negative_applicants`. The figures made from these tables are in
`paper/*/figures/` and `experiment/deep_dive/figures/`.
