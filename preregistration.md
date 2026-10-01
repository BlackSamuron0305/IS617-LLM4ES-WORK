# Preregistration (DRAFT, NOT FROZEN)

| field | value |
|---|---|
| Working title | Beyond "Arab" as a Single Category: A Counterfactual Audit of National-Origin Bias in LLM Hiring |
| Version | 0.4.1-draft |
| Date | 2026-10-01 |
| Status | **Draft. Not frozen. Not timestamped.** Cells carrying a team-decision marker, a pin marker or `[TBD at Stage B]` block the freeze (§14.2). |
| Authors | IS 617 (LLM4ESS) team, University of Mannheim, HWS26 — names added at freeze |
| Venue | OPEN DECISION (review M16): internal file only, OSF, or AsPredicted timestamp |
| Structure | AsPredicted / OSF-style. Internal research document, not paper prose. |

Built from: `research/design_contract.md` v0.6 (§00000 U1–U5, §0000 V1–V10, §000 G1–G7,
§00 B1–B21, §0 A1–A24), `research/experimental_design.md` v0.4, `research/hypotheses.md` v0.4,
`analysis/statistical_analysis_plan.md` v0.5 (cited as **SAP §n**; host-national
handling in SAP §4a), `analysis/multiple_testing_plan.md` v0.4 (MTP),
`analysis/model_specifications.md` v0.4, `config/analysis_settings.csv`, the
input tables in `stimuli/`, `config/*` and `prompts/*` as of 2026-10-01 (all CSV;
conventions in `DATA_FORMAT.md`). Rationale:
`research/design_decisions.md` (D01–D48). Threats: `research/threats_to_validity.md`
v0.4. Review status: `research/review_response.md`. Remaining conflicts: **§16**.

---

## 0. Data collection status

- As of 2026-10-01 **no real model output exists**. The only run is the mock pipeline
  test (`is_mock = true`, synthetic, not results). `results/unblinding_log.jsonl` holds
  entries from mock data only.
- The pilot has not run. The main study has not run. `config/prereg_freeze.json` does
  not exist yet, and the project is not yet committed.
- **Two-stage freeze** (procedure in §14.2).
  - **Stage A — before the pilot runs:** hypotheses, estimands, decision rules, SESOIs,
    analysis plan, placebo set, stimulus tables (A2; `hypotheses.md` header).
  - **Stage B — after the blind pilot, before any main-study call:** N (I, r, c), pinned
    model revisions, frozen prompts and decoding settings, frozen-inputs table (§14.3).
- The analysis is **blind by default**; unblinded analysis of real data is refused by
  the code unless the freeze conditions in §3.4 hold.

## 1. Research questions

- **RQ1 (primary).** Holding the CV constant, do an LLM's evaluations differ across the
  22 Arab League member-state nationality signals; how large is that heterogeneity
  relative to a smallest effect of interest; is it larger than the spread among other
  nationality labels; does it differ between models?
- **RQ2 (secondary).** Does the average Arab League nationality signal receive different
  evaluations from German, Polish, Turkish and no stated nationality?
- **RQ3 (secondary).** Does an explicit nationality-neutrality instruction attenuate,
  leave unchanged, amplify or reverse nationality-associated disparities?
- **RQ4 (exploratory).** Does measured nationality preference differ between forced
  choice and independent evaluation, and in which direction?
- **SQ1 (secondary, descriptive).** Does a model that states nationality should not
  matter nonetheless evaluate applicants differently by nationality?

**Scope of every claim** (review L9, M17): this CV template and output schema; three
wordings; English-language prompts for jobs in **eight Arab League countries** (United
Arab Emirates, Saudi Arabia, Qatar, Kuwait, Oman, Bahrain, Jordan, Egypt; six of them GCC
states) whose **only language requirement is English (C1)**; applicants who live, were
educated and work in the CV's base country, are authorised to work there and **list no
language other than English**; within-Arab and Arab-vs-benchmark estimands **net of one
common host-national effect** (§2.1); the tested open-weight models at their pinned
revisions. No claim about the Maghreb, other Arab labour markets, non-Arab settings or
jobs that require Arabic.

## 2. Hypotheses

### 2.1 Conventions (all hypotheses)

- Every confirmatory test runs **separately per model**. Default: prompt condition
  `baseline`, outcome `overall_fit` (0–100 points), primary arm, counterfactual clones.
  Models are never pooled for confirmatory purposes.
- α = .05 two-sided. Equivalence by TOST (90 % CI inside ±SESOI). For σ_A equivalence
  requires **both** the noncentral-F test and the sphericity-free calibrated bootstrap
  test (SAP §5.4).
- **Four-way labels**, computed from **Holm-adjusted** p-values and Holm-adjusted TOST
  within the family (SAP §4; MTP §3):

  | label | condition |
  |---|---|
  | effect | test rejects and equivalence not established; sub-label **effect exceeds SESOI** if the unadjusted 95 % CI lies entirely beyond the SESOI |
  | trivial effect | test rejects and equivalence established |
  | null (equivalence) | test does not reject and equivalence established — **only if the model passes the manipulation check** (§2.4) |
  | inconclusive | neither |

- **Support** = *effect* in the predicted direction (two-sided hypotheses: *effect*).
- **Robust** = sign holds and CI excludes 0 (σ_A: permutation p < α) under R1, R3
  (≥ 2 of 3 wordings), R4, R5 (Manski bounds for Δ on observed, CV-specific support —
  logical 0/100 support must also pass only if differential missingness rejects; SVI,
  both values, for σ_A) and **HX** (host-national clones excluded, no host term; both the
  22- and the 19-origin version; SAP §4a, §15). Missing checks are named in the label.
- **Host-national status** (SAP §4a; lead decision 2026-10-01). Every CV is set in one
  Arab League base country; the clone whose nationality equals it is a host national
  (exactly one of the 22 Arab clones per CV; never a benchmark, placebo or NONE). All
  clones are kept and every estimand involving Arab origins (δ(n), σ_A for 22 and 19
  origins, σ_A,net, Δ(Ā, b) and their R1 versions, Δ(n, DEU), Δ(n, POL), H1c, H1e,
  H3a/H3b) is computed **net of one common host-national effect η** (CV and nationality
  fixed effects plus η·host; η re-estimated in every bootstrap, permutation and
  calibration replicate; permutations keep each CV's host cell fixed). τ(n) is therefore
  a nationality's level as a non-host applicant. η itself (and η_FC in forced choice) is
  **secondary and descriptive**: 95 % CI only, no family, no decision label, never a
  confirmatory claim, never computed in blind mode. Assumption: one common η for all
  origins; HX is the check.
- Estimand notation: `experimental_design.md` §1.3–1.4. Occupations weigh equally, base
  CVs equally within occupation; stimulus means are averaged over replicates, then over
  the K = 3 wordings, with additive imputation of a wording that has no valid replicate
  (SAP §3).

### 2.2 Confirmatory (primary) — RQ1

Each test runs for the **22-origin set** and for the **19-origin set** (without SOM, DJI,
COM), each as its own Holm family across models.

**H1a — within-Arab heterogeneity exists (F1).**
- Estimand: δ(n) = τ(n) − τ̄_A (host-adjusted, §2.1); σ_A = sqrt((1/J) Σ δ(n)²), J = 22
  (19).
- H0 (sharp): the non-host Arab labels do not change the output distribution of any CV
  (an arbitrary host bonus allowed).
  H1: δ(n) ≠ 0 for at least one n.
- Test: within-CV permutation of the Arab labels (replicates stay attached; each CV's
  host cell kept fixed; η re-estimated per permutation), ≥ 10,000 Monte Carlo
  permutations, statistic = debiased, host-adjusted σ̂²_A (SAP §4a, §5.3). Exact for the
  sharp null, approximately valid for equal mean effects. Expected to reject easily; it is a
  precondition, not the informative result.

**H1b — heterogeneity is negligible (F1-eq).**
- H0: σ_A ≥ SESOI_σ. H1: σ_A < SESOI_σ.
- Established only if the noncentral-F equivalence test **and** the sphericity-free
  calibrated CV-bootstrap test both reject, each Holm-adjusted (SAP §5.4).

**Minimum-effect test (F1-min).** H0: σ_A ≤ SESOI_σ; H1: σ_A > SESOI_σ; rejection ⇔
one-sided 95 % lower limit of σ_A > SESOI_σ (SAP §5.5).

**Decision rule per origin set:**

| H1a | minimum-effect | equivalence (both) | label |
|---|---|---|---|
| rejects | rejects | – | **support: meaningful heterogeneity** |
| rejects | does not | established | trivial heterogeneity |
| rejects | does not | not established | **heterogeneity present; size relative to SESOI undetermined** |
| does not | – | established | **equivalence: a single "Arab" category is adequate** (only with a passed manipulation check) |
| does not | – | not established | **inconclusive** |

**Headline RQ1 label:** the strongest label supported by both origin sets. Identical →
that label; both report heterogeneity but differ → "heterogeneity present; size
undetermined"; otherwise "inconclusive: 22- and 19-origin analyses disagree".

### 2.3 Secondary confirmatory (family F2; Holm within each sub-family)

**H1c — models differ in heterogeneity (baseline).** Wald test of equal debiased σ̂²_A(m)
(variance scale), covariance from a CV bootstrap with shared resamples, inflated by
n_j/(n_j − 1), F(M − 1, I − #occupations) (SAP §5.9). **Support** if Holm-adjusted
p < .05; otherwise **inconclusive** (no equivalence bound; never "models are equal").
Reported with reliability-corrected profile concordance (descriptive).

**H1d — income gradient (ecological, descriptive of structure).**
- Estimand: slope β_W of δ(n) on centred ln GDP per capita, PPP (WDI
  `NY.GDP.PCAP.PP.KD`, 2022) from `config/country_covariates.csv` (fetched by
  `scripts/fetch_country_covariates.py`, retrieved 2026-09-30). **Yemen has no value
  2015–2022 and is excluded: k = 21.**
- H0: β_W = 0; H1: β_W ≠ 0; positive sign predicted.
- Primary estimator (lead decision): REML random-effects meta-regression in the
  21-dimensional contrast space, Knapp–Hartung, t(k − 1 − p) (SAP §5.10). The
  design-based slope is a sensitivity analysis only.
- Decision quantity: predicted difference across the interdecile range (IDR) of ln
  income among the included origins: IDR = 2.964 ln units (numpy linear-interpolation
  percentiles; frozen covariate file, no outcome data), so the 1-point SESOI corresponds
  to about 0.34 points per ln unit.
- Decision: **support** β_W > 0 and *effect*; **contradicted** β_W < 0 and *effect*;
  **null** 90 % CI of the predicted IDR difference within ±1 point and no rejection;
  **trivial** rejection with that CI within ±1; **inconclusive** otherwise.
- Pre-registered sensitivity slopes: + `wb_sub_saharan` (COM, MRT, SOM, SDN); the
  sub-Saharan indicator alone; income group (ordinal); excluding fallback-year origins
  (none). Occupation-specific slopes exploratory.
- Stated now: income is collinear with sub-Saharan association and conflict, so a slope
  is not a test of status → competence (review M9).
- **Arab-world setting (v0.4).** The response variable is the host-adjusted δ̂(n). The
  six high-income origins are exactly the six GCC states, which are also the base
  countries of 36 of 48 CVs, so the top of the income scale is entangled with proximity
  to the setting (host status: adjusted; GCC-partner status in other GCC states: not
  adjusted, threat C15). A positive slope is therefore not read as a status gradient
  unless it survives this caveat. The prediction (positive sign) is unchanged; its
  motivation now rests on setting-independent LLM status associations
  (`hypotheses.md` H1d). GCC-indicator sensitivity slope (log GDP + GCC indicator):
  `[TEAM DECISION REQUIRED BEFORE FREEZE]` (pre-register as an additional sensitivity
  slope, or report the confound only).

**H1e — within-Arab spread vs placebo spread (review H5).**
- Estimand: σ_A − σ_placebo on the same base CVs; σ_placebo = the same debiased estimator
  over the 8 placebo signals (URY, BOL, SYC, MWI, MDV, NPL, MYS, KHM), baseline IE,
  primary arm. σ_A is host-adjusted; placebos are never host nationals.
- Setting caveat (v0.4, threat C18): the placebo rule was fixed for a German setting; in
  Gulf labour markets "Nepalese" in particular carries a labour-migrant association
  [VERIFY]. The set is not changed. Leave-one-out σ_placebo as a pre-registered
  sensitivity: `[TEAM DECISION REQUIRED BEFORE FREEZE]`.
- Test: variance-scale difference with a shared stratified CV bootstrap (inflated
  variance), two-sided t(I − #occupations); SD-scale 95 % CI by bootstrap percentiles
  (SAP §5.8). Holm across models.
- Decision (SAP §5.8): **Arab spread exceeds placebo spread** iff the 95 % SD-scale CI
  lies above 0 **and** the Holm-adjusted p < .05; **below placebo spread** iff the CI lies
  below 0 and the Holm-adjusted p < .05; otherwise **not distinguishable from placebo
  spread** (never "equal").
- Interpretation fixed now: any claim that the within-Arab spread is Arab-specific
  requires "exceeds"; a headline heterogeneity label without it is reported as
  heterogeneity of the order of generic nationality-label spread. SD-scale CI coverage
  was 91 % at 18 CVs and 94 % at 48 CVs in simulation; check it at the frozen main size.

**H2a–H2d — Arab mean vs benchmarks.**
- Estimands: Δ(Ā, b) = τ̄_A − τ(b), b = DEU (H2a), POL (H2b), TUR (H2c), NONE (H2d);
  host-adjusted (each Arab origin at its non-host level; unadjusted, Δ would be shifted
  by η/22, SAP §4a).
- H0: Δ = 0; H1: Δ ≠ 0. **No direction pre-registered.**
- Test: per-CV contrast (host-adjusted per-CV values ψ_i, SAP §4a), occupation-stratified
  t (Welch–Satterthwaite), TOST at ±SESOI (SAP §4, §6). Four-way label; with a 1-point
  SESOI, *inconclusive* is an expected label.
- Interpretation aids (v0.4, Arab-world setting): every benchmark is a foreign national
  with the same legal status on the record as a non-host Arab national (GCC partners
  aside, C15), so legal status no longer separates the benchmarks. **Ā–DEU compares a
  foreign Arab national with a Western-European expatriate**: it bundles origin with a
  possible Western-expatriate premium (C17) and with a possible inferred-Arabic
  advantage of the Arab applicants (C16), which run in opposite directions; Ā–POL
  compares with a Central-European, Christian-majority expatriate; Ā–TUR with a
  non-Arab, Muslim-majority regional neighbour whose national language is not Arabic;
  Ā–NONE may carry a host-like component if a fully local CV without a nationality line
  is read as a local applicant (C10). Checked with R9, `mentions_language` and HX;
  Δ(DEU, NONE) is descriptive. The German-setting aids (Ā–TUR closest on non-EU legal
  status; Ā–POL = EU free movement; inferred-German channel C13) are withdrawn. Benchmark
  roles (keep DEU, POL, TUR with this reading, or replace / add a benchmark):
  `[TEAM DECISION REQUIRED BEFORE FREEZE]`.

**H3a — neutrality instruction and dispersion.** ΔD_σ = σ_A(neutrality) − σ_A(baseline);
variance-scale paired CV bootstrap, t(I − #occupations); SD-scale 95 % / 90 % intervals
(SAP §7). **Attenuation** = *effect* with ΔD_σ < 0; **amplification** = *effect* with
ΔD_σ > 0; **no change** = 90 % interval within ±SESOI_σ; **inconclusive** otherwise.

**H3b — neutrality instruction and the Arab–DEU gap.** ΔD_DEU (per-CV
difference-in-differences of host-adjusted values, each condition with its own η̂,
stratified t, TOST). **Attenuation** = *effect* towards zero;
**amplification** = *effect* away from zero; **overcorrection** = sign change with both
conditions' CIs excluding 0; **no change** = equivalence within ±SESOI; **inconclusive**
otherwise. If the baseline disparity is *null (equivalence)*, H3a/H3b are reported as
"does the instruction create disparities".

### 2.4 Descriptive (CIs only, no tests)

- **Manipulation check** (review M1): PC = positive-control clone − NONE clone
  (baseline); **passed** iff PC < 0 and its one-sided 95 % upper limit < 0 (SAP §9). It
  shows that the model reads the CV, not that the design is sensitive at SESOI scale.
- λ (neutrality − baseline on NONE), Δ(DEU, NONE), σ_A,net (SAP §5.7), E_m, variance
  components with 80 % upper limits.
- **Host-national effect** η per model × condition × outcome (`host_effect.csv`) and η_FC
  in forced choice: secondary, descriptive, 95 % CI only (SAP §4a). It bundles "local
  applicant", knowledge of nationalisation policies (threat C14) and congruence with
  every employer and school; it is not read as discrimination or as a pure citizenship
  effect.
- **SQ1 classification** (per model): gap / substantive gap / consistent /
  unclassifiable (`hypotheses.md` SQ1), using the RQ1 headline label and the H2 labels.
  **E_m ≈ 1 is expected** because the reverse-keyed items are blatant, so "gap" may be
  nearly automatic whenever a disparity is found (review L11). No combined index.

### 2.5 Exploratory (labelled; no confirmatory claims)

Per-origin δ(n), Δ(n, DEU), Δ(n, POL) with simultaneous max-|t| bands, BH q-values
(q = .05) and rank intervals, with the HX values of δ(n) beside the host-adjusted ones;
ΔD_POL, ΔD_TUR; nationality × model / condition / wording
profile tests (SAP §8); occupation × origin, tier × origin; occupation-specific H1d
slopes; RQ4 (Bradley–Terry worths, position bias, dispersion ratio, concordance,
tie-free sensitivity; SAP §12–13); `forced_choice_neutrality`; text flags (incl.
unsupported language concerns by nationality) and pronoun inference; `confidence`;
model cross-checks MS1–MS3 (`model_specifications.md`).

### 2.6 Not hypothesised

No hypothesis names a particular Arab origin as favoured or disfavoured; none concerns
a specific occupation or tier. No origin is called "most" or "least" favoured unless its
simultaneous band excludes the Arab mean.

## 3. Design

### 3.1 Factors and levels

| factor | levels | notes |
|---|---|---|
| N nationality signal | 22 Arab League member states; DEU (reference), POL, TUR; NONE (line omitted); 8 placebo signals | rows of `stimuli/nationalities.csv`; placebo: baseline IE, primary arm only |
| clone type | 34 nationality renderings + 1 positive control per base CV (35) | PC = NONE rendering minus every qualification line that satisfies the must-have (`positive_control_education` in `stimuli/cvs.csv`; master's and bachelor's for master's CVs); baseline only |
| J occupation | 6 main; pilot: software_developer, retail_sales_associate, warehouse_associate | fixed strata, equal weight |
| I base CV (nested in J) | rows of `stimuli/cvs.csv`: main default 8 per occupation (2 strong / 4 adequate / 2 borderline), final I `[TBD at Stage B]`; pilot 6 (2/2/2) | independent unit (cluster) |
| base country (attribute of I) | ARE (Dubai), SAU (Riyadh), QAT (Doha), KWT (Kuwait City), OMN (Muscat), BHR (Manama), JOR (Amman), EGY (Cairo); fixed allocation per same-tier CV pair (`fc_pair`, `base_country` in `stimuli/building_blocks/cv_slots.csv`): 3 pairs = 6 CVs per country, each pair in a different occupation; pairs per country (strong/adequate/borderline) ARE, SAU, KWT, JOR 1/1/1, OMN, BHR 1/2/0, QAT, EGY 0/2/1; pilot: every country once, ARE twice | absorbed by the CV effects; job ad located there; FC pairs share it |
| host_national (derived) | 1 if nationality = base country: one Arab clone per CV; 8 host-eligible nationalities, each host in 6 of 48 CVs (pilot: ARE 4, the others 2 of 18) | common fixed effect η in primary estimates; HX sensitivity (SAP §4a) |
| P prompt condition | baseline, neutrality (IE); forced_choice, forced_choice_neutrality (FC); principle_probe | FC-neutrality exploratory, off in the pilot |
| K wording variant | k1, k2, k3 | crossed with every IE cell; FC: one variant per quad, Latin-rotated per nationality |
| r replicate | pilot 3; main `[TBD at Stage B]` (default 2) | replicates, not candidates |
| m model | §5 | fixed levels, never pooled |
| FC arrangement × order | quad = {CV1:a, CV2:b}, {CV1:b, CV2:a} × AB, BA | two different same-occupation, same-tier CVs with the same base country; NONE and placebo excluded (25 levels); BT host term host_A − host_B |
| principle item × context | 12 target (6 pro, 6 reverse) + 3 control × 7 contexts; r = 5 | items `prompts/principle_items.csv`; recipe `principle_probe` in `prompts/prompt_recipes.csv` |

Robustness arm (main only): `greedy` (T = 0, r = 1, baseline, all models, all K). The
former native-German arm (R12) is withdrawn: no CV lists German (G2).

### 3.2 Held constant

Within a base CV across clones: everything except the nationality line, **by
construction** — each prompt renders one CV row with one nationality row through one
template (G1); the job ad shown with a CV is the same for all its clones.
Across base CVs (design constants, validated identical in every row):
`Availability: One month's notice`; `Languages: English (C1)` (no other language
anywhere); nothing dated after 06/2024; one template; no name, photo, date of birth,
gender, pronouns, religion, marital status or birthplace. One system prompt incl. the
constant pseudonymisation sentence.
Per base country (constant within a CV, varying across CVs; V1, validated against
`src/hiringaudit/stimuli/setting.py`): `Location: <base city>, <country>`; `Work
authorization: Authorized to work in <the country>; no visa sponsorship required`;
`Driving licence: Valid driving licence issued in <the country>`; employer cities and
education institutions (real universities and colleges) on the base country's whitelist
(`stimuli/base_countries.csv`, `stimuli/building_blocks/institutions.csv`), the most
recent job in the base city. One job ad per
occupation, localised to the CV's base city (otherwise identical), invented
country-neutral employer, only language requirement "Fluent English (C1 or higher)".
Nothing German anywhere (validator-scanned).
Decoding: T = 0.7, top_p = 1.0, top_k −1, min_p 0, repetition penalty 1.0, max_tokens
400, JSON mode where supported, Qwen3 thinking off.

### 3.3 Randomisation

- No treatment assignment is random: every base CV carries every nationality.
- Execution order: seeded shuffle of all calls within a model; each model's conditions
  in one contiguous serving window; `execution_index` logged.
- Seeds from nationality-free fields (A17); master seed 20261013. The CV table was
  rebuilt for the Arab-world setting on 2026-10-01 with seed 20261001
  (`scripts/build_cv_table.py --force`; previously seed 20260929); the table is now the
  source of truth. Base countries are allocated by a fixed table, not at random (§3.1).
- FC nationality pairs: seeded Hamiltonian-cycle design, balanced and connected;
  wording variants Latin-rotated and balanced per nationality (pilot: 100 pairs, each
  level in 8 quads, variant spread ≤ 1; main: all 300 pairs, c = 2 PROVISIONAL, each level
  in 48 quads, 16 per variant).

### 3.4 Blinding (enforced in code; SAP v0.4 §0, §16)

- `python -m hiringaudit analyze` is **blind by default** and writes to
  `results/<run_id>/blind/`. Blind output: design and balance checks, parse/refusal
  diagnostics (differential missingness as one omnibus p-value), manipulation checks,
  scale use per tier (P3), FC position diagnostics (P7), principle-probe summaries (P8),
  text-flag and pronoun base rates without nationality breakdown (P9, P11), variance
  components with 80 % upper limits (P6). No per-origin means, contrasts, rankings, σ_A,
  placebo comparison, nationality tests, host-national effect (η, η_FC) or HX results.
  A blind run refuses a non-empty directory without `summary.md`.
- `--unblind` on data that are not entirely mock requires **all** of: (i) this file and
  `config/prereg_freeze.json` committed at HEAD and identical to the working tree;
  (ii) the freeze's `preregistration_sha256` equal to the SHA-256 of this file (CRLF → LF);
  (iii) no unresolved team-decision or pin markers in this file; (iv)
  `config/analysis_settings.csv` committed at HEAD and unchanged. Otherwise the run
  stops with a one-line `UnblindingError` (exit 2) and nothing is logged. Unblinded
  output goes to `results/<run_id>/unblinded/`.
- The analysis config (`analyze --config <file.json>`) cannot set the project root, the
  confirmatory-settings path or the log path; `analyze` checks relative to `--root`.
- Every unblinded run is appended to `<root>/results/unblinding_log.jsonl`.
- An analysis config that changes any confirmatory setting, or a confirmatory file that is not
  committed or differs from the committed version, stamps every output "EXPLORATORY
  OVERRIDE"; outputs from an exploratory re-parse are stamped "EXPLORATORY PARSE".
- During main collection, monitoring is limited to aggregate technical indicators and
  the nationality-blind stop rule.
- Tier validation: two team members assign tiers to NONE renderings blind to the tier
  column; agreement reported.

### 3.5 Run sizes (`python -m hiringaudit plan --run <pilot|main>`, re-run 2026-10-01; counts unchanged by the setting change and by the move to CSV tables)

| run | per model | notes |
|---|---|---|
| pilot (row `pilot` of `config/runs.csv`) | 10,807: baseline 4,212 + placebo 1,296 + PC 162 + neutrality 4,212 + FC 400 + principle 525 | 4 models, 43,228 total |
| main (row `main` of `config/runs.csv`) | 26,637: baseline 7,488 + placebo 2,304 + PC 288 + neutrality 7,488 + greedy 3,744 + FC 2,400 + FC-neutrality 2,400 + principle 525 | **PROVISIONAL**; 4 models, 106,548 total |

## 4. Stimuli and their validation

- **Two tables and one template** (G1): `stimuli/cvs.csv` (48 base-CV rows, wide columns,
  no nationality), `stimuli/nationalities.csv` (34 rows; notes in `stimuli/README.md`),
  `stimuli/cv_template.txt`. Nothing is pre-rendered: each prompt renders job ad + one CV
  row + one nationality row at call time; every rendered prompt is stored once per
  SHA-256 in `data/raw/<run_id>/prompts.jsonl`. The CV table was built by
  `scripts/build_cv_table.py` from `stimuli/building_blocks/*.csv`, `stimuli/jobs.csv`
  and `stimuli/base_countries.csv` (rebuilt 2026-10-01 for the Arab-world setting; the
  builder reproduces it byte for byte); the table is the source of truth and may be edited
  directly (then re-validated).
- **CV content** (V7): 2–3-sentence profile; key achievements (strong 3, adequate 2,
  borderline 2); 3–5 bullets per relevant job; skills 12 / 10 / 8 by tier; up to 3
  certificates; length fixed within a tier. Strong software developers, accountants and
  consultants hold a master's preceded by its bachelor's (same base country); strong
  retail, warehouse and administrative CVs an advanced diploma. Retail, warehouse and
  administrative must-haves read "Diploma in …".
- **Tier rubric** (review H2), relative to the ad's minimum relevant experience (req; 3
  years for software, accountant, consultant; 2 for retail, warehouse, admin): strong
  ≥ req + 36 months; adequate req + 1…20 months, no unrelated jobs; borderline 12–18
  months short of req, one earlier genuinely unrelated job, total experience below
  every adequate CV.
- **Validator** (`python -m hiringaudit validate-stimuli`; exit 1 on any violation;
  passed on 2026-10-01): renders all 48 × 34 combinations plus 48 positive controls
  (1,680) in memory; every rendering equals the DEU rendering except
  `^Nationality: <demonym>$` (NONE: removed); positive control = NONE minus exactly the
  lines of the CV's `positive_control_education` entries (every qualifying education entry), with no qualification
  cue left anywhere; well-formed tables (unique ids and references, known occupations
  and tiers, DEU and NONE present); design constants identical in every row; **English is
  the only language**; the base country is a whitelisted Arab League base country, the
  base city is its own, and the Location, work-authorisation and driving-licence lines
  are the derived ones; employer cities and institutions on the **base country's
  whitelist**; every CV has exactly one same-occupation, same-tier, same-country partner
  with the same pilot status (its FC pair); applicant references never encode a
  nationality; **list-based** leak check (`config/leak_terms.csv`, incl. German terms)
  over rendered CVs, the job ads localised to every base country, every prompt part and
  the assembled prompt templates — only the CV's own base country and its cities are exempt; it catches
  listed terms only; no date after 06/2024 and experience months consistent with job
  dates; tier ordering per occupation; title–bullet and achievement–tier coherence
  against the builder pools; prompt recipes checked structurally (`prompts/README.md`,
  "Checks"): each neutrality recipe = its baseline recipe of the same variant + exactly
  one step, the part `neutrality_paragraph`, immediately before the output instructions
  (same for forced choice).
- **Near-duplicate check** (pairwise token-set Jaccard below a threshold): threshold
  `[TO SET BEFORE STAGE A]`; not yet implemented in code (Discrepancy 24).
- **Tier validation:** blind two-coder assignment; pilot P3 per tier, P4, P5; failures
  lead to revision and re-pilot, documented.
- **Job ads:** invented, country-neutral English employer names (no legal suffix), each
  ad localised to the CV's base city; only language requirement "Fluent English (C1 or
  higher)"; accountant ad asks for IFRS; names checked against company registers of the
  base countries (and internationally) before publication.
- **Base-country mix:** six of eight base countries are GCC states (threat E9); the
  Amman retail and Cairo warehouse pairs (both in the pilot) come with English-only ads
  that may read as implausible (threat E10). Keep the allocation as a scope limit or
  re-allocate before the pilot: `[TEAM DECISION REQUIRED BEFORE FREEZE]`.
- **Principle items:** team review of the draft wording before Stage A.

## 5. Models

| alias | exact model id | pilot | main | revision |
|---|---|---|---|---|
| qwen3-8b | Qwen/Qwen3-8B | yes | yes | **TO PIN BEFORE FREEZE** |
| llama-3.1-8b-instruct | meta-llama/Llama-3.1-8B-Instruct | yes | yes | **TO PIN BEFORE FREEZE** |
| gemma-3-12b-it | google/gemma-3-12b-it | yes | yes | **TO PIN BEFORE FREEZE** |
| mistral-small-3.2-24b-instruct | mistralai/Mistral-Small-3.2-24B-Instruct-2506 | yes | yes | **TO PIN BEFORE FREEZE** |
| optional API model (M17) | placeholders `gpt-4.1-mini`, `claude-sonnet-4-5`, `gemini-2.5-flash` (`unverified`) | only if budget approved | only if piloted | dated snapshot **TO PIN BEFORE FREEZE** |

- Served with vLLM on bwUniCluster, one model per instance,
  `--revision <sha> --generation-config vllm --seed 0`.
- The runner refuses `--allow-real-calls` when a selected model has an empty `revision` (`config/models.csv`), is
  `unverified`, when git shows modified or untracked files under `src/`, `config/`,
  `prompts/` or `stimuli/` in the data root or in the repository holding the running
  code, or when the vLLM server does not serve the configured `model_id`. The code must
  be committed and tagged before the pilot.
- Recorded per model: HF commit SHA, chat-template hash, vLLM version, dtype,
  quantisation, GPU type (`null` when unknown), training cut-off from the model card.
- API model `[TEAM DECISION REQUIRED BEFORE FREEZE]`. A model enters the main study only
  if it was piloted; the list is never changed after seeing nationality results.

## 6. Outcomes

| role | variable | scale |
|---|---|---|
| **Primary** | `overall_fit` under baseline | 0–100 job-fit score (points). Never a hiring probability. |
| **Key secondary** | `interview` | yes/no → percentage points; every family repeated (R2) |
| Secondary | non-ok status (incl. terminal `api_error`) | analysed as an outcome (§7) |
| Secondary | FC `choice` → chosen nationality | Bradley–Terry (RQ4, exploratory) |
| Secondary | principle `answer` × keying, `agreement` | SQ1 |
| Exploratory | `confidence`; phrase-pattern text flags (incl. `mentions_language` for unsupported language concerns such as Arabic, C16, and `mentions_visa` for unsupported sponsorship concerns, C2); `pronoun_gender`; parser diagnostics `n_json_objects`, `near_miss` (never outcomes) | descriptive |

R10 (logprob P(interview = yes)) is not in the processed schema and is not planned
unless implemented before Stage B (Discrepancy 17).

## 7. Exclusions and missing data

- **Rows in confirmatory models:** `arm == "primary"`, `clone_type == "counterfactual"`,
  `parse_status == "ok"`, placebo rows only in H1e.
- **Nothing is dropped silently.** Every status is counted per task × model × condition ×
  arm and per nationality.
- **Transport/API errors** are retried within a call (max 5 attempts, exponential backoff
  with jitter). Calls whose only records are `api_error` are re-attempted on resume in at
  most 3 sessions, attempts counted across sessions; after that the `api_error` is
  terminal and listed in the manifest.
- **Malformed JSON, schema violations, refusals, empty outputs** are terminal: **never
  re-sampled, never coerced**. The first JSON object in an output is the answer.
- **Differential missingness is an outcome:** within-CV permutation test of the total
  non-ok share (terminal `api_error` included) across nationalities, reported split by
  type (blind pilot: one omnibus p). If it rejects in the main study, R5 becomes
  co-primary and the logical-support bounds become decision-relevant.
- **R5** = worst-case Manski bounds for each Δ contrast; the robust label uses
  **observed, CV-specific support** (min/max of the valid responses of the same base CV);
  logical 0/100 support is reported with the bound width (descriptive unless
  missingness rejects). **SVI** (every non-ok call at the lowest / highest observed value)
  for σ_A, labelled as imputation, not a bound (SAP §10).
- **Missing wordings** are imputed additively within the CV before averaging; cells with
  no valid wording stay missing.
- **No outlier removal** of valid scores. **FC non-choices** are NA, rate reported,
  never coerced.
- **Technical stop rule** (implemented, nationality-blind): once a model has 5 % of its
  planned calls answered, it is stopped if more than 10 % of those answers are non-ok;
  transport failures (`api_error`) count neither in numerator nor denominator. Recorded
  in the run manifest. Fix, re-pilot, document the deviation, archive the aborted data
  unanalysed.
- **Parser freeze:** `parse` refuses a parser version or fingerprint that differs from the
  one recorded in the run manifest; `parse --exploratory` writes marked tables to
  `data/processed/<run_id>__exploratory/`, whose analysis outputs are stamped
  "EXPLORATORY PARSE" and never confirmatory.
- **Model retention** for persistently > 10 % non-ok output in the pilot
  `[TEAM DECISION REQUIRED BEFORE FREEZE]`; decided on pilot parse rates only.
- **Pilot responses** never enter confirmatory analyses. **Mock data** are never results;
  mock run ids must start with `mock`, real ones must not.

## 8. Smallest effect sizes of interest

Defaults in `config/analysis_settings.csv` (`sesoi.*` rows; `sesoi_is_final` = false). **A2 requires
them to be fixed before the pilot runs (Stage A).**

| quantity | default | alternatives (SAP §11) | status |
|---|---|---|---|
| contrasts on `overall_fit` | **1.0 point** | anchor to the fit shift that moves the interview rate by 5 pp (pilot fit→interview link, NONE clones, blind) | `[TEAM DECISION REQUIRED BEFORE FREEZE]` |
| σ_A on `overall_fit` (H1b, minimum-effect, H3a) | **1.0 point** | as above | `[TEAM DECISION REQUIRED BEFORE FREEZE]` |
| contrasts and σ_A on `interview` | 5 pp | 2 pp; 10 pp (four-fifths heuristic at 50 %) | `[TEAM DECISION REQUIRED BEFORE FREEZE]` |
| forced choice | 0.45–0.55 (±0.20 logit) | 0.40–0.60 | `[TEAM DECISION REQUIRED BEFORE FREEZE]` |
| H1d | 1.0 point across the IDR (≈ 0.34 points per ln unit) | follows the fit SESOI | `[TEAM DECISION REQUIRED BEFORE FREEZE]` |
| SQ1 endorsement | E_m ≥ 0.90 | — | `[TEAM DECISION REQUIRED BEFORE FREEZE]` |

**Why 1 point (review H4).** The only LLM CV audit with an Arab group reports −1.41
points on a 1–100 scale, a discrimination ratio of 0.85 at a cutoff (Lippens 2024,
checked against the full text by the reviewer). A 2-point SESOI would have labelled that
effect trivial or null.

**Trade-off stated in advance.** With 1 point, equivalence for Δ contrasts and for H3 is
likely unreachable at feasible N, so many RQ2/RQ3 results will be *inconclusive*; the
power analysis reports minimum detectable effects instead. The SESOI is never changed
after the pilot, to fit the budget, or after data are seen. The positive control is a
yardstick, never a SESOI.

## 9. Analysis plan (summary; SAP v0.5)

| step | what | SAP |
|---|---|---|
| Blinding, frozen settings, provenance | blind default; unblinding gate (committed files, hash, markers, confirmatory config); log; override and exploratory-parse stamps | §0 |
| Units, arms, loader checks | base CV = cluster; primary arm; mixed revisions/prompt versions refused; placebo only in H1e | §1 |
| Estimands | τ, δ, σ_A, σ_A(19), σ_A,net, σ_placebo, Δ, ΔD, λ, PC, β, E_m | §2 |
| Replicates and wordings | averaged; additive imputation of missing wordings | §3 |
| Linear contrasts and labels | per-CV contrasts, stratified t, TOST, Holm-based labels | §4 |
| Host-national status | common host fixed effect η in all Arab estimands; design-based inference incl. η's error; η re-estimated per resample; permutations keep host cells fixed; η descriptive; HX sensitivity required for "robust"; BT host term and host-free sensitivity | §4a |
| RQ1 | raw H/R with noise floor; debiased σ_A; H1a; H1b (two tests); minimum-effect test and labels; exploratory per-origin; σ_A,net; H1e (label rule); H1c; H1d | §5.1–5.10 |
| RQ2 | Δ(Ā, b), labels, R1 versions | §6 |
| RQ3 | H3b DiD; H3a bootstrap | §7 |
| Profile tests | nationality × model / condition / wording | §8 |
| Manipulation check | one-sided PC | §9 |
| Missing data and bounds | non-ok incl. terminal api_error; Manski R5 (observed support for the robust label); SVI | §10 |
| SESOIs | defaults, alternatives, trade-off | §11 |
| Forced choice, RQ4 | Bradley–Terry; format comparison | §12–13 |
| SQ1 | E_m, controls, classification | §14 |
| Robustness | R1–R13 (R12 withdrawn) and HX | §15 |
| Blind mode | pilot outputs (no host effect, no HX) | §16 |
| Variance components and power | 80 % upper limits; power script | §17 |
| Confirmatory vs exploratory | status table | §18 |

Mock-labelled outputs carry "SYNTHETIC MOCK DATA — NOT RESULTS".

## 10. Multiple-testing strategy (MTP)

- F1: H1a per model, Holm across models, one family per origin set (22, 19).
- F1-eq: H1b per model; noncentral F and sphericity-free test, each Holm across models
  per origin set (four families); equivalence requires both.
- F1-min: minimum-effect test per model and origin set, Holm across models.
- F2 sub-families, each Holm over all its tests, not adjusted against each other: H1c
  (1, baseline); H1d (M); H1e (M); H2 (4M); H3 (2M).
- Estimation tier: σ_A, Δ(Ā, b), δ(n), Δ(n, DEU) with marginal CIs and simultaneous 95 %
  bands, all host-adjusted; no significance claims.
- Host-national effect η and η_FC (MTP tier 2b): no family, no Holm, no decision label;
  its p-value is unadjusted and is not a test of a hypothesis.
- Exploratory per-origin / pairwise: BH q = .05 plus max-|t| bands.
- `interview` (R2): same structure, own Holm adjustment.
- The RQ1 headline label needs both origin sets (intersection–union; no further
  adjustment). FWER per family; Holm across F1 and all F2 would be a documented deviation.

## 11. Sample size and stopping rule

1. **Pilot** (fixed, §3.5) → blind analysis → variance components per model with 80 %
   upper limits from a stratified CV bootstrap (SAP §17).
2. **Power simulation** (`analysis/power_analysis.py`, fast engine, ≥ 2,000 simulations
   per cell, M = number of main-study models, ρ_ε = 0, `--use upper`). Targets: H1a power
   ≥ .80 at σ_A = SESOI_σ at α/M; H1b power ≥ .80 at σ_A = 0; SE(δ̂(n)) ≤ SESOI/2.5
   (= 0.4 points with the default); TOST power for Δ(Ā, DEU); FC c such that SE(β_n) ≤ FC
   SESOI (logit)/2.5. H1a and H1b are expected to be nearly automatic; sizing will be
   driven by the SE and TOST targets (review M14).
3. **Allocation:** smallest r ∈ {1, 2, 3, 5} whose decoder-noise term is ≤ ¼ of the
   stimulus-interaction term (default r = 2); then smallest I ≥ 8 per occupation (1 : 2 : 1)
   meeting the targets. If the authoring ceiling `[TEAM DECISION REQUIRED BEFORE FREEZE;
   proposed 16]` binds, run at the ceiling and report the achieved minimum detectable
   effects and the narrowest supportable equivalence bound. More CVs means more rows in
   `stimuli/cvs.csv`, validated before Stage B; they must come as same-tier pairs with
   one base country each (validator rule), allocated so that every base country keeps
   the same number of CVs (equal host cells per host-eligible nationality, D45).
4. **Frozen N** at Stage B: `I = [TBD at Stage B]`, `r = [TBD at Stage B]`,
   `c = [TBD at Stage B]`.
5. **No optional stopping.** No interim analysis by nationality; every cell is run once
   in randomised order to completion. Only the technical stop rule (§7) halts a model.
6. **Mock-provider output is never used for sizing.**

## 12. Robustness checks

| id | check | status |
|---|---|---|
| R1 | 19 origins (without SOM, DJI, COM) — also a co-requirement of the RQ1 headline label | planned |
| R2 | all confirmatory families on `interview` | planned |
| R3 | per-wording estimates; nationality × wording test; δ-profile correlation | planned |
| R4 | greedy decoding arm | planned (main config) |
| R5 | Manski worst-case bounds for Δ (observed support for the robust label; logical support descriptive); SVI for σ_A | planned; co-primary if differential missingness rejects |
| R6 | occupation-specific; leave-one-occupation-out | planned |
| R7 | tier-specific estimates | planned |
| R8 | within-CV rank outcome | planned |
| R9 | POL and NONE as references (= H2b, H2d); also the check for the Western-expat premium C17 and the inferred-Arabic channel C16 (NONE possibly read as a local applicant, C10) | planned |
| R10 | logprob P(interview = yes) | **not implemented**; dropped unless implemented before Stage B |
| R11 | H1d sensitivity slopes (sub-Saharan, income group, fallback exclusion) | planned |
| R12 | native-German language-line arm | **withdrawn** (G2: no German listed anywhere) |
| R13 | empirical-Bayes shrunken δ(n) | planned |
| HX | host-national clones excluded, no host term: σ_A (22 and 19 origins), δ(n) beside the adjusted values, Δ(Ā, b); BT without quads containing a host national (SAP §4a) | planned; **required for the "robust" label** (`host_exclusion_required_for_robust: true`) |
| GCC | GCC-partner sensitivity (threat C15): GCC nationals in a CV set in another GCC state as quasi-host applicants (indicator identified from GCC nationals in JOR/EGY vs other GCC CVs, or σ_A on the 12 JOR/EGY CVs) | `[TEAM DECISION REQUIRED BEFORE FREEZE]`; not implemented in code |

## 13. What we will NOT do

- No post-hoc selection or dropping of countries, placebo labels, CV rows, occupations,
  prompts, wordings or models based on results; no new benchmark or sensitivity set after
  data.
- No reporting of p > .05 as "no bias": a null is claimed only as *null (equivalence)*
  within the pre-registered SESOI, with a passed manipulation check.
- No "meaningful heterogeneity" unless the lower bound of σ_A exceeds the SESOI in both
  origin sets; no claim that the within-Arab spread is Arab-specific unless H1e says
  "exceeds".
- No reading of Arab-vs-benchmark contrasts as pure origin bias: Ā–DEU compares foreign
  Arab nationals with a Western-European expatriate and can carry a Western premium (C17)
  and an inferred-Arabic advantage of the Arab set (C16); Ā–NONE may carry a host-like
  component (C10).
- No reading of the host-national effect η as discrimination, as a confirmatory finding
  or as a pure citizenship effect; no unadjusted within-Arab estimate presented as
  primary.
- No reading of a GCC-shaped δ profile or a positive H1d slope as a status gradient
  without the GCC-proximity caveat (C15).
- No calling the 0–100 score a hiring probability; no treating `confidence` as calibrated.
- No calling forced choice a "jailbreak"; no claim that it reveals a "truer" preference.
- No pooling across models for confirmatory tests.
- No re-sampling of malformed, empty or refused outputs; no coercion of non-choices or
  near-misses.
- No optional stopping; no interim nationality breakdowns; no changing SESOIs, N,
  stimulus tables, parser or confirmatory settings after seeing outcome data (changes are
  EXPLORATORY OVERRIDE / EXPLORATORY PARSE or documented deviations).
- No unblinded analysis of real data before the freeze; no use of pilot responses in
  confirmatory analyses; no use of mock output as results or for power.
- No claim that a named origin is "most" or "least" favoured unless its simultaneous band
  excludes the Arab mean; no 231 pairwise significance claims.
- No mechanism claims (religion, conflict, race, visa, language) from text flags, reasons
  or H1d; no "anti-Arab" or "anti-Muslim" framing — outputs say "Arab League
  member-state nationalities" and "national-origin signal".
- No claim that the validator rules out every origin cue (it is list-based).
- No generalisation beyond the scope in §1 (in particular not to jobs that require
  Arabic, to Arab labour markets outside the eight base countries, or to non-Arab
  settings); no claim about real people from these countries.
- No presentation of the principle–behaviour comparison as a new construct or index.

## 14. Freeze

### 14.1 Checklist

Stage A = before the pilot runs. Stage B = before any main-study call.

| # | item | owner | stage | status |
|---|---|---|---|---|
| 1 | Ratify SESOI values (§8); set them (`sesoi.*` rows) and `sesoi_is_final` = true in `config/analysis_settings.csv` | Team + Statistician | A | open |
| 2 | Freeze `hypotheses.md` v0.4 | Methodologist | A | ready for review (after items 23–27) |
| 3 | Resolve remaining discrepancies (§16) | Methodologist + Statistician + Engineer | A | open |
| 4 | Sign off principle-item wording | Team | A | open |
| 5 | Ukrainian benchmark (one more row in `stimuli/nationalities.csv`); its rationale ("refugee-associated in Germany") was German-specific: re-motivate or drop | Team | A (before stimuli freeze) | open |
| 6 | Model retention rule for > 10 % non-ok in the pilot | Team | A | open |
| 7 | Blind two-coder tier check on the CV table rebuilt on 2026-10-01 | Team | A | open |
| 8 | Set the near-duplicate threshold; implement and run the check | Engineer | A | open |
| 9 | Commit and tag code, configs, prompts, stimulus tables (required by the real-call guard and the unblinding gate) | Engineer | A | open |
| 10 | Verify models on bwUniCluster; pin revisions and provenance in `config/models.csv` | Engineer | A (pilot), B (main) | open |
| 11 | Covariate file committed with retrieval date (fetched 2026-09-30) | Lead | A | check committed |
| 12 | Implement or drop R10 and the calibration subset (threats I3/I6) | Engineer | A | open |
| 13 | Timestamped registration venue (M16) | Team | A | open |
| 14 | Write the Stage A freeze (§14.2) | Team | A | not started |
| 15 | Run pilot (4 models); blind analysis; document P1–P11 decisions | Team + Statistician | B | not started |
| 16 | Power simulation (§11); write I, r, c; check H1e CI coverage at the frozen size | Statistician | B | not started |
| 17 | FC c | Team + Statistician | B | provisional |
| 18 | API model (M17) and snapshot pinned, or open-weight-only scope confirmed | Team | B | open |
| 19 | Authoring ceiling per occupation; add CV rows if needed and re-validate | Team | B | open |
| 20 | Hand-coding protocol (sample size, codebook, coders); validate text flags | Team | B | open |
| 21 | Fill the frozen-inputs table (§14.3) and write the Stage B freeze | Team | B | not started |
| 22 | Employer names checked against company registers of the eight base countries (and internationally) | Team | before publication | open |
| 23 | Benchmark roles in the Arab-world setting: keep DEU, POL, TUR with the provisional reading (§2.3 H2), or replace / add a benchmark (stimulus change) | Team | A (before stimuli freeze) | open |
| 24 | GCC-partner sensitivity (§12 "GCC", threat C15): pre-register (and implement) or leave to interpretation | Team + Statistician | A | open |
| 25 | H1d GCC-indicator sensitivity slope (§2.3 H1d): pre-register or report the confound only | Team + Statistician | A | open |
| 26 | Leave-one-out σ_placebo for H1e (threat C18): pre-register or not | Team + Statistician | A | open |
| 27 | Base-country mix and the English-only Amman retail / Cairo warehouse pairs (§4; threats E9, E10): keep as scope limits or re-allocate before the pilot | Team | A (before stimuli freeze) | open |
| 28 | Verify the [VERIFY] claims about Arab labour markets (nationalisation policies, GCC labour mobility, sponsorship, CV conventions, pay hierarchies) and the local institution names before anything enters the paper | Team | before publication | open |

### 14.2 Freeze procedure (how to write `config/prereg_freeze.json`)

The analysis accepts a freeze only if this file and the freeze file are committed at
HEAD and identical to the working tree, the hash matches, this file carries **no
unresolved markers** (the bracketed team-decision marker and the pin marker; exact strings
in SAP §0), and `config/analysis_settings.csv` is committed and unchanged (SAP v0.4
§0). At each stage:

1. Complete the stage's checklist items. Replace every marker in this file with the
   decided value (also `[TBD at Stage B]` at Stage B); update §15 and, at Stage B, §11 and
   §14.3. This file must be complete **before** hashing: any later edit changes the hash.
2. Set the ratified SESOIs (`sesoi.*` rows) and `sesoi_is_final` = true in
   `config/analysis_settings.csv`. Commit everything and tag the commit
   (`prereg-stage-a`, later `prereg-stage-b`).
3. Compute the hashes exactly as the analysis does (CRLF normalised to LF):

   ```bash
   PYTHONPATH=src python -c "from hiringaudit.analysis.settings import sha256_text; print(sha256_text('preregistration.md'))"
   PYTHONPATH=src python -c "from hiringaudit.analysis.settings import sha256_text; print(sha256_text('config/analysis_settings.csv'))"
   ```

4. Write `config/prereg_freeze.json`. The analysis reads `preregistration_sha256`; the
   other keys are for the audit trail:

   ```json
   {
     "preregistration_sha256": "<hash from step 3>",
     "stage": "A",
     "frozen_utc": "<ISO 8601 time>",
     "git_tag": "prereg-stage-a",
     "git_commit": "<commit of step 2>",
     "confirmatory_config_sha256": "<SHA-256 of config/analysis_settings.csv, LF>",
     "previous_preregistration_sha256": []
   }
   ```

   At Stage B, overwrite `preregistration_sha256`, `stage`, `frozen_utc`, `git_tag` and
   `git_commit`, and append the Stage A hash to `previous_preregistration_sha256`.
5. **Commit the freeze file** (the gate requires it committed at HEAD); register the
   frozen file (or its hash) with the chosen timestamp venue (M16).
6. After Stage B, **this file is never edited.** Any edit breaks the hash or the
   committed-at-HEAD check and the code refuses unblinding until a new freeze is written.
   Deviations are recorded, dated, in `research/design_decisions.md`; a re-freeze is
   itself a deviation and is visible in git history and in the preregistration hash of
   every unblinding-log entry.

### 14.3 Frozen inputs (filled at Stage B)

| input | SHA-256 / value |
|---|---|
| git tag / commit | `[TBD at Stage B]` |
| `config/analysis_settings.csv` | `[TBD at Stage B]` |
| `stimuli/cvs.csv`, `stimuli/nationalities.csv`, `stimuli/cv_template.txt` | `[TBD at Stage B]` |
| prompt tables `prompts/prompt_parts.csv`, `prompts/prompt_recipes.csv` (and the `user_prompt_version` of every condition × variant) | `[TBD at Stage B]` |
| `stimuli/jobs.csv`, `prompts/principle_items.csv` | `[TBD at Stage B]` |
| validator and builder inputs `config/leak_terms.csv`, `stimuli/base_countries.csv` and `stimuli/building_blocks/*.csv` (incl. institution whitelist and base-country allocation) | `[TBD at Stage B]` |
| run settings: row `main` of `config/runs.csv` (sizes, decoding, seed) | `[TBD at Stage B]` |
| `config/country_covariates.csv` | `[TBD at Stage B]` |
| parser version / fingerprint (covers `config/text_flags.csv`) | `[TBD at Stage B]` (currently `PARSER_VERSION = 2`) |
| model revisions | `[TBD at Stage B]` |
| I, r, c | `[TBD at Stage B]` |

## 15. Version and changelog

| version | date | change |
|---|---|---|
| 0.1-draft | 2026-09-30 | Initial draft from contract v0.2, design v0.1, hypotheses v0.1, SAP v0.2, MTP v0.2, model specifications v0.2 and configs. |
| 0.2-draft | 2026-09-30 | Adversarial-review fixes: placebo set and H1e; 19-origin co-requirement; minimum-effect test; two equivalence tests; SESOI defaults 1.0; one-sided manipulation check; Manski R5 and SVI; blinding enforced and freeze procedure; parser freeze; stop rule and api_error redo; tier rubric; list-based leak check; Latin-rotated FC variants; power defaults; H1d ecological; scope statement. |
| 0.3-draft | 2026-09-30 | Structural change (contract G1–G7): table-based stimuli rendered at call time; English is the only language (no German anywhere; native-German arm R12 withdrawn; C4 replaced by C13 in the Ā–DEU interpretation); Rhine-Neckar same-region rule; HGB wording; Mistral piloted (4 models, pilot 43,228 calls); main 106,548 calls. Round-2 fixes (SAP v0.4): stricter unblinding gate and freeze procedure; R5 robust label on observed support; terminal api_error counts as non-ok, excluded from the stop rule, re-attempted in at most 3 sessions; H1e label rule; MS1–MS3; exploratory-parse stamp. Discrepancies 10, 16, 19, 21, 22 resolved. |
| 0.4-draft | 2026-10-01 | Arab-world setting (contract V1–V10; design decisions D44–D47): every CV set in one of eight Arab League base countries (employers, real local institutions, job ad localised to the base city; location, work-authorisation and driving-licence lines per base country; nothing German); base countries allocated per same-tier CV pair (3 pairs per country); FC pairs share a base country; `host_national` recorded; **primary estimates net of one common host-national effect (SAP v0.5 §4a)**, η descriptive; **HX required for "robust"**; BT host term and host-free sensitivity; extended CVs, master's CVs list the bachelor's, positive control removes every qualifying line; CV table rebuilt with seed 20261001; DEU now a Western-European-expatriate benchmark, German-setting benchmark aids and threat C13 withdrawn (C16, C17 added); H1d setting caveat (GCC = high-income origins); scope rewritten; new open decisions (checklist 23–27) marked; discrepancies 25 updated, 26–29 added. Run sizes unchanged (pilot 43,228; main 106,548). |
| 0.4.1-draft | 2026-10-01 | Structural only (contract U1–U5, design decision D48): every input is now a CSV table and prompts are assembled from parts; every rendered prompt is byte-identical. Paths, commands and the freeze procedure updated: `config/analysis_settings.csv` replaces `config/analysis_confirmatory.yaml` (§3.4, §8, §14), `--run <pilot\|main>` replaces `--config config/<x>.yaml` (§3.5), prompt tables in §4 and §14.3, `config/runs.csv` row added to §14.3, hash command for the settings file in §14.2. No design change. |

Before the Stage B freeze, changes are made here and in the changelog. After it, only in
`research/design_decisions.md` as dated deviations (§14.2 step 6).

## 16. Discrepancies

Status after the v0.5 setting change (2026-10-01) and SAP v0.5. "Resolved" = documents
and code now agree.

| # | discrepancy | status |
|---|---|---|
| 1 | Effect labels use Holm-adjusted tests | **resolved** |
| 2 | H1d estimator, k, IDR base, CI level | **resolved** (lead decision; SAP §5.10) |
| 3 | Blind-mode missingness: one omnibus p | **resolved** |
| 4 | SESOI timing | **resolved in documents** (Stage A); values still open |
| 5 | σ_A SESOI on `interview` | **resolved** (5 pp) |
| 6 | "Robust" definition details | **resolved** (hypotheses v0.3 §0 = SAP §15) |
| 7 | H1c scope ("one Wald test per condition" in MTP) | **resolved in substance** (confirmatory family uses baseline only); MTP wording minor |
| 8 | ΔD_POL, ΔD_TUR | **resolved** (exploratory; not implemented) |
| 9 | Pilot FC scope | **resolved** |
| 10 | Mistral in the main list but not piloted | **resolved** (G4: pilot uses all 4 models) |
| 11 | CR-23 sentence described as optional | **resolved** |
| 12 | Principle-probe size | **resolved** (15 items, 525 calls) |
| 13 | `expected_answer` | **resolved** |
| 14 | Safeguard sizing and ρ_ε | **resolved** (SAP §17) |
| 15 | Calibration subset (threats I3/I6/I7) not implemented | **remaining** (checklist 12) |
| 16 | `api_error` in the missingness outcome and R5 | **resolved** (SAP v0.4 §10: terminal api_error counts as non-ok) |
| 17 | R10 listed but not implementable | **remaining** (checklist 12) |
| 18 | Stale text in contract v0.2 / `variables.md` | **resolved** |
| 19 | Id clash SAP S1–S3 vs threats S1–S11 | **resolved** (SAP v0.4 renamed MS1–MS3) |
| 20 | H1c / H3a nulls on SD vs variance scale | informational (same null) |
| 21 | Confirmatory-config hash not enforced against a frozen value | **resolved** (SAP v0.4 §0: the file must be committed at HEAD and unchanged, otherwise EXPLORATORY OVERRIDE / no valid freeze) |
| 22 | H1e label rule missing in SAP and code | **resolved** (SAP v0.4 §5.8; `analysis/hypotheses.py` emits the labels) |
| 23 | Freeze file written at Stage A vs final hash at Stage B | **resolved by procedure** (§14.2) |
| 24 | Near-duplicate check promised but not implemented; threshold unset | **remaining** (checklist 8) |
| 25 | SAP v0.4 still lists the `native_german` arm → R12 (§1 arms, §15) and says it builds on contract v0.2 | **partly resolved**: SAP v0.5 marks the arm as removed and R12 withdrawn; its header still says it builds on contract v0.2 (minor; SAP owner) |
| 26 | Documents described the setting as Mannheim / Rhine-Neckar, the PC as one EDUCATION line, DEU as host reference, threat C13 | **resolved** 2026-10-01 (this version, contract V1–V10, research documents v0.4) |
| 27 | Job ads no longer contain A24's "Applications in English are welcome" sentence; documents quoted it | **resolved in documents** (recorded as a deviation, `design_decisions.md` §3 #9); the contract text of A24 is kept as history |
| 28 | `stimuli/nationalities.csv` note for PSE still reads "Not recognised as a state by Germany" (German-setting note) | **remaining** (stimuli owner; `stimuli/README.md` note updated) |
| 29 | SAP §20.3 asked `preregistration.md` and `hypotheses.md` to mention §4a and HX before the freeze | **resolved** (§2.1, §2.2, §12 here; `hypotheses.md` v0.4 §0) |
