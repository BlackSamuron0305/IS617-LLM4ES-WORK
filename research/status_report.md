# Research status report — 2026-09-30 (updated 2026-10-01)

> **Update 2026-10-01 (user request).** This supersedes the 2026-09-30 notes below
> wherever they conflict.
>
> - **Setting.** The labour-market setting is now the Arab world; nothing in the stimuli
>   is German. Each CV has one base country (UAE, Saudi Arabia, Qatar, Kuwait, Oman,
>   Bahrain, Jordan, Egypt), with 3 same-tier CV pairs per country spread over
>   occupations and tiers. Its employers, its schools (real local universities) and the
>   advertised job are all in that country. Forced-choice pairs share a base country.
> - **Host nationals.** `host_national` marks clones whose nationality equals the base
>   country. Primary estimates adjust for one common host effect, a sensitivity check
>   (HX) drops those clones, and the host effect is reported descriptively.
> - **CVs.** CVs are longer: profile, key achievements, more bullets and skills.
>   Master's CVs also list the bachelor's, and the positive control removes every
>   qualifying degree line.
> - **Cleanup.** The old project's `archive/` was deleted. `paper/` carries the working
>   title and the verified bibliography. Nothing is committed (user's choice); the
>   deleted old files therefore still show as "deleted" in git until the next commit.
> - **Verification.** `validate-stimuli` passes (1,680 combinations), `pytest` gives
>   294 passed, a clean mock run → parse → blind and unblinded analysis works, and
>   real calls are still refused.
> - **Calls.** Pilot 43,228 (4 models), main 106,548 (provisional).
> - **New design questions for the team:**
>   - Benchmark roles. German is now a Western-expat benchmark; are Polish and Turkish
>     still the right comparison countries for Gulf/Levant labour markets?
>   - Base-country mix. Six of the eight base countries are Gulf states.
>   - Whether English-only retail and warehouse jobs read as plausible in Cairo and
>     Amman.
> - **Structure (later on 2026-10-01).** All YAML files were replaced by CSV tables:
>   `config/runs.csv`, `models.csv`, `analysis_settings.csv`, `leak_terms.csv`,
>   `text_flags.csv`, plus `stimuli/jobs.csv` and `stimuli/building_blocks/`.
>   Prompts are assembled from `prompts/prompt_parts.csv` following
>   `prompts/prompt_recipes.csv`. Rendered prompts are byte-identical to before
>   (`tests/test_prompt_snapshot.py`). Commands now use `--run mock|pilot|main`.
> - **Environment.** Windows Application Control intermittently blocks Python extension
>   DLLs (pandas, scipy). Re-running the command works. Run pytest with
>   `-p no:hypothesispytest`.

> **Update (later on 2026-09-30, user request).** The stimuli are now two tables,
> `stimuli/cvs.csv` and `stimuli/nationalities.csv`. Prompts combine one CV row with one
> nationality row at call time, so the pre-rendered clone files are gone.
>
> Other changes in the same update:
> - Jobs require English only, and CVs list English (C1) only.
> - All past positions and schools are in the Rhine-Neckar region.
> - The native-German robustness arm was removed, so open decision 5 below no longer
>   applies.
> - The main study is now 106,548 calls; the pilot is unchanged at 43,228.
>
> New trade-off: with no German listed anywhere, a model may assume only the German
> applicant speaks German. That affects Arab-vs-German contrasts, not within-Arab ones.
> `mentions_language` measures it.
>
> Verification after the change: 246 tests pass, and all 1,680 combinations validate.

Stage: **pre-pilot, ready pending team decisions.** No real model has been called.
Every number in `results/` and `data/*/mock*` is synthetic mock data and is labelled
as such.

## 1. What exists

| Area | State | Where |
|---|---|---|
| Literature review | 193 sources, all confirmed to exist (69 read in full, 117 abstract, 7 metadata only; 68 added on 2026-10-04); keys consistent across matrix, bib and all docs | `research/literature_review.md`, `literature_matrix.csv`, `references.bib` |
| Novelty audit | Falsification searches in English, German, Arabic on arXiv, OpenAlex, ACL Anthology, Semantic Scholar (partly rate-limited), web | `research/novelty_assessment.md` |
| Causal design | Potential-outcomes estimands, variables, hypotheses, threats, 40 traced design decisions | `research/experimental_design.md`, `variables.md`, `hypotheses.md`, `threats_to_validity.md`, `design_decisions.md` |
| Statistics | Analysis plan, model specs, multiple-testing hierarchy, simulation power script | `analysis/*.md`, `analysis/power_analysis.py` |
| Stimuli | 48 base CVs (6 occupations × 8, tiered), 2 × 1,680 validated clones (22 Arab League + 3 benchmarks + 8 placebos + not-stated + positive control), diffs, manifests | `stimuli/` |
| Pipeline | Stimulus generation/validation, providers (mock, vLLM, OpenAI, Anthropic, Google, HF), resumable runner, parser, blind-by-default analysis, figures, LaTeX tables | `src/hiringaudit/` |
| Preregistration | Draft v0.2 with freeze checklist and freeze procedure | `preregistration.md` |
| Ethics | Synthetic data, no deployment, reporting rules, legal framing | `ETHICS.md` |
| Adversarial review | Two rounds by an independent agent; round 1 "major revision" (5 HIGH), round 2 "minor revision"; the two remaining round-2 items (N1 unblinding bypass, N2 git check) were then fixed | `research/adversarial_review.md`, `research/review_response.md` |

## 2. Verification performed (2026-09-30)

- `validate-stimuli`: `[v1] OK: 1680 clones`, `[v1_native_german] OK: 1680 clones`, 0 errors.
- `pytest -q`: **253 passed**.
- Clean mock run → resume (no duplicates) → parse → analyze blind → analyze `--unblind`:
  all succeed; every output carries "SYNTHETIC MOCK DATA — NOT RESULTS".
- `run --run pilot --allow-real-calls`: **refused** (exit 2): model revisions
  unpinned, working tree uncommitted. This is intended.
- The reviewer's 33 validator tamper cases: 31 caught in round 2; the title–bullet case
  (T26) was fixed afterwards; the remaining miss (a changed applicant number) is trivial.

## 3. Strongest current novelty claim

Within our search coverage, no prior study has tested, in controlled LLM hiring
decisions with qualifications held fixed, whether evaluations differ systematically
across individual Arab national-origin signals. The closest work pools "Arab" into one
group (Lippens 2024; Hoffmann et al. 2026), covers a single Arab country (Salinas et al.
2023: Jordan; Huijzer & Chen 2025: Morocco), or studies values rather than decisions
(MENAValues).

## 4. Strongest threat

"Predictable combination plus noise": Lippens shows a pooled Arab penalty, MENAValues
shows that models differentiate Arab countries, and any 22 labels will spread by chance.
Defences in the design:

- a noise-corrected heterogeneity estimate with a permutation noise floor;
- 8 placebo nationalities, for a pre-registered comparison of Arab spread with placebo spread;
- the 19-origin result (excluding Somalia, Djibouti and Comoros) required for the headline claim.

Open literature risk: Bilon 2025 has a national-origin factor, and its countries could
not be checked without library access.

## 5. Unresolved decisions (team)

1. **SESOIs**: default 1.0 fit point and 5 pp interview. Must be fixed *before* the
   pilot. With 1 point, equivalence ("no meaningful difference") will often be out of
   reach, and those contrasts will read "inconclusive". That is the honest trade-off.
2. **Models**: pin HF commit SHAs for Qwen3-8B, Llama-3.1-8B-Instruct, Gemma-3-12B-it,
   Mistral-Small-3.2-24B. Add one API model if there is budget; otherwise every claim is
   scoped to open-weight 8–24B models.
3. **Timestamped registration** of the preregistration (OSF or AsPredicted) before the pilot.
4. Ukrainian benchmark (default: not included).
5. "Native German" vs "C2" as the primary language line (default: C2 primary, native as a robustness arm).
6. Model retention rule (drop a model with more than 10% unusable output?).
7. Authoring ceiling for base CVs per occupation (main default 8; power may ask for more).
8. Wording of the principle-probe items (drafts in `prompts/principle_items.csv`).
9. Two-coder blind check that the qualification tiers read as intended.
10. Timeline: pilot ~20.10, freeze ~27.10, main before the 11–12.11 midterm.
11. Lead decisions the team may reverse before the pilot:
    - retail sales associate replacing sales representative;
    - the 8-country placebo set;
    - fit score as primary outcome, interview as key secondary.

## 6. Pilot design

- **Models:** 4 open-weight, served by vLLM on bwUniCluster.
- **Occupations:** software developer, retail sales associate, warehouse associate; 6 base CVs each (2 strong, 2 adequate, 2 borderline).
- **Nationality conditions:** 22 Arab League + DEU/POL/TUR + not stated; 8 placebos in baseline only.
- **Prompt conditions:** baseline and neutrality, 3 wordings × 3 replicates; a positive-control clone per CV; 100 forced-choice quads (nationality swap × order swap); principle probe (15 items × 7 contexts × 5 replicates).
- **Analysis:** the pilot analysis is blind. It outputs only variance components, manipulation checks and failure rates. These feed the power simulation that fixes the main-study size.

## 7. Expected calls

| Run | Calls | Input tokens (rough) | Output tokens (expected / max) |
|---|---|---|---|
| Pilot | 43,228 (10,807 per model) | ≈ 37.6M | ≈ 3.5M / 17.3M |
| Main (provisional) | 114,036 | ≈ 107M | ≈ 9.1M / 45.6M |

Token counts use a characters ÷ 4 heuristic and are rough. On bwUniCluster, the cost is
GPU time only.

## 8. What must be approved before real data collection

1. Items 1–3 of section 5 (SESOIs, pinned model revisions, registration venue).
2. A commit of the repository. The runner refuses real calls from an uncommitted tree.
   The generated stimuli (~22 MB) are meant to be committed.
3. Writing `config/prereg_freeze.json` after the preregistration is final
   (procedure: `preregistration.md` §14.2). This is needed only for unblinding, not for
   running the pilot.
4. A vLLM endpoint on bwUniCluster (`VLLM_BASE_URL` in `.env`).
5. Explicit go-ahead to run
   `python -m hiringaudit run --run pilot --allow-real-calls`.

## 9. Known limits, stated in advance

- **Scope:** single CV template, English prompts, a German setting. The three wordings share one template, so robustness across wordings is weak evidence of robustness across prompts.
- **What is estimated:** the total effect of a nationality line for German-educated applicants. The foreign-credential channel is held fixed.
- **Principle probe:** the reverse-keyed items are blatant, so near-universal endorsement of neutrality is expected. The principle–behaviour comparison is descriptive, not a new concept.
- **Placebo comparison:** its interval covers about 91% at pilot size. It becomes relevant only at main size.
