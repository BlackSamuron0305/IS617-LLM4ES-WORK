# Novelty assessment (stress-tested)

Status: final, 2026-09-30 (three statements about the setting corrected on 2026-10-01,
when the setting moved from Germany to the Arab world; searches not re-run). Internal
analysis. **Not paper prose.** The team words
the contribution itself (AI-usage rule in `CLAUDE.md`). Sources and keys are in
`literature_matrix.csv` and `references.bib`, and the search log is in
`literature_review.md` §1. This file supersedes `lit_parts/L2_novelty_draft.md`.

---

## 1. Tentative claim under test

> Existing LLM hiring audits primarily examine broad race/gender categories, while
> Arab/MENA LLM audits focus primarily on stereotypes, cultural alignment, or
> safety. We investigate whether LLM hiring decisions exhibit systematic
> heterogeneity across individual Arab national-origin signals.

Split into three testable parts:

- **C1.** LLM hiring audits mostly vary broad race and gender categories.
- **C2.** Arab/MENA LLM work mostly measures stereotypes, cultural alignment or safety.
- **C3 (the contribution).** No prior study tests, in LLM hiring decisions, whether
  outcomes differ systematically across *individual* Arab national-origin signals.

## 2. Falsification strategy

**Target.** Any study that meets all three conditions:
- (a) an LLM makes a hiring, screening or comparable allocative decision about a person;
- (b) national origin is manipulated;
- (c) the manipulation includes **more than one individual Arab country**.

**Near-misses recorded:**
- LLM hiring audits with one pooled "Arab" group;
- Arab countries appearing in non-hiring decisions or advice;
- many countries appearing in non-decision tasks;
- human studies with many origins.

**Decision rule.**
- C3 is **falsified** if one study meets (a)+(b)+(c).
- C3 is **weakened** if a study meets (b)+(c) in a closely related allocative task, or meets (a)+(b) with a pooled Arab group.

**Coverage.** Searches ran 2026-09-29 and 2026-09-30, in English, German and a small Arabic check.
- arXiv API: about 49 field queries and about 100 ID lookups.
- OpenAlex: 22 searches, 5 of them boolean title/abstract filters.
- General web: about 65 queries, including 4 in Arabic and 7 in German.
- Semantic Scholar: only 6 of 23 queries answered, because of rate limits.
- Crossref: used to verify every entry.
- ACL Anthology pages.
- Full texts of the closest threats: Lippens 2024, Mao & Zhao 2025, MENAValues, Salinas 2023, Forcada Rodríguez 2025, Huijzer & Chen 2025, Venkit 2023.

**Not covered:**
- Google Scholar;
- most of Semantic Scholar;
- Arabic bibliographic databases;
- issue-by-issue browsing of FAccT, AIES and EMNLP 2026;
- SSRN except through a web engine;
- paywalled full texts (Bilon 2025).

Every query in every pass returned **0** studies meeting (a)+(b)+(c).

## 3. Closest prior work

Ranked by closeness to our exact experiment. HUMAN rows are analogues, not LLM evidence.

| # | Study (key, verification) | What it does | What it does not do | Threat |
|---|---|---|---|---|
| 1 | Lippens 2024 (`lippens2024computer`, fulltext) | GPT-3.5 CV-screening correspondence audit in Flanders; 34,560 vacancy–CV combinations; 9 name-signalled groups including **one pooled "Arab"** group and Turkish. Arab −1.41 points, discrimination ratio 0.85 | Does not disaggregate Arab; uses names, not a nationality field (nationality fixed as "Belgian"); one model; Dutch/Flemish frame; no mitigation or principle probe | **Medium**: pre-empts "LLMs penalise Arab applicants" |
| 2 | Hoffmann et al. 2026 (`hoffmann2026evaluating`, fulltext) | Gemini 2.0 Flash rates freelancer–project fit on a European freelance marketplace (French prompts; 172,800 profile–brief pairs); first names signal European male, European female and **one pooled "Arabic male"** group. Average Arabic-name effect about zero (+0.001, not significant); small baseline penalty with different weights on experience and reputation | Pooled Arab group (names, one gender); no nationality field; one model; freelance fit rather than employee hiring; no within-Arab estimand | Low: a second pooled-Arab LLM hiring study, which strengthens the "prior work pools Arab" point |
| 3 | Mao & Zhao 2025 (`mao2025gatekeepers`, fulltext) | GPT-3.5/4 US immigration-admission choice experiment; 10 origins including **Iraq, Sudan, Somalia**; most origin coefficients not significant; interviews show origin-based reasoning despite stated neutrality | Not hiring; only 3 Arab League levels (Somalia contested); no within-Arab estimand; no CV clones; preprint | **Medium**: the nearest (b)+(c) case, in immigration |
| 4 | Zahraei et al. 2025, MENAValues v2 (`zahraei2025menavalues`, fulltext) | Value alignment against survey data for **14 Arab League states** plus Iran and Turkey; country-level inequity; Arab countries **collapsed into one cluster** under Arabic prompts | Values and knowledge, not decisions about people; no qualifications held fixed | **Medium**: pre-empts "within-Arab heterogeneity" as a general claim |
| 5 | Keleg 2025 (`keleg2025arabs`, abstract) | Position paper: the "Arabs share one culture" assumption is invalid yet built into LLM work | No experiment | Low: the critique itself is not ours |
| 6 | Salinas et al. 2023 (`salinas2023unequal`, fulltext) | Job recommendations and salaries for 20 explicit nationalities plus a no-nationality baseline | Only one Arab country (Jordan); advice, not screening; US frame | Low |
| 7 | Nakano et al. 2024 (`nakano2024nigerian`, fulltext) | GPT-4 selects a six-person team from 3,657 GitHub profiles in 4 countries (US, India, Nigeria, Poland); the **location string is swapped** counterfactually; regional preferences persist after the swap (ICSME 2024) | No Arab country; real profiles rather than fixed CVs; one model; no heterogeneity estimand | Low: precedent for a one-string country swap in LLM recruitment |
| 8 | Forcada Rodríguez et al. 2025 (`forcada2025colombian`, fulltext) | Occupation recommendations for 25 countries including **Morocco and Saudi Arabia**; German among the prompt languages | Two Arab countries; no screening; no fixed qualifications; no Arab estimand | Low |
| 9 | Huijzer & Chen 2025 (`huijzer2025discrimination`, fulltext) | Tamkin-style decisions in Dutch and English with a Moroccan background among others; mitigation instructions (best: −27% max–min gap) | One Arab origin; generic decisions; no heterogeneity estimand | Low |
| 10 | Bilon 2025 (`bilon2025sociodemographic`, abstract) | ChatGPT hiring scores, 24,000 evaluations, with a national-origin factor | Abstract reports only **U.S. vs non-U.S.**; country levels **unverified** (full text 403) | Low, **unresolved** |
| 11 | Busetta et al. 2025 (`busetta2025artificial`, abstract) | Vignette hiring experiment across 6 LLMs; sex, ethnicity, education, age | No nationality factor per the abstract; ethnicity levels not stated | Low |
| 12 | Leyva-Vazquez & Smarandache 2026 (`leyvavazquez2026prestige`, abstract) | Candidate evaluations with name origin, institution prestige and a 2-level country factor | Two countries, none Arab | Low |
| 13 | MIRAGE 2026 (`mohammad2026mirage`, abstract) | Muslim vs matched non-Muslim cases in agentic decisions including hiring screens (9–22 pp asymmetry) | Religion, not national origin; no Arab-country levels | Low |
| 14 | Venkit et al. 2023 (`venkit2023nationality`, fulltext) | GPT-2 stories for 193 demonyms; Libya, Sudan and Tunisia among the five most negative | Generation sentiment only; old model | Low |
| 15 | Sakunkoo & Sakunkoo 2025 (`sakunkoo2025thrones`, abstract) | Disaggregates "Asian" in LLM status rankings | Different group and task; shows the disaggregation logic is established | Low |
| 16 | Tamkin et al. 2023 (`tamkin2023evaluating`, fulltext) | The template for RQ3: "Illegal / Ignore demographics" instructions cut discrimination to near zero | No nationality; no within-group dispersion | Low (RQ3 only) |
| H1 | Di Stasio & de Vries 2024 (`distasio2024same`, abstract), **HUMAN** | 22 origin countries of Muslim applicants; origin-country authoritarianism and gender inequality predict lower callbacks (men) | Human employers, names | Framing: within-origin heterogeneity is an established **human** question |
| H2 | Koopmans, Veit & Yemane 2019 (`koopmans2019taste`, fulltext), **HUMAN** | 35 origin groups in Germany; Iraqi and Moroccan applicants below Turkish; cultural distance explains the differences | Human employers; groups other than German and Turkish "around n = 100" each (verified in the full text) | Framing, as above |

## 4. Verdict (conservative)

- **C3 is not falsified.** Within the coverage above (arXiv, OpenAlex, a general web engine in English and German with a small Arabic check, ACL Anthology, Crossref and partial Semantic Scholar, searched 2026-09-29/30):
  - we found **no controlled LLM hiring or CV-screening experiment that varies national origin across more than one individual Arab country**;
  - we found **none that estimates heterogeneity among Arab national origins in any LLM decision about individuals**.
  - This is absence of evidence under the stated coverage, not proof of absence.
  - The only unresolved candidate is Bilon 2025, whose abstract describes a U.S. vs non-U.S. contrast. A second full-text retry (Unpaywall, Semantic Scholar, Crossref, CORE, web, publisher, author site) found no open copy.
  - Two near-misses raised by the adversarial review were checked in full text and do not change the verdict: Hoffmann et al. 2026 pools Arabic-sounding names into one group, and Nakano et al. 2024 swaps location strings across four non-Arab countries.
- **C1 is supported, but overstated as written.**
  - Across 189 bias papers, 79.9% study gender and 13.2% nationality (`ghosh2025bias`; not hiring-specific).
  - In hiring audits, when national origin appears it is pooled (Lippens; Hoffmann, Arabic-sounding names), two-level (ABLEIST: US/India; Rao: UK/India; Leyva-Vazquez: two countries), four non-Arab countries (Nakano: US, India, Nigeria, Poland), or U.S. vs non-U.S. (Bilon, per the abstract).
  - Safer version: "LLM hiring audits mostly vary gender and race; when national origin appears, it is a pooled regional or ethnic category or a handful of countries."
- **C2 is supported, with one qualification.** Saeed 2024 and 2026, Naous, ArGAN, Abid, Elsafoury, Shahid and MIRAGE are stereotype, safety or discourse studies. However, MENAValues and Elsafoury **do** resolve individual Arab countries. The accurate contrast is therefore "not in allocative decisions about individuals with qualifications held fixed", **not** "never at country level".

## 5. Strongest current novelty claim (one sentence; content for the team to phrase)

Within our search coverage, no prior study has tested, in controlled LLM hiring
decisions with qualifications held fixed, whether evaluations differ systematically
across individual Arab national-origin signals. This audit does so for all 22 Arab
League nationalities, using an explicit nationality field on CVs set in eight Arab League
countries (host-national status adjusted for), against a pre-registered noise floor and a
placebo-nationality reference, across several open-weight model families. (Until
2026-10-01 this read "German-style nationality field"; the setting is now the Arab world.)

**What is explicitly not claimed as new:**
- that LLMs penalise Arab applicants (Lippens; Saeed);
- that LLMs treat Arab countries differently in general (MENAValues; Keleg);
- that within-origin heterogeneity exists in hiring (a human finding: Di Stasio & de Vries; Koopmans et al.);
- LLM hiring bias as such;
- explicit-field vs name effects (Tamkin; Rozado);
- position bias;
- the principle–behaviour gap (see §8).

## 6. Strongest threat

**The "predictable combination plus noise" critique.** A Q&A reviewer can argue as follows:
- Lippens 2024 already shows a pooled Arab penalty in LLM screening.
- MENAValues already shows that LLMs differentiate Arab countries.
- Therefore "LLM hiring treats Arab countries differently" is the expected combination of known results.
- And with 22 levels sampled at T = 0.7, *some* between-country spread is guaranteed.

`chen2026competence` sharpens the point: competence-preserving presentation changes alone flip 29.6–41.4% of pairwise LLM screening decisions. If "systematic heterogeneity" is not defined against a pre-registered noise floor, the contribution collapses into a replication of Lippens plus noise.

**Second, literature-level threat.** An unseen study already varies several Arab nationalities in LLM screening. Candidates for this:
- the full text of Bilon 2025;
- a 2026 preprint posted after our searches;
- Arabic-language work that was not searched.

## 7. Smallest changes if a threat materialises (no new factors)

| Threat scenario | Smallest change |
|---|---|
| **Heterogeneity is questioned as trivial** (the main threat) | **Now adopted; see §7a.** Originally proposed: make it a pre-registered estimand: the SD of the within-Arab nationality random effect, compared with (a) a label-permutation null and/or (b) the dispersion across replicate reference clones or placebo one-line changes, and judged against the SESOI (A2). Add one test of whether the pooled Arab estimate misrepresents countries, e.g. country effects of opposite sign to the pool, or exceeding it by a pre-set margin. The data are already collected; only the analysis plan changes. Placebo clones (parked in design §10) would be the one cheap stimulus addition. |
| **Dispersion does not exceed the floor** | Report a bounded null with equivalence tests: "LLM hiring decisions do not differentiate individual Arab origins beyond noise; the pooled category is adequate here". This is informative, and consistent with MENAValues' collapse finding at the decision level. Needs the pre-registered SESOI and the positive control (A7) to be defensible. |
| **A prior study varying several Arab nationalities in LLM screening turns up** (e.g. the Bilon full text) | Reframe as a (i) pre-registered, multi-model, open-weight replication-and-extension (ii) in an Arab-world setting (CVs and jobs in eight Arab League countries) with an explicit nationality field, host-national status adjusted for so that citizenship is held constant among the compared Arab clones (all foreign nationals of the CV's country; GCC partners aside). Move weight to the two secondary angles we found no precedent for: (iii) whether the neutrality instruction **compresses between-country dispersion**, not just the mean (H3a; Tamkin and Huijzer report means or max–min gaps only), and (iv) whether dispersion depends on response format, independent evaluation vs forced choice (RQ4). No new factor needed. |
| **The combination critique lands in Q&A** | Framing only. Stress (1) decisions about individuals with qualifications fixed, not values; (2) a counterfactual clone design with the positive control as a yardstick; (3) heterogeneity defined against the noise floor; (4) the within-Arab contrast, net of the host-national adjustment, holds the non-citizenship signal constant, which an Arab-vs-majority contrast in Lippens-type designs cannot. |
| **The human precedent is raised** (Di Stasio & de Vries; Koopmans) | Framing: the question is whether LLMs reproduce, flatten or reorder human origin hierarchies. H1d (status gradient) is an LLM-specific test of a known human pattern, not a new idea. |

## 7a. Planned defence against the "Lippens + MENAValues + noise" objection

Adopted by the lead after the adversarial review (H5, 2026-09-30). This is design
content for the team to phrase themselves.

The defence rests on three pre-registered elements. None adds a new experimental
factor: all run under the baseline independent evaluation.

1. **A debiased heterogeneity estimator with a permutation noise floor.**
   - σ_A is estimated with the debiased moment estimator in D25, which removes the spread that estimation noise alone would produce.
   - It is tested with a within-CV label permutation, which gives the decoder-noise floor.
   - This answers the objection that "some spread is guaranteed at T = 0.7".
2. **8 placebo nationality signals** (`stimuli/nationalities.csv`, group `placebo`: Uruguayan, Bolivian, Seychellois, Malawian, Maldivian, Nepalese, Malaysian, Cambodian).
   - They are chosen by a rule fixed before any data: outside the Arab League, MENA, Europe and the benchmark set; 2 from each of 4 World Bank regions; an income spread close to the Arab set's; rare demonyms included; 2 Muslim-majority states.
   - A pre-registered comparison of σ_A with σ_placebo asks whether the spread among Arab labels exceeds the spread among *any* comparably diverse labels.
   - This answers "LLMs just react to demonyms" (cf. `venkit2023nationality`, `salinas2023unequal`). The permutation floor cannot rule out systematic idiosyncratic responses to rare or multi-token demonyms; the placebo set can.
3. **The 19-origin σ_A as a co-requirement for the headline claim.**
   - The claim of systematic within-Arab heterogeneity is made only if it holds for all 22 origins and for the 19 excluding Somalia, Djibouti and Comoros.
   - This guards against the spread being driven by associations with the Horn of Africa, race or conflict rather than by differentiation among Arab nationalities.

Against Lippens (pooled) and MENAValues (values, not decisions), the headline then
becomes a pre-registered statement: in hiring decisions with qualifications held
fixed, spread among Arab national-origin signals does, or does not, exceed both
decoder noise and generic nationality-label spread, and survives excluding the
contested members.

A null is also a defensible, informative result, given the positive control (A7) and
the SESOI (A2).

## 8. Status of the principle–behaviour idea

**Not a novel concept.** It is a crowded, named family:

| Construct | Source (key) |
|---|---|
| Stated vs revealed preferences ("preference deviation") | Gu et al. 2025 (`gu2025alignment`) |
| Value–action gap | Shen et al. 2025, EMNLP (`shen2025value`) |
| Explicitly unbiased, implicitly biased; relative evaluations more diagnostic | Bai et al. 2025, PNAS (`bai2025explicitly`) |
| Overt vs covert prejudice driving decisions | Hofmann et al. 2024, Nature (`hofmann2024dialect`) |
| For **nationality**: implied exchange rates value lives unequally by country, and the model may deny it when asked | Mazeika et al. 2025 (`mazeika2025utility`) |
| Related: veneer of fairness, task-dependent stereotyping, unverbalized bias, "Said-washing", origin-based reasoning despite stated neutrality | `gupta2024bias`, `kumar2026redirected`, `arcuschin2026blind`, `shahid2026orientalism`, `mao2025gatekeepers` |

**What remains defensible** is a narrow *application*:
- pair each model's stated endorsement of non-discrimination (principle probe, per occupation context, with control and reverse-keyed items; A11)
- with the same model's measured nationality effects in that occupation.

Present it as an instance of stated-vs-revealed comparison (cite Gu, Shen, Bai, Hofmann, and Mazeika for nationality) applied to non-discrimination in hiring.

**No new "index" or measure should be claimed as a contribution.** A "principle–behaviour inconsistency index" would be a relabel of existing constructs and is likely to be challenged in Q&A. The four-way classification in `hypotheses.md` (SQ1) is a reporting device, not a contribution.

## 9. Checks still open before the 13.10 pitch

1. Bilon 2025: obtain the full text through library access and record the national-origin levels. Two retries through open routes failed. It is the only unresolved literature threat.
2. Re-run the 7 Semantic Scholar queries that failed (G1 in `literature_review.md`), or the same phrasings in Google Scholar, from a university network.
3. If time allows, run a short search of an Arabic bibliographic database. Otherwise name "no Arabic-language search" as a coverage limit.
4. Done in the design (see §7a): placebo signals, the σ_A vs σ_placebo comparison, the 19-origin co-requirement and the debiased estimator with a permutation floor. Remaining step: freeze the exact decision rule for "exceeds the placebo spread" in the preregistration before the pilot.
5. Do not cite Törnberg 2026 (arXiv:2603.13891). The author withdrew it over a stimulus-assignment confound.
