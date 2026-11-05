# Repository map

Where everything is. The tree shows folders; each folder has a README unless it only holds data.

```
.
├── README.md, ETHICS.md, CLAUDE.md, AGENTS.md
│
├── experiment/                       WHAT is run (the design). Start with experiment/README.md
│   ├── inputs/
│   │   ├── policy/                   the guidance given to the model (paraphrase and word-for-word Article 32) and the nationality rules
│   │   ├── applicants/               30 + 10 + 12 simulated applicants: full records, the filter, what the model sees, templates
│   │   ├── countries/                nationality sets (main 26, reference, conflict) and the official rules per nationality
│   │   └── costs/                    prices and rates behind the cost measures
│   ├── prompts/
│   │   ├── main_prompts/             base.txt and the main prompts of the variants (roles, time framing, fairness position)
│   │   ├── task_wordings/            three wordings per task form (base, reasoning, risk_scale, ...)
│   │   └── variants.csv              every variant: which files, which application change, which nationality set, repetitions
│   ├── config/                       models.csv (pinned revisions), run_settings.csv (sampling settings)
│   ├── planning/                     analysis_plan.md, design_review.md, deviations.md (D1 to D7)
│   ├── judge/                        the judge of the free-text reasons
│   │   ├── lab/                      other judge versions (v1, v1_unmasked, v2, v3)
│   │   └── validation/               the 200-item sample the team codes by hand
│   └── deep_dive/                    exploratory work (branch bias-deep-dive): README, RESULTS, figures/
│
├── pipeline/                         the code (standard library only); commands in pipeline/README.md
│   ├── core/                         common (paths, tables, batch locations), client, calls
│   ├── design/                       filter_applicants, build_runs
│   ├── answers/                      run_models, parse_answers, merge_batches, pilot_report
│   ├── judge/                        build, run, parse, validate, lab, lab_report
│   ├── analysis/                     summarize, analyze_main, costs, make_figures
│   └── deep_dive/                    report, figures, significance_tests
├── tests/                            mirrors pipeline/: core/, design/, answers/, judge/, analysis/
├── cluster/                          Slurm scripts (run_vllm.sbatch, submit_chain.sh, download_model.sbatch), PILOT.md
│
├── data/
│   ├── raw/                          model answers exactly as returned (committed as .jsonl.gz)
│   │   ├── 00_smoke_tests/<model>/<batch>/
│   │   ├── 01_pilots/<batch>/
│   │   ├── 02_audited_main_run/<model>/<batch>/              blocks 1 to 3
│   │   ├── 03_audited_boundary_applicants/<model>/<batch>/   blocks 5 and 6
│   │   ├── 04_audited_prompt_variants/<model>/<batch>/       block 4
│   │   ├── 05_extra_models/{round_1_small_and_mid,round_2_large}/<model>/<batch>/
│   │   ├── 06_deep_dive/{qwen_family,negative_applicants,new_prompt_variants,five_repetitions,conflict_nationalities}/<model>/<batch>/
│   │   └── 07_thinking_and_temperature/{thinking_on,temperature}/<model>/<batch>/
│   └── processed/                    the same folders as tables (not committed; rebuilt from raw)
│
├── results/                          summary tables, one folder per run (results/README.md)
│   ├── audited_models/
│   ├── extra_models/{round_1_small_and_mid,round_2_large}/
│   └── deep_dive/{ablations_reference_family,negative_applicants,judge_lab,significance_tests,thinking_and_temperature}/
│
├── paper/                            course deliverables, each with its own README
│   ├── proposal/   first_presentation/   second_presentation/   final_presentation/   final_paper/
│
├── research/
│   ├── literature/                   review, matrix, references.bib, notes per strand (lit_parts/)
│   ├── visa_scenario/                the research behind the visa design (and parked_comparison_set/)
│   ├── scenario_reviews/             the notes that led from hiring to banking
│   └── old_design/                   hiring and bank designs: background only
└── docs/                             this map and the implementation plans
```

A batch is one named group of calls to one model, for example `dd_rep_qwen3-32b_s1` (`dd_rep`: the run, `qwen3-32b`: the model,
`_s1`: shard 1 of several). The prefix decides the run folder (`pipeline/core/common.py`, `BATCH_GROUPS`).
