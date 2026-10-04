# Configuration

All configuration is CSV (conventions: `../DATA_FORMAT.md`). One entity per row.

| file | one row per | used by |
|---|---|---|
| `runs.csv` | run: `mock`, `pilot`, `main`, with every setting as a column | `plan` / `run --run <name>` |
| `models.csv` | model alias | every run (`models` column of `runs.csv`) |
| `leak_terms.csv` | forbidden origin cue | `validate-stimuli` (and every run) |
| `text_flags.csv` | pattern of an exploratory reason-text flag | `parse` |
| `analysis_settings.csv` | confirmatory analysis setting (frozen with the preregistration) | `analyze` |
| `country_covariates.csv` | country: World Bank covariates for H1d (fetched, never typed) | `analyze` |

## `runs.csv`

Each run states every setting explicitly; nothing is inherited from a defaults
file, so the `pilot` and `main` rows can be compared cell by cell. The resolved
settings are snapshotted into each run's `run_manifest.json` and hashed
(`config_hash`); `workers` is excluded from the hash.

| columns | meaning |
|---|---|
| `run` | the name used on the command line (`--run mock`) |
| `experiment_id`, `run_id`, `description` | `run_id` empty = `<experiment_id>__<hash of the inputs>`; mock run ids must start with `mock` |
| `models` | aliases of `models.csv` |
| `occupations`, `base_cvs`, `nationalities` | `all`, `pilot` (rows marked pilot in `experiment/stimuli/jobs.csv` / `experiment/stimuli/applicant_cvs.csv`) or a list; `base_cvs` may list `occupation:cv_id` items |
| `include_placebo` | placebo nationalities in baseline independent evaluation of the primary arm ONLY (review H5) |
| `positive_control` | one positive-control clone per base CV, baseline only (A7) |
| `prompt_variants` | wording variants (A3), crossed with every independent-evaluation cell |
| `seed` | master seed: per-call seeds (A17) and execution order (A5) |
| `<condition>_enabled`, `<condition>_repetitions` | per prompt condition (`baseline`, `neutrality`, `forced_choice`, `forced_choice_neutrality`, `principle_probe`): on/off and r per cell |
| `principle_probe_contexts`, `principle_probe_items` | `all` (generic + every occupation; every item) or lists (A11) |
| `fc_tiers`, `fc_exclude_nationalities` | forced-choice tiers; levels never paired (`NONE`; placebo levels are always excluded) |
| `fc_n_cycles`, `fc_copies` | Hamiltonian cycles of nationality pairs (each puts every level in 2 pairs; `all` = all 300 pairs) and CV pairs per nationality pair (A9) |
| `greedy_arm`, `greedy_*` | the greedy-decoding robustness arm (A10): conditions, temperature, repetitions, models, variants; empty when `greedy_arm` is false |
| `temperature`, `top_p`, `max_tokens`, `json_mode`, `logprobs`, `top_logprobs`, `logprobs_max_tokens` | decoding, identical for every model (A10); JSON mode and logprobs are requested only where `models.csv` says the model supports them; logprobs kept for the first N tokens |
| `openai_compatible_extra` | JSON sent to vLLM so that model-specific generation defaults (e.g. `top_k` from `generation_config.json`) cannot change decoding; also serve with `--generation-config vllm` |
| `stop_rule_*` | technical stop rule (review M8): once a model has `first_fraction` of its planned calls answered, stop it if more than `max_non_ok_share` are non-ok; transport errors count neither way |
| `retry_*` | transport/API errors only (A4); `max_api_error_sessions`: an api_error-only call is re-attempted in at most this many sessions |
| `workers`, `plan_expected_output_tokens` | parallel requests; rough output length used by `plan` only |
| `mock_*`, `mock_rate_*` | the deterministic mock provider (used only when `models` = `mock`) |

Notes per run:

- **mock**: tiny end-to-end run, no keys, no network. EVERYTHING IT PRODUCES IS
  SYNTHETIC MOCK DATA, NOT RESULTS (records carry `is_mock = true`).
  `mock_effect_pattern = alphabetical_ramp` gives each nationality code a
  SYNTHETIC effect that depends only on the alphabetical position of its code
  (from -amplitude/2 to +amplitude/2 fit points): deliberately meaningless, so
  that the analysis can be checked against a known ramp and nobody can mistake it
  for a finding. The failure rates exercise every parse path while staying below
  the stop rule. There are no hand-set per-nationality mock effects.
- **pilot** (design contract v0.2; `research/experimental_design.md` section 6):
  3 pilot occupations x 6 base CVs, 26 nationality clones + positive control + 8
  placebo nationalities, K = 3 x r = 3, forced choice with 4 cycles (every level
  in 8 pairs, connected), principle probe 15 items x 7 contexts x r = 5, and all
  four main-study models (every main-study model must be piloted, review M11).
  Pilot analysis runs BLIND (A15).
- **main**: sizes are PROVISIONAL (`baseline_repetitions`, `neutrality_repetitions`,
  `fc_copies` and the model list) until the pilot power analysis
  (`analysis/power_analysis.py`). Do not run before they are fixed, the models are
  verified on bwUniCluster and their revisions are pinned in `models.csv`.

## `models.csv`

| columns | meaning |
|---|---|
| `alias` | the name used in `runs.csv`; records log both the alias and `model_id` |
| `provider` | `mock`, `openai_compatible` (vLLM, the main path), `openai`, `anthropic`, `google`, `hf_local` |
| `model_id` | exact model id (Hugging Face id or dated API snapshot) |
| `revision` | HF commit SHA or dated snapshot; copied into every record; empty = not pinned |
| `status` | `ok` (only the mock); `candidate` (open-weight model for vLLM on bwUniCluster: check availability and quantisation before a real run); `unverified` (optional API model: pin the exact dated id first; do not run until budget is approved) |
| `supports_seed`, `supports_logprobs`, `supports_json_mode` | capabilities |
| `send_top_p` | false for providers that reject temperature and top_p together (recent Claude models) |
| `timeout_s`, `base_url_env`, `api_key_env` | request timeout; names of the environment variables with the endpoint and key (never the key itself; see `.env.example`). Several vLLM servers at once: give each model its own `base_url_env` |
| `extra_body` | JSON passed to the server and logged per record, e.g. Qwen3 "thinking" disabled through `chat_template_kwargs` (design contract, section 5) |
| `serving_engine`, `serving_engine_version`, `dtype`, `quantization`, `gpu_type`, `chat_template_sha256` | provenance (A6); empty when unknown, never guessed |
| `notes` | serving notes |

The runner refuses real calls while `revision` is empty or `status` is
`unverified`, and checks `/v1/models` for the exact `model_id` each session. Serve
exactly the pinned revision (the same command is in `README.md`):

```bash
vllm serve <model_id> --revision <sha> --generation-config vllm --seed 0 --port 8000 --api-key "$VLLM_API_KEY"
```

The API model ids are placeholders from memory: pin exact dated ids before a run.

## `leak_terms.csv`

The stimulus validator forbids these origin cues (adversarial review M6), in
addition to every demonym and country name of `experiment/stimuli/applicant_nationalities.csv`
(case-sensitive). Matching is whole-word.

| column | values |
|---|---|
| `term` | the cue |
| `category` | label: `cities` (capitals and major cities of every listed country, including the base-country cities), `german` (nothing German: cities, regions, credentials, legal forms, standards, software, authorities), `regions`, `languages` (other than English), `country_forms`, `german_currency`, `citizenship`, `religion`, `origin_steering`, `german_characters` |
| `scope` | `all`: every rendered CV (outside its Nationality line), every job ad (localized to every base country), the system prompt, every assembled prompt template (without the neutrality paragraph) and the principle-probe contexts; `texts`: all of these except the CVs (words harmless in a CV that would steer a screener towards origin) |
| `match_type` | `word` (literal, exact case), `word_ignore_case` (literal, any case), `regex_ignore_case` (regular expression, any case), `character` (forbidden anywhere: umlauts, sharp s, euro sign) |
| `allowed_on_cv_line` | label of the one CV line on which the term is allowed (`visa` on `Work authorization: ...; no visa sponsorship required`) |
| `note` | why the term is listed |

The place names of a CV's (or job ad's) own base country (`experiment/stimuli/base_countries.csv`:
name, aliases, cities) are masked before scanning, so "Riyadh, Saudi Arabia"
passes in a CV set in Saudi Arabia while "Saudi" alone, any other country and
any other city stay forbidden. This is a list-based check: it catches the listed
cues, not every conceivable one. `native speakers?` is a regex term, so it
matches both "native speaker" and "native speakers" (until 2026-10-01 it was
matched literally and never fired).

## `text_flags.csv`

Patterns of the EXPLORATORY reason-text flags in `evaluations.csv`
(`mentions_nationality`, `mentions_language`, `mentions_visa`,
`mentions_culture_fit`, `mentions_religion`, `mentions_testing` (A18, evaluation
awareness), `mentions_conflict`).

| column | values |
|---|---|
| `flag` | the flag the row belongs to |
| `pattern_type` | `regex` (Python regex, case-insensitive, wrapped in `\b...\b` unless it contains `\b`); `all_demonyms` / `all_country_names` (every demonym / country name of `experiment/stimuli/applicant_nationalities.csv`; a demonym that starts a country name, "Saudi" in "Saudi Arabia", is matched only outside it); `exclude` (a demonym or country name those two skip: "German" collides with the language, the eight base countries are named in every Location line and job ad) |
| `pattern`, `note` | the pattern (empty for `all_*`); a note |

CAUTION: the flags are crude case-insensitive matches with no negation handling
("nationality played no role" still sets `mentions_nationality = 1`). Use them
only for descriptive, exploratory summaries, never as a primary outcome, and
validate them against the planned hand-coded sample before reporting any of
them. Every pattern is a phrase that cannot match the rendered CVs or job ads (a
test enforces this, review M12). `pronoun_gender` is computed in code. The parser
fingerprint covers this file: changing it after a run requires `parse --exploratory`.

## `analysis_settings.csv`

Confirmatory analysis settings (adversarial review H1), frozen together with
`preregistration.md`; owner: statistician. Columns: `setting` (a dotted name such
as `sesoi.overall_fit` is a nested setting), `value`, `type` (`int`, `float`,
`bool`, `str`, `list`), `description`. `run_analysis` records the file's SHA-256
(line endings normalised) in `summary.md` and in the unblinding log, and stamps
every output "EXPLORATORY OVERRIDE" when a run's analysis config changes any
setting (including resampling counts, e.g. `--quick`) or the file is not
committed at HEAD and unchanged. Unblinding real data requires it to be
committed and unchanged. Changing it after the preregistration is frozen is a
documented deviation (`research/design_decisions.md`).

## `country_covariates.csv`

Written by `scripts/fetch_country_covariates.py` from the World Bank API, with
the retrieval date on every row; never edited by hand; frozen before main-study
data collection.
