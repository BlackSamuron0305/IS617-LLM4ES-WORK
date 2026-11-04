# Validation sample for the judge

`validation_sample_to_code.csv`: 200 items (67 Qwen3, 67 Mistral, 66 Gemma 4), drawn by `pipeline/judge_validate sample`
(seed 617, half of them with a masked nationality term) from the block 1 judge inputs of the main run, on 2026-11-02.
Each row has the masked reason and the masked application, **not** the judge's codes.

**What the team does.** Two people code each item blind, 0 or 1, in the six columns `mentions_nationality` to
`names_legal_ground` (the definitions are in `../judge_prompt.txt` and `../README.md`), put their name in `coder`, and save the
file under another name. `python -m pipeline.judge.validate agreement --batch main_<model> --human FILE --judge olmo-3.1-32b-instruct`
then gives Cohen's kappa per code. A code is used in the report only if kappa is at least 0.7 (the threshold is provisional until the
team confirms it). Until then every judge figure is exploratory.

Note: the sample was drawn from items in which almost every reason has no mention of the nationality, so the codes
`mentions_nationality`, `nationality_as_risk`, `passport_country_conditions` and `contradicts_application` have very few
positives; kappa for them may be undefined or unstable. Report that rather than a number.
