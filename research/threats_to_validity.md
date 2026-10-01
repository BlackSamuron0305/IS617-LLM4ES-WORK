# Threats to validity

Version 0.4 (methodology), 2026-10-01. Companion to
`research/experimental_design.md` (design), `research/hypotheses.md`
(decision rules) and `research/lit_parts/M_change_requests.md` (CR-n).

**v0.4 changes** (Arab-world setting of 2026-10-01; contract V1–V10; design decisions
D44–D47): every CV is set in one Arab League base country and one Arab clone per CV is a
host national. **New threats:** C14 (host status and nationalisation-policy priors), C15
(GCC nationals' cross-GCC right to work vs the constant authorisation line), C16
(inferred-Arabic language channel), C17 (Western-expatriate premium for DEU), C18
(setting-specific associations of placebo labels), S12 (one common host effect), E9
(Gulf-heavy base set), E10 (English-only retail and warehouse ads in Cairo and Amman).
**Superseded:** C4 (German C2 vs native; work-authorisation incongruity for DEU/POL) and
C13 (inferred-German channel). Updated to the new setting: I1, C1, C2, C5, C6, C7, C9,
C10, C11, C12, E1–E5, E7, E8. Robustness check **HX** (host-national clones excluded) is
new and required for the "robust" label.

**v0.3 changes** (structural change of 2026-09-30; contract G1–G7): I1 updated for
table-based stimuli rendered at call time; C2 and E4/E7 updated for the English-only
language requirement and the Rhine-Neckar same-region rule; **C4 resolved** (no German
listed anywhere) and replaced by the new threat **C13** (language channel in
Arab-vs-DEU contrasts); C11 wording adjusted.

**v0.2 changes** (adversarial review; `research/review_response.md`): mitigations
updated to the implemented state (I1, I3, I5, I8, C3, C5, C6, S2, S5, S8, E3, E6); new
threats **C11** (Horn-of-Africa / race confound), **C12** (demonym idiosyncrasy),
**S10** (sphericity), **S11** (analyst degrees of freedom after seeing data).

**Severity** (after considering the threat without mitigation):
**H** = could reverse or invalidate a confirmatory conclusion;
**M** = could bias magnitude or limit interpretation;
**L** = minor, or a scope limit to be stated. "Residual" gives the severity
after the listed mitigation.

Robustness check ids (R1–R13, HX) refer to `experimental_design.md` §8 and SAP §4a.
Citation convention: `[VERIFY]` marks references whose existence or details I
am not certain of.

---

## I. Internal validity (is the within-CV contrast caused by the nationality line?)

**I1. Clone integrity.** A clone differs from its reference in more than the
nationality line (template bug, whitespace, a field conditional on nationality).
*Severity* H, *residual* L. *Mitigation:* nothing is pre-rendered: each prompt
renders one CV row of `stimuli/cvs.csv` with one nationality row of
`stimuli/nationalities.csv` through one template, so clones differ only in the
Nationality line by construction (G1); `validate-stimuli` renders all 48 × 34
combinations plus 48 positive controls (1,680) in memory and fails on any difference
beyond that line; design constants must be identical in every table row; list-based
origin-cue check over CVs, job ads and prompts (`config/leak_terms.csv`, review M6 —
catches listed terms only); base-country whitelists for employer cities and
institutions (V1; formerly Rhine-Neckar, G3) and the derived base-country lines
(location, work authorisation, driving licence), which are identical across the clones
of a CV; the positive control checked against `positive_control_education`; title–bullet
coherence against the builder pools. *Probe:* validator run before every real run
(passed 2026-10-01: 1,680 combinations); SHA-256 of both tables, the template,
`stimuli/jobs.csv`, `prompts/principle_items.csv` and the prompt tables
(`prompts/prompt_parts.csv`, `prompts/prompt_recipes.csv`) part of the run identity; every rendered prompt
stored by SHA-256.

**I2. Execution order, batching and time.** If clones of one nationality run
together (one batch, one time window), server load, batch composition, cache
state or a mid-run update become confounded with nationality. *Severity* M,
*residual* L. *Mitigation:* one seeded shuffle over all cells within a model;
all conditions for a model in one contiguous serving window [CR-5].
*Probe:* log `execution_index`; check that execution index is balanced across
nationalities; regress outcome on execution index (drift check).

**I3. Model-version drift.** Weights, tokenizer, chat template or serving stack
change during or between runs; API aliases silently move. *Severity* M (H for
API models), *residual* L. *Mitigation:* HF commit SHA, tokenizer/chat-template
hash, vLLM version, dtype, quantisation, GPU type in the manifest; dated API
snapshots only [CR-6]. Implemented (review H3): the run identity includes the full
model specs, so a changed revision starts a new run; `--allow-real-calls` is refused
for an empty revision (`config/models.csv`), an unverified model, an uncommitted tree or a vLLM server not
serving the configured model; the analysis loader refuses mixed revisions. *Probe:* a
fixed calibration subset (proposed 100 stimuli) run at the start and end of each
model's run (cf. Chen, Zaharia & Zou 2024 [chen2024chatgpt]) — **not implemented**;
until it is, the drift probe is the execution-index regression (I2).

**I4. Position effects (forced choice).** LLM judges favour one position
(Zheng et al. 2023; Wang et al. 2023 [wang2024large]), also in pairwise CV comparisons
(Rozado 2025 [rozado2026gender]). *Severity* M, *residual* L. *Mitigation:* the quad puts
each nationality on each CV in each position, so position cancels in π_q;
position bias γ is estimated in the Bradley–Terry model. *Probe:* share of
position-determined quads per model (pilot P7); such quads carry no nationality
information, and a model dominated by them is flagged as low-information for
FC (pre-registered, not an exclusion).

**I5. Prompt sensitivity.** LLM outputs change with small, meaning-preserving
changes to prompt wording and format (Sclar et al. 2024 [sclar2024quantifying]). With one
template, every conclusion is conditional on that wording and a
"prompt-specific effect" cannot even be detected. *Severity* H, *residual* M.
*Mitigation:* K = 3 wording variants crossed with nationality within base CV
[CR-3]; the estimand averages over them. One system prompt, one output schema and one
CV template remain a limitation: the three wordings share the output block, so
"robust across wordings" is weak evidence of prompt robustness and claims are scoped
to this template (review L9). *Probe:* R3 (per-wording estimates, nationality ×
wording test, correlation of δ profiles across wordings).

**I6. Isolation failures.** A call sees another call's content (conversation
history, shared session) — violating A1. *Severity* H, *residual* L.
*Mitigation:* stateless calls; no multi-turn context; principle probe in fresh
contexts. Prefix caching of the shared system prompt only affects numerics.
*Probe:* calibration subset (I3) run with caching on and off once.

**I7. Nondeterminism.** Even at T = 0, batched inference is not bit-reproducible
across batch compositions (e.g. Thinking Machines Lab 2025 blog on
nondeterminism in LLM inference [he2025defeating]). *Severity* L. *Mitigation:* treated
as noise; randomised order makes it independent of nationality; seeds logged.
*Probe:* I3 calibration subset.

**I8. Differential refusal, parse failure and retry selection.** If a model
refuses or breaks the schema more often for some nationalities, analysing only
parseable answers is selection on the outcome; re-sampling until a parseable
answer appears does the same. *Severity* H, *residual* M. *Mitigation:*
transport errors are the only retried failures; model-output failures are
terminal outcomes [CR-4]; api_error-only calls are redone on resume (review M7);
`parse_status` is analysed as an outcome; a missing wording is imputed additively
within the CV so that wording effects do not leak into contrasts (review M15).
*Probe:* within-CV permutation test of equal non-ok shares across nationalities (per
model; blind pilot: one omnibus p); R5 = worst-case Manski bounds for Δ contrasts
(robust label on observed, CV-specific support; logical 0/100 support descriptive,
decision-relevant only if the omnibus test rejects; review M2, N3) and single-value
imputation sensitivity (SVI) for σ_A; R5 becomes co-primary if the omnibus test
rejects. Terminal `api_error` cells count as non-ok (SAP v0.4 §10).

---

## C. Construct validity (does the manipulation and measurement mean what we say?)

**C1. Nationality vs ethnicity vs religion (and the rest of the bundle).** A
stated nationality lets the model infer ethnicity, religion, language,
migration history, conflict exposure and national wealth. MENA ≠ Arab ≠ Muslim.
*Severity* M (H if the paper claims "anti-Arab" or "anti-Muslim" bias).
*Mitigation:* the estimand is the **total effect of the national-origin signal**
(Greiner & Rubin 2011; Sen & Wasow 2016); mechanism claims are exploratory.
Partial triangulation: POL (European, non-MENA, Christian-majority), TUR (non-Arab,
Muslim-majority MENA, national language not Arabic), variation within the Arab set (H1d
on income; exploratory conflict status), text flags for religion and conflict. In the
Arab-world setting the bundle also contains host status (C14), GCC-partner status (C15)
and an inferred-Arabic channel (C16). Separating religion from origin
needs a design like Adida, Laitin & Valfort (2010) — Parked. The counterfactual
approach to social categories has principled critics (Kohler-Hausmann 2019
[kohlerhausmann2019eddie]); our claim is limited to what the signal does to model outputs.
*Probe:* `mentions_religion`, `mentions_conflict` by nationality
(exploratory); wording discipline in the paper ("national-origin signal").

**C2. Visa / work-permit and language channels (rewritten v0.4 for the Arab-world
setting; the German-language part is superseded).** A model may penalise a foreign
nationality because it assumes the applicant needs employer sponsorship or lacks a
language the job needs. *Severity* M. *Held constant by:* an explicit work-authorisation
line per base country ("Authorized to work in <the country>; no visa sponsorship
required"), identical across the clones of a CV; `Languages: English (C1)` in every
clone; education and employers in the base country; and job ads whose only language
requirement is "Fluent English (C1 or higher)", which every applicant meets (G2, V1). The
visa channel and the *required*-language channel are therefore closed *on the record*;
if a model still voices them, the concern is **unsupported by the record** and part of
the total effect. *Residual:* the authorisation line may not read the same for every
nationality. It is natural for host nationals (citizens; C14) and plausible for GCC
nationals in another GCC state (C15); for other foreign nationals in Gulf labour
markets, where expatriate work permits are usually tied to an employer's sponsorship
[VERIFY], "no visa sponsorship required" may read as unusual (e.g. as a dependant's or a
long-term resident's status). Arabic is neither required nor listed, so a model may still
assume Arabic skills from an Arab nationality: threat C16. *Measurement:* flags
`mentions_visa`, `mentions_language`; a stratified hand-coded sample separates concern
from neutral mention and from disclaimers, with two-coder agreement (design §3).
*Probe:* rate of unsupported visa/language concerns by nationality and nationality group
(exploratory, descriptive).

**C3. Names.** *Why excluded from the primary design.* (i) A name carries
gender, religion, ethnicity and class signals and is not nationality-specific:
the same Arabic name is common across many of the 22 states and among non-Arab
Muslims, so no name identifies a nationality. (ii) With one name per origin,
name idiosyncrasies (frequency, familiarity, famous bearers, transliteration)
are perfectly confounded with origin — the stimulus-sampling problem (Wells &
Windschitl 1999); names signal groups imperfectly and unevenly (Gaddis 2017).
Validated name sets exist mainly for US race/ethnicity categories (e.g.
Crabtree et al. 2023 [crabtree2023validated]), not for 22 Arab national origins.
(iii) The nationality line isolates the construct of interest better.
*Cost:* realism (real CVs carry names); the reference number may read as an
anonymised procedure; the model may default to a gender. *Severity* M.
*Mitigation:* constant `APP-dddd` reference; a constant system-prompt sentence on
pseudonymised screening in every condition (A23; not a pilot factor); pronoun flag in
reasons (exploratory). *Secondary name experiment (Parked):* one pan-Arab name held
constant across all 22 Arab nationalities, crossed with a no-name arm
(2 × 22). It asks whether a constant Arab ethnic cue shifts the level and
whether within-Arab heterogeneity survives it (i.e. whether heterogeneity is
carried by national rather than ethnic information). The name is chosen from
validated sources and pre-tested for regional non-specificity; it is **never
assumed** to identify a nationality. A single male name adds gender, which must
be stated or crossed.

**C4. German national listed with C2 German; work authorisation stated for German
and Polish nationals — SUPERSEDED (v0.4).** The language part was resolved in v0.3 (no
CV lists German, G2). The remaining part (an unrestricted right to work is superfluous
for German and EU nationals in Germany) no longer applies: in the Arab-world setting
DEU and POL are foreign nationals like the others. The analogous incongruity now sits in
the **host-national clones** (a citizen stating authorisation to work in their own
country; C14, removed by HX) and, more weakly, in GCC partners (C15).

**C13. Language channel in Arab-vs-DEU contrasts (v0.3) — SUPERSEDED (v0.4).** In the
German setting a model might infer that only the German applicant speaks German. With
the setting in Arab League countries, no German-language advantage is plausible for
these jobs; the language concern is now the inferred-Arabic channel **C16**, which runs
in the opposite direction (it favours the Arab set over the benchmarks).

**C5. Evaluation awareness and demand characteristics.** Models can often tell
when they are being evaluated (Needham et al. 2025 [needham2025large]); human subjects
respond to perceived study purpose (Orne 1962). Cues here: a lone
`Nationality:` line in a sparse personal-details block; a CV without a name
that nevertheless states nationality; and, above all, the neutrality paragraph,
which names nationality, raises its salience and announces that fairness is at
stake. Effects could go either way: suppressed disparities (a test-mode model
behaves better than in deployment, biasing towards null) or amplified attention
to the attribute. *Severity* M (H for interpreting RQ3 and for any null).
*Mitigation:* constant, conventional personal-details fields so nationality is
one field among several [CR-8]; no fairness language in the baseline;
independent single-candidate calls; forced choice with two *different* CVs
rather than identical CVs; neutrality as a separate condition with λ(m)
measured on `NONE` clones to isolate the paragraph's generic effect.
*Probe:* `mentions_testing` (phrase patterns such as "this is a test", "being
evaluated", "bias test", review M12) and `mentions_nationality` rates under baseline
(pilot P11); disclaimers under neutrality (hand-coded sample). CV dates end 06/2024 so
that "future" dates do not read as synthetic (review L7). Since 2026-10-01 the CVs are
longer (profile, key achievements, fuller job descriptions; D47), so the nationality
line is one field among many, and a nationality field is common on CVs in Gulf labour
markets [VERIFY]. Separating salience from the directive requires a generic
job-relevance instruction that does not name nationality (Parked).

**C6. Implausible origin–occupation–location combinations and missing Arabic.**
In the Arab-world setting: a GCC national (as host or as GCC partner) applying for a
warehouse or retail job, where Gulf private-sector low-skill jobs are mostly held by
expatriates [VERIFY]; a Mauritanian or Comorian who studied at a university in Riyadh
and has worked only in Saudi Arabia; an Arab national who lists no Arabic for a job in an
Arab country. A local career is common for some foreign Arab groups in some base
countries and rare for others [VERIFY], so plausibility varies with the nationality ×
base-country combination. A penalty for implausibility is part of the total effect but
is not status-based stereotyping, and it can masquerade as heterogeneity — e.g.
producing a *negative* wealth gradient in low-skill jobs that works against H1d.
*Severity* M. *Mitigation:* the implied applicant is explicitly a long-term resident of
the base country (design §2.3); H1d is pre-registered as an ecological association,
descriptive of structure (review M9); the host term absorbs the host-specific part.
*Probe:* occupation-specific estimates (R6) and occupation-specific H1d slopes
(exploratory); hand-coded sample includes a "plausibility concern" code.

**C7. Outcome constructs.** `overall_fit` is a model-internal scale, not a
probability; `interview` is generated after, and conditional on, the score;
`confidence` is uncalibrated; `reason` is post-hoc text (it follows the
decisions in autoregressive order); keyword flags have false positives
(e.g. praise of English fluency flagged as a language mention). *Severity* M.
*Mitigation:* pre-specified primary (fit) and secondary (interview) outcomes
[CR-1]; confidence exploratory; flags validated against hand coding; no
mediation claims from reasons. *Probe:* R2; flag–hand-code agreement.

**C8. Principle-probe construct.** Stated endorsement may reflect
alignment-trained boilerplate rather than anything like a belief; acquiescence
inflates agreement; endorsement near 100 % for every model leaves no variance.
*Severity* M. *Mitigation:* ≥ 10 paraphrases, half reverse-keyed; control items
where an attribute should matter; agreement scale as a continuous companion;
fresh contexts; framing as *stated vs revealed* (Hofmann et al. 2024 on overt vs
covert bias; Bai et al. 2025 [bai2025explicitly]). *Probe:* control-item discrimination;
direct vs reverse-keyed agreement.

**C9. Origin-specific associations and training vintage.** Some signals carry
distinctive, time-varying associations: Palestinian (contested statehood; refugee
status in several Arab host countries, and in Jordan a large population of Palestinian
origin, many with Jordanian citizenship [VERIFY]; conflict salience since October
2023), Syrian (war, refugee movements to neighbouring countries incl. Jordan and to
Europe, the December 2024 change of government), Sudanese (war since 2023), Yemeni,
Libyan, Somali. In the Arab-world setting some of these associations are
base-country-specific (e.g. "Palestinian" or "Syrian" in a CV set in Amman), which the
common nationality effect averages over. (The former German-setting note on the
administrative recording of Palestinians in Germany no longer applies.) Models with
different training cut-offs have seen different discourse, so model differences may
partly reflect data vintage. *Severity* M.
*Mitigation:* results framed as signal effects; per-origin results reported
descriptively; training cut-offs recorded from model cards. *Probe:*
exploratory correlation of δ(n) with fragile/conflict status; comparison of
profiles across models with different cut-offs (descriptive).

**C10. The `NONE` control.** Removing a line is a different kind of
manipulation from changing it (length changes; absence may be read as concealment or as
nothing). In the Arab-world setting a CV whose whole career and education are local and
that states no nationality may be read as a **default local (host) applicant**, so
Δ(Ā, NONE) and Δ(DEU, NONE) may partly carry the host effect (η applies only to the
stated host clone, not to NONE). *Severity* L (M for H2d). *Mitigation / probe:*
Δ(DEU, NONE) is reported to show which reading the model takes; NONE is used as
an alternative reference only alongside POL (R9). NONE is excluded from forced
choice [CR-9], where its asymmetry would make nationality the most salient
difference.

**C11. Horn-of-Africa / race confound within the Arab League set (new, review H5,
M9).** SOM, DJI and COM (and SDN, MRT) may evoke sub-Saharan or Black African
associations for a model; they are also among the lowest-income origins, and several
low-income origins are conflict-affected (SYR, PSE, SDN, SOM). A large σ_A or a
positive H1d slope could therefore reflect anti-Black or anti-refugee associations
rather than differentiation among Arab nationalities. No CV lists a native language
(only English C1), which a model may find less surprising for Somali-, French- and
Comorian-speaking origins than for Arabic-speaking ones; in an Arab labour market a model
may also doubt their Arabic (C16), which adds a language channel to the same three
origins. *Severity* H for the headline claim, *residual* M.
*Mitigation:* the RQ1 headline label requires the 22- and the 19-origin analyses to
agree (SAP §5.5); H1d is ecological and carries pre-registered sensitivity slopes with
the World Bank sub-Saharan indicator (COM, MRT, SOM, SDN) (SAP §5.10); σ_A net of
sub-region means (descriptive). *Residual:* SDN and MRT stay in the 19-origin set;
fragile-and-conflict status is not available from the World Bank API, so conflict is
not adjusted for.

**C12. Demonym idiosyncrasy (new, review H5).** The within-CV label permutation rules
out random decoder noise, not systematic reactions to any demonym string (token
rarity, multi-token words, unusual forms such as "Comorian" or "Djiboutian"). Without
a floor, "within-Arab heterogeneity" cannot be distinguished from "LLMs react to
demonyms". *Severity* H for the novelty claim, *residual* M. *Mitigation:* 8 placebo
nationality signals chosen by a pre-specified rule (incl. rare demonyms and two
Muslim-majority states) and the secondary comparison H1e σ_A − σ_placebo (SAP §5.8).
*Residual:* σ_placebo rests on 8 labels; H1e can show whether the Arab spread exceeds
generic label spread, not why; some placebo labels carry setting-specific associations
in the Gulf (C18).

**C14. Host-national status and nationalisation-policy priors (new, v0.4).** In every
CV exactly one Arab clone is a citizen of the CV's base country. Several base countries
run nationalisation policies that favour citizens in parts of private-sector hiring
(Emiratisation, Saudisation / Nitaqat, Omanisation, Kuwaitisation, Qatarisation,
Bahrainisation; Jordan and Egypt restrict some occupations or quotas for foreign
workers) [VERIFY all, no matrix source]. A model that knows this may "legitimately", in
the sense of reproducing law or policy, prefer host nationals; whether such a preference
counts as bias is a normative question the design does not settle. *Effect on
estimands:* without adjustment the host bonus is credited to the eight host-eligible
nationalities (δ̂(n) off by +0.08η for them and −0.045η for the other 14; σ_A inflated by
≈ 0.06η; Δ(Ā, b) shifted by η/22; SAP §4a). *Severity* H for RQ1 and RQ2 if unadjusted,
*residual* L–M. *Mitigation:* all clones kept; primary estimates include a common host
fixed effect η (SAP §4a; D46); η reported separately, descriptively, never as a
confirmatory or "discrimination" finding; HX (host clones excluded) required for the
"robust" label in both origin sets; forced choice with a host term and a host-free
sensitivity. *Residual:* the adjustment assumes one host effect for all origins,
occupations and countries (S12); nationalisation rules differ by country and occupation
[VERIFY], so the true host bonus is probably not common. *Probe:* HX vs adjusted δ(n)
side by side (`host_sensitivity_deltas.csv`); `mentions_nationality` and hand-coded
reasons that cite local-hiring rules (exploratory).

**C15. GCC nationals' right to work across the GCC vs the constant authorisation line
(new, v0.4).** Every CV states "Authorized to work in <the country>; no visa sponsorship
required" for every clone. In reality GCC nationals can, in principle, work in other GCC
states with near-national treatment [VERIFY], so in the 36 CVs set in GCC states the five
other GCC nationalities are **quasi-host** applicants, a second tier of congruence that
`host_national` does not mark. For each GCC origin, 30 of its 42 non-host CVs are in
another GCC state (12 in JOR or EGY). *Effect on estimands:* a GCC-partner bonus is
absorbed into τ(n) of the six GCC origins; it raises their δ(n), adds a GCC-shaped
component to σ_A (22 and 19; all six are uncontested), shows up as gcc sub-region
structure, and is collinear with the top of the income distribution in H1d (the six GCC
states are the six high-income origins; D27). *Severity* M for RQ1 structure and H1d,
L for the omnibus existence question. *Mitigation (partial):* the authorisation line
closes the legal channel on the record; σ_A,net (net of sub-region means) removes a
common GCC shift from the spread; interpretation fixed in advance (a GCC-shaped δ
profile is not read as status → competence). *Open (design_decisions §2 item 11):* a
pre-registered GCC-partner indicator (identified from GCC nationals in JOR/EGY vs other
GCC CVs) or a σ_A on the 12 JOR/EGY CVs; low precision either way.

**C16. Inferred-Arabic language channel (new, v0.4; supersedes C13).** Every CV lists
only `English (C1)` and every ad requires only English. A model may nevertheless assume
that an Arab national speaks Arabic, an asset in Arab labour markets (customer contact,
dealings with authorities, local clients), while a German, Polish, Turkish or placebo
national may not. *Effect on estimands:* Ā-vs-benchmark contrasts (H2a–c, H3b) can carry
an Arab advantage that is part of the total effect of the signal but not origin
preference as such (the opposite direction of the former C13). Within the Arab set the
channel is roughly constant, except for origins whose Arabic a model may doubt (SOM, DJI,
COM; to a lesser extent MRT, SDN), which would add to σ_A in the 22-origin set and to
H1e "exceeds". Placebo labels are all plausibly non-Arabic-speaking, so σ_placebo is not
inflated by this channel. *Severity* M for H2a–c, H3b and the 22-origin σ_A; L for the
19-origin σ_A. *Mitigation / probe:* the RQ1 headline needs the 19-origin analysis (R1);
Δ(Ā, NONE) as an alternative reference (R9) is largely free of this channel if NONE is
read as a local applicant (C10), though it then carries a host-like component;
occupation-specific estimates (R6; the channel should be larger in customer-facing
retail, admin and consulting); `mentions_language` and the hand-coded sample (an
Arabic-skills concern is unsupported by the ads); scope statement that Arabic was
neither required nor listed. A version with Arabic listed for everyone is Parked.

**C17. Western-expatriate premium for the DEU benchmark (new, v0.4).** DEU is the
reference level for benchmark contrasts and is now a Western-European expatriate. Gulf
labour markets are described as having nationality-based pay and status hierarchies with
Western expatriates near the top [VERIFY, no matrix source]; LLMs favour
Western-associated entities in Arabic contexts (`naous2024beer`, LLM, abstract level). A
negative Δ(Ā, DEU) may therefore reflect a Western premium rather than an Arab penalty,
and a DEU–POL gap may separate "Western" from "European". *Severity* M for H2a and H3b,
L for RQ1 (the within-Arab estimands do not use DEU). *Mitigation / probe:* RQ1 is
referenced to the Arab mean; POL, TUR and NONE as alternative references (R9; H2b–d);
per-origin Δ(n, POL) next to Δ(n, DEU) (exploratory); interpretation fixed in advance
(Δ(Ā, DEU) = Arab foreign national vs Western-European expatriate). The benchmark roles
themselves are an open decision (design_decisions D19, §2 item 10).

**C18. Setting-specific associations of placebo labels (new, v0.4).** The placebo set
(URY, BOL, SYC, MWI, MDV, NPL, MYS, KHM) was chosen by a rule fixed for a German
setting. In Gulf labour markets some of these labels are tied to large labour-migrant
groups — "Nepalese" most clearly [VERIFY] — and may be evaluated very differently from
the rest. *Effect on estimands:* σ_placebo can be inflated by one or two labels, which
makes "Arab spread exceeds placebo spread" (H1e) harder to reach and the floor less
"generic". *Severity* M for H1e, L otherwise. *Mitigation:* the set is pre-registered and
not changed after data; per-placebo deviations reported descriptively (exploratory).
*Open (design_decisions §2 item 14):* pre-register a leave-one-out σ_placebo before
Stage A, or accept the floor as it is and state the limitation.

---

## S. Statistical-conclusion validity

**S1. Pseudo-replication.** Counting replicates (or wordings) as independent
candidates inflates N and ignores CV × nationality variance (Hurlbert 1984;
Clark 1973; Judd, Westfall & Kenny 2012). *Severity* H, *residual* L.
*Mitigation:* base CV is the unit; replicates averaged within stimulus;
clustering or bootstrap over base CVs; the permutation test for H1a permutes
labels within base CV (design §1.5).

**S2. Ceiling and floor.** If every strong CV scores near the top and every
borderline CV is rejected, nationality cannot move the outcome.
*Severity* M, *residual* L. *Mitigation:* three tiers with a validator-enforced rubric
(review H2): borderline CVs are 12–18 months short of the ad's minimum, have one
unrelated earlier job, and less total experience than every adequate CV; retail and
warehouse ads require 2 years; pilot P3 (per tier, review L6) / P4 targets and
revision rule; the estimand's tier mix is fixed in advance. *Probe:* R7 (tier-specific
estimates); blind two-coder tier check (not yet run).

**S3. Heaping and discreteness.** LLM scores tend to concentrate on round
numbers (to be checked in the pilot). Mean contrasts stay unbiased, but
information is coarse and ties are frequent, which also matters for RQ4.
*Severity* L–M. *Probe:* R8 (within-CV rank or standardised outcome); tie rate
reported.

**S4. Temperature and sampling.** At T = 0.7 the estimand is the mean of the
sampling distribution; at T = 0 it is the mode, which can jump discretely
between clones. Model-card recommended settings differ between families; using
them would confound family with decoding. *Severity* M, *residual* L–M.
*Mitigation:* identical T, top_p = 1.0 and no top_k for all models [CR-10];
estimand explicitly conditional on T. *Probe:* R4 (greedy); R10 (logprob-based
interview probability).

**S5. Multiple comparisons across 22+ origins.** 22 origins × models ×
conditions × outcomes yields hundreds of contrasts; some will be "significant"
by chance. *Severity* H, *residual* M. *Mitigation:* a small confirmatory set
(omnibus, equivalence and minimum-effect test per model, each for 22 and 19 origins;
a few secondary contrasts) with Holm;
per-origin deviations as estimation with simultaneous CIs and BH-FDR, labelled
exploratory; partial pooling as a check (Gelman, Hill & Yajima 2012); no named
origin hypotheses (hypotheses §0).

**S6. Shrinkage artefacts and rank instability.** Partial pooling towards
sub-region means can manufacture sub-regional structure; ranks of 22 noisy
estimates are unstable. *Severity* M. *Mitigation:* unpooled estimates are
primary for description; pooled as sensitivity (R13); rank intervals; no claim
that an origin is "most/least favoured" unless its simultaneous CI excludes
the Arab mean.

**S7. Few units at the top levels.** 48 base CVs in the main study (12–18 in
the pilot) and 22 origins for H1d; cluster-robust formulas are unreliable with
few clusters. *Severity* M. *Mitigation:* cluster bootstrap and permutation
inference; pilot treated as descriptive; H1d via meta-regression with known
sampling variances; its ecological character stated.

**S8. Over-powered trivial effects and under-powered nulls.** With many calls,
tiny effects become significant; with few base CVs, equivalence may be
unreachable. *Severity* M, *residual* L–M. *Mitigation:* pre-specified SESOIs and
the four-way decision rule [CR-2]; "meaningful heterogeneity" only via the
minimum-effect test (review M4); N from pilot variance with 80 % upper limits from a
CV bootstrap and ρ_ε = 0 (design §7, review M14); if underpowered, the achieved
minimum detectable effect is reported and SESOIs are not moved. With the new default
SESOI of 1.0 fit point (review H4), equivalence for RQ2/RQ3 contrasts will often be
unreachable and those results will be "inconclusive" — accepted in advance.

**S9. Format comparability in RQ4.** Forced choice cannot tie; coarse scores
tie often. Comparing preference strength across formats is partly mechanical.
*Severity* M (RQ4 only). *Mitigation:* RQ4 exploratory; common Bradley–Terry
scale; tie-free sensitivity always shown (hypotheses RQ4); FC wording variants
Latin-rotated per nationality so that wording is not confounded with nationality
(review M13).

**S10. Sphericity (new, review M3).** The noncentral-F interval and equivalence test for
σ_A assume equal residual variance across nationalities; LLM score distributions may be
heteroscedastic by label (hedging, refusals near a boundary, bimodality). *Severity* M
for any null claim, *residual* L. *Mitigation:* equivalence requires both the
noncentral-F test and a sphericity-free calibrated CV-bootstrap test; per-nationality
residual variances and a Greenhouse–Geisser ε are reported (SAP §5.4).

**S11. Analyst degrees of freedom after seeing data (new, review H1, M11).** Unblinded
pilot output, analysis-time changes to SESOIs or settings, re-parsing with a changed
parser, or attaching arbitrary robustness runs would let results shape the analysis.
*Severity* H, *residual* L. *Mitigation:* blind analysis by default; unblinding real
data requires `config/prereg_freeze.json` matching `preregistration.md`; confirmatory
settings in `config/analysis_settings.csv` with "EXPLORATORY OVERRIDE" stamps and
an unblinding log; parser freeze (`parse --exploratory` otherwise); H1d estimator fixed;
`r4_processed_dir` removed; since SAP v0.4 the unblinding gate also requires the
preregistration, the freeze file and the confirmatory config to be committed at HEAD
and the preregistration to carry no unresolved decision or pin markers; the analysis
config (`analyze --config <file.json>`) cannot redirect the root, confirmatory file or log (review N1). *Residual:* the
near-duplicate threshold is still open.

**S12. One common host-national effect (new, v0.4).** The primary model removes a single
η for all host clones (SAP §4a). If the host bonus differs by origin (e.g. larger for
GCC nationals), by base country (different nationalisation rules), by occupation
(quotas or reserved occupations [VERIFY]) or by tier, the remainder stays in τ(n) of the
eight host-eligible origins. Base country is also unevenly crossed with tier (QAT and
EGY have no strong CVs, OMN and BHR no borderline CVs; D45), so η is a weighted average
with country-specific tier mixes. An origin-specific host bonus is not separable from
τ_n with 8 countries × 6 CVs (SAP §20.3). *Severity* M for the eight host-eligible δ(n)
and for σ_A, *residual* L–M. *Mitigation:* HX needs no host model and is required for the
"robust" label (22 and 19 origins); adjusted and HX δ(n) are reported side by side; a
disagreement between them for the host-eligible origins is the diagnostic. Modelling
host heterogeneity would be a documented deviation.

---

## E. External validity and design-criterion assessments

**E1. The Arab League inclusion criterion.** *Severity* M.

Options considered:

1. *Arab League membership (22 states; current rule).* Public, unambiguous,
   verifiable and state-level, which matches a state-level signal
   (nationality). It coincides with the World Bank "Arab World" aggregate
   (per the contract; to verify), which helps covariate coverage, and it
   requires no analyst judgement. Weaknesses: it is political-institutional;
   it includes members whose Arab identity is contested (Somalia, Djibouti,
   Comoros; some would add Mauritania or Sudan) and excludes Arabic-speaking
   populations in non-member states. Syria's suspension (2011–2023) and
   Palestine's contested statehood (Palestine is itself an Arab League member; its
   recognition by individual states varies [VERIFY]) need documenting, not exclusion.
2. *Arabic as an official language.* Would add Chad (Arabic co-official, not a
   member) and raise judgement calls about working or "special status"
   languages (Eritrea; Israel since 2018 [VERIFY]). Chad's associations in
   model training text are plausibly Sahelian rather than Arab, adding noise
   to the "Arab" set. Less crisp, no gain.
3. *Arab-majority population.* Needs contested ethnic self-identification
   data and analyst judgement, and describes populations, not the state whose
   nationality is signalled.

*Decision:* **keep Arab League membership** as the primary rule; the analysis
excluding the three contested members is now a **co-requirement of the RQ1 headline
label** (19-origin families, review H5; see C11), not only a robustness check (R1); do
not add further sensitivity sets (each extra set is another forking path). Label
the set precisely in all outputs: "nationalities of Arab League member states",
not "Arab applicants" [CR-19].

**E2. Choice and number of benchmarks (rewritten v0.4).** *Severity* M for RQ2, L for
RQ1. In the German setting DEU (host reference), POL (EU, free movement) and TUR
(non-EU, Muslim-majority MENA, largest migrant group in Germany) triangulated host vs
foreign, EU vs non-EU and Arab vs non-Arab MENA. **In the Arab-world setting that logic
no longer holds:** no benchmark is a host national (host status now varies only within
the Arab set, C14), EU membership confers no labour right in Arab League states, and the
host-country history that made TUR informative in Germany is absent. Provisional
reading (D19): DEU = Western-European expatriate (Western premium, C17); POL =
Central-European, Christian-majority, EU expatriate; TUR = non-Arab, Muslim-majority
regional neighbour without Arabic as national language (closest on religion and region,
differs on language, C16). Gaps: no benchmark represents the largest expatriate-origin
groups of Gulf labour markets (South and Southeast Asian) [VERIFY]; no benchmark shares
the refugee association of several Arab signals; all three benchmarks differ from the
Arab set in assumed Arabic (C16). Each additional benchmark costs about 4 % more calls
and no authoring, but adds secondary contrasts and does not serve the primary
contribution. *Recommendation:* re-motivate or replace before Stage A (OPEN DECISION,
design_decisions §2 item 10). The former case for a Ukrainian benchmark
("refugee-associated in Germany") was German-specific and needs a new rationale or
should be dropped [CR-22].

**E3. Occupations.** *Severity* M for occupation-level interpretation, L for the
primary estimand. Theory offers four relevant dimensions: skill level
(statistical discrimination is expected where productivity is hard to observe),
customer contact (customer discrimination; Becker 1957; Holzer & Ihlanfeldt
1998 [holzer1998customer]), trust or fiduciary content (warmth/trustworthiness stereotypes in
the SCM), and "cultural fit" emphasis (hiring as cultural matching in elite
professional services; Rivera 2012). Assessment of the six:

- *software_developer* (high skill, low contact): English is a common working
  language in tech, which makes English prompts most plausible here (in every base
  country).
- *sales_representative* (mid skill, high contact; **replaced**, see decision below):
  customer-discrimination probe, but mid-skill, so skill and contact were not crossed.
- *retail_sales_associate* (low skill, high contact; replacement): customer-contact
  probe at low skill; English-only less plausible in Amman (E10) and the inferred-Arabic
  channel likely largest here (C16); 2-year experience minimum.
- *warehouse_associate* (low, low): in Gulf labour markets such jobs are largely held by
  expatriates [VERIFY], which may make foreign nationals look "typical" (possible
  reverse effects) and GCC nationals atypical (C6); English-only less plausible in Cairo
  (E10).
- *financial_accountant* (mid-high, low, trust): the only trust role; a good
  probe of trustworthiness stereotypes.
- *management_consultant* (high, high, fit): the canonical cultural-matching
  setting; contact and fit are confounded in this one role.
- *administrative_assistant* (mid, mid): a feminised occupation; with no name,
  the model may infer a female applicant (pronoun flag, exploratory).

The set is not a factorial design: no low-skill, high-contact role exists,
consultant confounds contact with fit, and with six occupations no
occupation-level theory can be tested statistically. *Decision (adopted, A12):*
`sales_representative` was replaced by `retail_sales_associate` (low skill, high
contact), covering the four skill × contact corners, keeping accountant (trust) and
admin (mid/mid). The six remain breadth, not a factorial test of occupation theory.
Care or health occupations (where foreign recruitment is common) are Parked.

**E4. English-language prompts for an Arab-world setting (rewritten v0.4).** *Severity*
M. English is a common working language in Gulf private-sector workplaces with large
expatriate workforces [VERIFY], so English screening is realistic for many jobs in the
six GCC base countries, especially software and consulting. Bias estimates can differ
by prompt language: Arabic-language discourse about specific origins differs from
English-language discourse, and under Arabic prompting models may collapse Arab
countries into one cluster (`zahraei2025menavalues`, LLM). *Mitigation:* scope stated
as "English-language screening of applications for jobs in eight Arab League countries
whose only language requirement is English (C1)"; occupation-specific estimates (R6).
The A24 sentence that English applications are welcome is not in the current ads
(design_decisions §3 #9). *Probe:* none within scope; an Arabic-language replication
(Arabic CV, Arabic listed or required) is the top Parked item (it replaces the former
German-language replication).

**E5. Synthetic, text-only, single-step screening.** Real pipelines involve
parsing, ranking many candidates, human review, photos and names. Generated CVs
may be more homogeneous than real ones. *Severity* M. *Mitigation:* scope
statement; CVs with profile, key achievements and fuller job descriptions (D47); a
nationality field, common on CVs in the region [VERIFY]; real local institutions;
stimulus sampling across base CVs.

**E6. Model selection and time.** Results hold for the tested models at the
tested revisions. Open-weight models served locally may differ from deployed
proprietary systems. *Severity* M. *Mitigation:* pinned revisions; ≥ 3 families
at roughly matched size; every claim scoped to the tested open-weight models under
this template (review M17, L9). OPEN DECISION: exact set (all four candidates are now piloted; any dropped after the pilot only by the pre-registered technical rule);
whether budget allows one pinned proprietary API model.

**E7. Implied applicant.** Only applicants who live, were educated and work in the CV's
base country, list English (C1) and no other language, and are authorised to work there
are represented: for the host clone a local citizen, for every other clone a long-term
resident foreign national with local credentials. Recent migrants with foreign
credentials are not represented (cf. Oreopoulos 2011), and nothing is said about how
listed Arabic skills would change the picture. *Severity* L (scope).

**E8. Arab-world labour-market and legal context (rewritten v0.4; formerly
Germany / Mannheim).** The eight base countries differ in nationalisation rules,
sponsorship regimes and anti-discrimination provisions [VERIFY]; the GCC states share a
common labour-mobility framework for their citizens [VERIFY]. The study does not assess
legality (ETHICS.md §4). Results may not transfer to other Arab labour markets or to
non-Arab settings; the design can be re-run with other base countries. (The former
German context — AGG, and the EU AI Act's high-risk classification of recruitment AI —
described the employer side in Mannheim; the EU AI Act remains relevant to the research
team, not to the simulated employers.) *Severity* L (scope).

**E9. Gulf-heavy base set (new, v0.4).** Six of the eight base countries are GCC states
(36 of 48 CVs); Jordan and Egypt are the only non-Gulf settings, and no CV is set in the
Maghreb, Iraq, Syria, Lebanon, Sudan or Yemen. Gulf labour markets are atypical (very
large expatriate shares, sponsorship regimes, nationalisation quotas) [VERIFY], so the
estimates describe nationality signals in a mostly Gulf hiring context. It also shapes
the host structure: the eight host-eligible origins are the six GCC states plus JOR and
EGY, and GCC-partner status (C15) applies in three quarters of the CVs. In the pilot every
country rests on one CV pair (ARE two). *Severity* M (scope; interacts with C15, S12).
*Mitigation:* scope statement (D40); base country absorbed by CV effects; per-country
results only descriptive. *Open (design_decisions §2 item 13):* keep as a scope limit or
re-allocate before the pilot.

**E10. English-only retail and warehouse ads in Cairo and Amman (new, v0.4).** The
Amman retail pair (borderline) and the Cairo warehouse pair (adequate) — both in the
pilot — come with ads that require only "Fluent English (C1 or higher)" and CVs that
list only English. In these labour markets such jobs are typically filled locally and
in Arabic [VERIFY], so the ad and the applicant may read as implausible, more so than in
Dubai or Doha. Implausibility may interact with nationality (e.g. a non-host foreign
national applying for an English-only warehouse job in Cairo) and with C16. *Severity* M
for occupation- and country-level readings, L for RQ1 (CV effects absorb a CV-level
plausibility penalty that is constant across clones). *Mitigation / probe:* scope
statement; R6 (occupation-specific estimates, leave-one-occupation-out); the hand-coded
"plausibility concern" code; P3/P4 per tier in the blind pilot. *Open:* keep, or
re-allocate these pairs before the pilot (design_decisions §2 item 13).
