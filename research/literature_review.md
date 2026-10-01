# Literature review (internal, structured)

Status: final synthesis of the two literature parts plus a gap-search pass, 2026-09-30.
Internal working document. **Not paper prose**: the team writes the paper and the
presentations themselves (AI-usage rule in `CLAUDE.md`). Do not paste from here.

Companion files:
- `research/literature_matrix.csv`: 125 sources, one row each, with a `strand` column.
- `research/references.bib`: the same 125 keys. `verification` and `strand` are custom
  fields that BibTeX styles ignore, and `annote` holds remarks.
- `research/novelty_assessment.md`: the stress-tested novelty verdict.
- Full search logs from the two parts: `lit_parts/L1_notes.md` and `lit_parts/L2_notes.md`.

**Verification levels.**
- `fulltext`: the relevant sections of the source were read.
- `abstract`: only the abstract (or an official summary page) was read.
- `metadata`: the bibliographic record was confirmed, but the content was not read.

Nothing unverified is in the matrix or the bib. Numbers are quoted only where a
researcher read them in the source. **HUMAN** marks human-subject studies. Their
findings are not LLM findings.

| strand | n | fulltext | abstract | metadata |
|---|---|---|---|---|
| llm_hiring | 27 | 8 | 18 | 1 |
| audit_method | 20 | 3 | 16 | 1 |
| human_audit | 19 | 3 | 15 | 1 |
| arab_mena_llm | 16 | 2 | 14 | 0 |
| nationality_llm | 13 | 5 | 8 | 0 |
| intervention | 8 | 3 | 5 | 0 |
| principle_behaviour | 8 | 1 | 7 | 0 |
| fairness_theory | 14 | 0 | 10 | 4 |
| **total** | **125** | **25** | **93** | **7** |

93 of the 125 sources are at abstract level. Check any claim that goes beyond an
abstract against the full text before it enters the paper.

---

## 1. Search strategy and coverage

### 1.1 Sources, dates, languages

- **Window.** The parts L1 and L2 ran on 2026-09-29 and 2026-09-30. The gap pass ran on 2026-09-30.
- **arXiv API** (field-restricted boolean queries, plus ID lookups for abstracts, comments and withdrawal notices):
  - L1: 18 queries and about 41 ID lookups.
  - L2: 23 queries and about 60 ID lookups.
  - Gap pass: 8 date-sorted queries and ID lookups.
- **OpenAlex:**
  - L1: DOI lookups for abstracts and open-access copies.
  - L2: 5 searches.
  - Gap pass: 12 relevance searches (2024 onwards) and 5 boolean title/abstract filter searches (from June 2023).
- **Semantic Scholar Graph API:** rate-limited throughout. See 1.4.
- **Crossref:** used to verify every DOI, author list, published title and page range. The gap pass also verified the canonical works added to resolve `[VERIFY]` tags.
- **ACL Anthology** abstract pages; **PMLR**; **PLOS**.
- **General web search:**
  - L1: 18 queries.
  - L2: 35 queries.
  - Gap pass: 12 discovery queries (3 English, 3 for Bilon and a salary dataset, 4 Arabic, 2 German), plus verification look-ups.
- **Full-text PDFs:**
  - L1: 15 read.
  - L2: 14 read.
  - Gap pass: re-checked Lippens 2024 and Salinas 2023 to settle the points where the two parts disagreed.
- **Languages:**
  - English throughout.
  - German: L1 used 2 queries, L2 used 3, and the gap pass used 2.
  - Arabic: the gap pass used 4 web queries. It was the first Arabic search.

### 1.2 Query families (union of both parts and the gap pass)

- nationality / national origin / country of origin × hiring / résumé / CV / recruitment / job applicants / candidates × LLM / ChatGPT / language model
- Arab / Middle Eastern / MENA / North African / Gulf / Levant / Maghreb × the same
- individual demonyms: Syrian, Egyptian, Saudi, Emirati, Palestinian, Yemeni, Moroccan, Jordanian, Lebanese, Iraqi, Tunisian, Algerian
- migrant / immigrant / refugee / expatriate / migration background
- within-group, intra-regional, disaggregated, heterogeneity
- method: position bias, order effects, ties, nondeterminism, pseudo-replication, correspondence audit, explicit vs name cues
- interventions: debiasing instruction, self-correction, anti-discrimination prompt
- principle–behaviour: stated vs revealed, value–action, explicit vs implicit, say–do, overt vs covert
- human audits: Arab / Muslim / MENA correspondence tests, Germany, GEMM, meta-analyses
- German: Staatsangehörigkeit, Herkunft, Bewerbung, Diskriminierung, Personalauswahl, Sprachmodell
- Arabic: تحيز النماذج اللغوية الكبيرة التوظيف الجنسية; التحيز ضد العرب في الذكاء الاصطناعي التوظيف; and 2 variants (see 1.3)

### 1.3 Gap-search log (2026-09-30)

"KQ" counts studies in which an LLM makes a hiring or screening decision over **more
than one individual Arab nationality**.

| # | Source | Query / action | Result | New relevant (action) | KQ |
|---|---|---|---|---|---|
| G1 | Semantic Scholar | 10 queries, 2024–2026 (nationality / national origin / country of origin / Arab / Middle Eastern / migrant × hiring / résumé / recruitment × LLM), up to 6 attempts each with growing backoff | **3 of 10 answered** ("country of origin bias large language model job candidates": 3 hits; "Arab names large language model employment bias": 416, top 25 read; "Middle Eastern names resume screening language model": 32); the other 7 got HTTP 429 on every attempt | none new (hits already in the matrix: Bilon, Leyva-Vazquez, Nghiem, Wilson, Tan, Leininger); McKenna & Tshuma 2026 screened (Global South narratives; not added) | 0 |
| G2 | OpenAlex relevance | 12 queries (e.g. "nationality large language model hiring", 6,443 hits; "Arab applicants large language model hiring", 967; "Syrian applicants large language model", 1,714); top 25 each | mostly off-topic | none new (only already-known hiring audits and HUMAN audits) | 0 |
| G3 | OpenAlex boolean filter | `(nationality OR "national origin" OR "country of origin") AND (hiring OR resume OR recruitment OR "job applicants" OR CV) AND (LLM OR ChatGPT OR GPT…)` | 16 | Bilon 2025 abstract found (upgraded to `abstract`); Potipiti 2026 salary dataset (checked: German, Chinese and American only, excluded); Lee & Cheon 2026 SSRN "Does Bias Drift?" (no abstract, SSRN 403, not assessed) | 0 |
| G4 | OpenAlex boolean filter | `(Arab OR "Middle Eastern" OR MENA OR "North African") AND (hiring OR resume OR recruitment OR applicants) AND (LLM…)` | 14 | Lippens 2024 (known); Törnberg 2026 (withdrawn) | 0 |
| G5 | OpenAlex boolean filter | individual demonyms × (hiring OR resume OR applicant) × LLM | 7 | none | 0 |
| G6 | OpenAlex boolean filter | (migrant OR immigrant OR refugee OR "migration background") × (hiring OR resume OR recruitment) × LLM | 10 | MIRAGE (added) | 0 |
| G7 | OpenAlex boolean filter | (nationality OR "national origin") × (discrimination OR bias) × LLM × (employment OR labour OR job) | 16 | none new | 0 |
| G8 | arXiv API, date-sorted | 8 queries (nationality / Arab / national origin / immigrant / demonyms / German × hiring × LLM; within-group; disaggregation). Totals 130, 53, 34, 3, 88, 6, 0, 0; OR-groups match loosely, so all hits were screened by title | – | Eida et al. 2026 (added); Aizaz & Nguyen 2026 (added); Leyva-Vazquez & Smarandache 2026 (added); MIRAGE (added). Screened and not added: Dasanaike 2026 (ethnicity from names), Chun & Elkins 2026, ConsistencyAI | 0 |
| G9 | Web (EN) | "2026 arXiv LLM hiring audit national origin Arab nationalities résumé counterfactual …"; "LLM resume screening bias explicit nationality field many countries 2026 …"; "nationality LLMs hiring bias 2026 preprint Egyptian OR Jordanian OR Lebanese OR Moroccan" | – | Chen & Xiao 2026b (added, audit_method). Screened and excluded as race/gender only: Tung et al. 2026 (SSRN 7370360), Webster 2025/26, Anzenberg et al. 2025, HALF, Peña et al. 2025 | 0 |
| G10 | Web + OpenAlex + author site | Bilon 2025 (3 searches; tandfonline 403; author site lists the paper without a PDF) | abstract obtained | national-origin levels **still unverified**; the abstract reports only U.S. vs non-U.S. | 0 |
| G11 | Crossref + Springer page | Busetta, Campolo & Ficarra 2025 (open item from L2) | abstract obtained | added: sex, ethnicity, education and age across 6 LLMs; **no nationality factor** per the abstract | 0 |
| G12 | Web (AR) | تحيز النماذج اللغوية الكبيرة التوظيف الجنسية; التحيز ضد العرب في الذكاء الاصطناعي التوظيف; تحيز ChatGPT فرز السير الذاتية المتقدمين العرب جنسية دراسة; "النماذج اللغوية" تحيز "الجنسيات العربية" OR "الأصل القومي" توظيف دراسة تجريبية | news and general pages only | none. Alkhaleej (2026-06-30) reports a Stanford study of game-based hiring tools with Asian and Black applicants; muwatin.net covers generic AI hiring bias | 0 |
| G13 | Web (DE) | "KI Bewerbungsauswahl Diskriminierung Staatsangehörigkeit Sprachmodell Studie 2026 syrisch marokkanisch Lebenslauf"; "Large Language Models Personalauswahl Herkunft Diskriminierung Experiment Lebensläufe Nationalität Studie Universität" | news and blogs | none. One ICML 2026 Princeton/UChicago hiring-agent study uses **fictional** groups (per a blog report, not added); AlgorithmWatch/FINDHR covers CV-format effects | 0 |
| G14 | arXiv API + full-text PDFs | adversarial-review leads (L14): arXiv:2601.11379, arXiv:2409.12544 | both exist; full text read | added `hoffmann2026evaluating` (pooled Arabic-name group, freelance fit, Gemini 2.0 Flash) and `nakano2024nigerian` (GitHub location-string swap across US, India, Nigeria, Poland; ICSME 2024) | 0 |
| G15 | Unpaywall, Semantic Scholar, Crossref, CORE, web, tandfonline, author site | Bilon 2025 full-text retry | no open version (Unpaywall: closed; S2: no OA PDF; Crossref: publisher link only; tandfonline 403; no SSRN, OSF or ResearchGate copy found) | levels still unverified | 0 |
| G16 | Full texts (ACL Anthology, EconStor, arXiv) | adversarial-review nuance check (L13): Kamruzzaman 2024, Koopmans 2019, Chen & Xiao 2026a, Lippens 2024 | all four checked | matrix corrected: Kamruzzaman direction-dependent nulls; Koopmans "around n = 100" verified; Chen & Xiao setting inferred, not stated; Lippens comparison with human benchmarks refined | – |

### 1.4 Known gaps in coverage

- **Semantic Scholar.** L1 got HTTP 429 on its only search. L2 got answers to 3 of 12 queries. The gap pass retried 10 queries with backoff and got answers to 3; the other 7 failed on every attempt. **Most of Semantic Scholar is therefore still uncovered.** The unanswered phrasings were covered instead in OpenAlex (G2–G7) and arXiv (G8).
- **Google Scholar** was not accessible.
- **Paywalls (HTTP 403):** tandfonline (Bilon; the JEMS/ERS versions of the GEMM papers), ACM DL, MDPI, ScienceDirect, PeerJ, SSRN, hogrefe and law.mit.edu. Open-access copies were used where they exist (EconStor, UGent, arXiv).
- **Arabic.** Only 4 general-web queries were run. No Arabic bibliographic database or Arabic-language journal index was searched. **Arabic-language scholarship is effectively not covered.**
- **German.** Seven web queries across the three passes. They surfaced news and HUMAN field experiments only. German-language grey literature (e.g. the Antidiskriminierungsstelle reports) was not searched systematically.
- **Venues.** FAccT, AIES, EMNLP 2026 and the ACL 2026 workshops were not browsed issue by issue. SSRN was searched only through the web engine. Preprints and workshop papers from the last few weeks may be missing.
- **Depth.** 93 of the 125 sources are at abstract level. For the papers flagged medium or high threat, the part researchers read the full text (Lippens, MENAValues, Mao & Zhao, Mazeika). Bai, Hofmann, Gu and Shen are abstract-level.

---

## 2. Strands

Each strand ends with **cannot answer** and **implies for us**.

### 2.1 LLM hiring and screening audits (`llm_hiring`, 25)

**What it shows.**
- **The field is large and mostly about US race × gender, signalled by names.** Examples: `an2025measuring` (about 361,000 résumés, five models), `an2024large`, `armstrong2024silicon`, `nghiem2024you` (more than 750,000 prompts), `gaebler2024auditing`, `wen2025faire`, `iso2025evaluating`, `veldanda2023emily`, `wang2024jobfair`, `gao2026can` (14 models).
- **Directions are unstable, and recent models often reverse the human pattern.**
  - `gao2026can`: the one 2023-vintage model is pro-White (+2.12 pp); every model from 2024 onwards shows a null gap or a pro-Black gap (up to −3.01 pp).
  - `gaebler2024auditing` and `an2025measuring` favour women.
  - `rozado2026gender`: female-named candidates are chosen 56.9% of the time in pairs, but isolated ratings show a negligible effect.
  - Group rankings shift across templates (`an2024large`).
- **Only two LLM hiring studies have an explicit Arab group, and both pool it into one name category.**
  - `lippens2024computer`: GPT-3.5, Flemish vacancies, 34,560 vacancy–CV combinations.
    - One pooled Arab name group: −1.41 points (SE 0.21), discrimination ratio 0.85 at a cutoff of 75.
    - Turkish: −1.75. Eastern Europeans carry the largest penalty.
    - The nationality field was fixed as "Belgian".
    - The author's comparison with human audits: the LLM penalty is smaller than human averages for Arabs (0.59 worldwide, 0.79 Belgium), about equal for Turks against Belgian audits (0.86 vs 0.85), and larger for Hispanics and for Black candidates in Belgium.
  - `hoffmann2026evaluating`: Gemini 2.0 Flash, a French-language freelance-marketplace task; European male, European female and "Arabic male" first names.
    - The average Arabic-name effect is about zero (+0.001 points, not significant).
    - Interactions show a small baseline penalty and different weights on experience and reputation.
- **When national origin appears, it is coarse:**
  - `phutane2025ableist`: American vs Indian.
  - `rao2025invisible`: UK vs India.
  - `bilon2025sociodemographic`: U.S. vs non-U.S., per the abstract; the levels are unverified.
  - `leyvavazquez2026prestige`: two countries.
  - `nakano2024nigerian`: GPT-4 team selection from GitHub profiles with the location string swapped; US, India, Nigeria and Poland.
  - `sorokovikova2025surface`: migrant type, not nationality.
  - `geiger2025salary` and `busetta2025artificial`: no nationality factor.
- **German setting:** `leininger2026fairness` (generation leakage, German vs Turkish names; ethnicity leakage weak).
- **Validity problems:**
  - `castleman2026measuring`: models fail to pick the more qualified CV and do not abstain between equals.
  - `pavlopoulos2026minimal`: negligible effects under equivalence testing, with a seniority positive control that confirmed sensitivity.
- **Explicit attribute fields enlarge effects:** `rozado2026gender` (adding a gender field), and see `tamkin2023evaluating`.

**Cannot answer.**
- Whether LLMs treat *individual* Arab national origins differently.
- Whether a pooled "Arab" estimate hides between-country heterogeneity.
- How an explicit nationality line behaves in a German screening task.
- Open-weight model families are rare, the exceptions being `leininger2026fairness` (Qwen3) and `pavlopoulos2026minimal`.

**Implies for us.**
- Use two-sided hypotheses, because reversals are common.
- Keep independent evaluation as the primary arm and forced choice as secondary, and report both, because pairwise and isolated results can disagree.
- Keep the positive control (A7) and equivalence bounds (A2).
- Log model vintage and revision (A6).
- Report both the score and the interview decision (A1).
- Keep Turkish as a benchmark.

### 2.2 Audit methodology (`audit_method`, 20)

**What it shows.**
- **Position bias is large and must be cancelled by design:**
  - `rozado2026gender`: the first-listed candidate is chosen 63.5% of the time (21 of 22 models individually significant).
  - `vohra2026audit`: the first-listed candidate gains 0.11 rank positions, about as much as the largest demographic effect.
  - `yin2026fragile`: order effects depend on quality.
  - `wang2024large` and `zheng2023judging`: position bias in LLM judges generally.
- **The verdict space and audit transparency drive pairwise results:**
  - `chen2026beyond`: forbidding ties gives an apparent selection-rate ratio of 0.39; permitting ties gives 94% or more ties in 7 of 9 models.
  - `vohra2026audit`: models tie every identical-content pair, recognise transparent audits (100% when probed, 89% unprompted), and none of 36 pre-registered contrasts survives correction.
  - `needham2025large`: evaluation awareness, AUC 0.83 for Gemini-2.5-Pro.
- **Noise and instability are substantial:**
  - `atil2024nondeterminism`: accuracy swings of up to 15% at "deterministic" settings.
  - `he2025defeating`: temperature-0 nondeterminism comes from batch-size-dependent numerics.
  - `chen2024chatgpt`: the behaviour of a named service drifts across versions.
  - `sclar2024quantifying`: up to 76 accuracy points from formatting alone.
  - `rottger2024political`: forced and unforced answers differ.
  - `chen2026competence`: competence-preserving presentation changes flip 29.6% of pairwise screening decisions for Llama-3.1-8B and 41.4% for Mistral-7B.
- **Inference with many noisy units:**
  - `miller2024adding`: clustered standard errors can be up to about 3 times naive ones.
  - `hurlbert1984pseudoreplication`: the classic definition of pseudo-replication.
  - `kline2022systemic` and `kline2024discrimination`: false-discovery-rate control and empirical-Bayes grades for many unit effects.
  - `perugini2014safeguard`: conservative sample-size planning.
- **The cue decides the conclusion:**
  - `tonneau2026cues`: different cues for the same group give inconsistent conclusions, even in direction.
  - `bui2025dialects`: an explicit label amplifies bias more than implicit cues.
  - `crabtree2023validated`: names signal class and citizenship, and validated sets exist only for US categories.

**Cannot answer.**
- How large the noise floor is for our stimuli and models.
- Whether a `Nationality:` line on a German-style CV triggers audit recognition.
- There is no LLM-audit method for dispersion across many levels of one attribute. The closest templates are `kline2022systemic` and `kline2024discrimination`, which are human field data.

**Implies for us.**
- Quads (swap nationality and order).
- An unconstrained choice field, with tie and refusal coding pre-registered.
- Different same-tier CVs in each forced-choice pair.
- K = 3 wording variants (A3).
- Pinned revisions and a randomised execution order (A5, A6).
- Base CV × nationality as the unit, with random effects or clustering.
- Empirical-Bayes shrinkage for the 22 effects.
- A pre-registered **noise-floor test** for "heterogeneity" (see §4, row 8).
- A `mentions_testing` flag (A18).
- Claims scoped to the explicit-field cue.

### 2.3 Human correspondence audits (`human_audit`, 19) — all HUMAN

**What it shows.**
- **The largest human ethnic penalty falls on the pooled Arab/Maghrebi/Middle Eastern group:** `lippens2023state`, discrimination ratio 0.5937 [0.5548, 0.6353], about 41% lower callback odds. Western Asian: 0.7508.
- **Germany:**
  - `koopmans2019taste`: callbacks 60% for German-origin applicants vs 47% for Turkish-origin; Iraqi and Moroccan applicants fall below Turkish; Albanian is lowest at 41%; cultural value distance explains group differences better than group education.
  - `kaas2012ethnic`: about 14% more callbacks for German names; the gap disappears with favourable reference letters.
  - `weichselbaumer2020multiple`: a headscarf adds a penalty.
- **Many origins:**
  - `distasio2021muslim`: a "Muslim by default" penalty in 4 of 5 countries.
  - `distasio2024same`: across 22 origin countries, authoritarianism and gender inequality in the origin country predict lower callbacks, for men only.
  - `lancee2021ethnic`: the GEMM design.
  - `distasio2020understanding`: the case for multi-group designs.
  - `thijssen2022discrimination`: similar penalties for Muslim groups across countries.
- **Pooled Arab-name audits** (the pooling we take apart):
  - `carlsson2007evidence`: every fourth employer discriminates.
  - `arai2016reverse`: Arabic-named men are penalised more than women.
  - `blommaert2014discrimination`: Dutch-named applicants are 60% more likely to get a positive reaction.
  - `adida2010identifying`: a religion contrast.
  - `bartkoski2018meta`: "Arab" targets draw more discrimination than "Muslim" targets, and primary studies conflate the two.
- **Citizenship:** `quillian2026racialized` finds that lacking citizenship or holding a foreign degree carries large penalties, while place of birth has little independent effect.
- **Country context:** `quillian2019countries` places Germany among the lower-discrimination countries.
- **Policy context:** `krause2012anonymous` (anonymous applications, including the German field experiment).

**Cannot answer.**
- Anything about LLMs. Human effect sizes are not a benchmark that LLMs "should" match.
- Human studies signal origin through names, language, photos or religion, not through an explicit nationality line on a CV with a work-authorisation line.
- In the German GEMM arm, groups other than German and Turkish had "around n = 100" applications each (verified in `koopmans2019taste`), so origin-level human estimates are noisy.

**Implies for us.**
- **Within-origin heterogeneity is an established human question.** Our contribution must be framed as LLM-specific.
- `distasio2024same` and `koopmans2019taste` supply *exploratory* moderators (authoritarianism, gender inequality, cultural distance). They also show that origin-country characteristics matter in humans, so **our status gradient (H1d) must be framed as a test of whether LLMs show such a structure, not as a new idea.**
- **A nationality line also signals non-citizenship** (`quillian2026racialized`):
  - Arab-vs-German contrasts mix origin with citizenship.
  - Within-Arab contrasts hold the non-EU citizenship signal constant.
  - Polish is the EU-foreign benchmark.
  - The work-authorisation line fixes legal status on the record, but not the signal.
- **"Muslim by default"** (`distasio2021muslim`): religion is part of the total effect, and mechanism claims stay exploratory.
- `kaas2012ethnic` predicts smaller effects for strong-tier CVs. Keep the tier × nationality check.

### 2.4 Arab / MENA / Muslim bias in LLMs (`arab_mena_llm`, 16)

**What it shows.**
- **Pooled anti-Arab and anti-Muslim bias is well established in generation and red-teaming:**
  - `saeed2024desert`: negative bias toward Arabs in 79% of cases.
  - `saeed2026surfacing`: Arabs cast in terrorism and religion roles in 89% or more of cases.
  - `abid2021persistent`: Muslim–violence association; positive adjectives cut violent completions from 66% to 20%.
  - `aly2025argan`: Arabs and Egyptians among the most negative targets in Modern Standard Arabic prompts.
  - `shahid2026orientalism`: "Said-washing", where a model disclaims generalising and then reproduces the structure it disclaimed.
  - `mohammad2026mirage`: a 9–22 pp asymmetry in agentic decisions (including hiring screens) for Muslim vs matched non-Muslim cases. Prompt mitigations fix completions but not decisions.
- **Culture and values:**
  - `naous2024beer`: Western defaults in Arabic contexts.
  - `zahraei2025menavalues`: 14 Arab League states plus Iran and Turkey. Algeria is worst served and Palestine best, about a 19.8% gap. Under Arabic prompts, models **collapse Arab countries into one cluster**.
  - `almheiri2025crosscultural`: commonsense reasoning transfers across Arab countries.
  - `keleg2025arabs`: a position paper arguing that Arabs are not one culture.
- **Within-Arab variation in other constructs:**
  - `elsafoury2025outofsight`: more measured bias in Egyptian Arabic than in Modern Standard Arabic.
  - `eida2026dialects`: bias against Sa'idi vs Cairene Egyptian Arabic.
- **Palestinian signal:** `aizaz2026persona` finds war and low-status associations, and fairness instructions leave the status distinctions in place.
- **Thin mitigation evidence:** `asseri2025prompt` found 8 studies, none in hiring.
- **Arabic-developed models:** `sengupta2023jais` and `bari2024allam` (a parked extension).

**Cannot answer.**
- Allocative decisions about individuals with qualifications held fixed.
- Any hiring decision compared across several Arab national origins.

**Implies for us.**
- A pooled Arab-vs-German penalty would be a replication, not the contribution.
- `zahraei2025menavalues` and `keleg2025arabs` pre-empt "within-Arab heterogeneity" as a general claim. **The novelty is limited to hiring decisions with qualifications held fixed.**
- Conflict and religion are the likely channels. Keep them as exploratory text flags, and treat training vintage as a threat for Palestinian, Syrian and Sudanese signals (C9).
- Never list Arabic. Keep English CVs, which the job ads accept (A24).

### 2.5 Nationality and country-of-origin bias in LLMs (`nationality_llm`, 13)

**What it shows.**
- **Nationality is under-studied:** `ghosh2025bias` finds nationality in 13.2% of 189 bias papers, against 79.9% for gender.
- **Many-country studies measure generation or perception, not decisions:**
  - `venkit2023nationality`: 193 demonyms; the five most negative include Libya, Sudan and Tunisia.
  - `manvi2024geographic`: lower-SES places are rated lower.
  - Also `zhu2024quite`, `kamruzzaman2024nation`, `jha2023seegull`, `nguyen2026representational` and `pelosio2025obscured`.
  - `kamruzzaman2024subtler` (full text): the nationality association depends on the probe direction. From group to attribute it is null for 2 of 4 models (GPT-4, Llama-2); from attribute to group it is significant for all 4.
- **Decisions or advice with several countries:**
  - `salinas2023unequal`: 20 nationalities with Jordan the only Arab country; **the no-nationality baseline was itself an outlier**.
  - `forcada2025colombian`: 25 countries including Morocco and Saudi Arabia; German among the prompt languages.
  - `mao2025gatekeepers`: a US immigration-admission choice experiment with Iraq, Sudan and Somalia. Most country coefficients are not significant, yet the models reason by origin when interviewed.
- **Disaggregation logic:** `sakunkoo2025thrones` splits "Asian" into subgroups.

**Cannot answer.** Hiring decisions with qualifications held fixed across many Arab
origins, in a German setting.

**Implies for us.**
- `not_stated` is not a neutral zero: keep German as the reference and `not_stated` as descriptive only.
- Wealth or SES is a plausible exploratory moderator and the basis of H1d. Use World Bank covariates (A14).
- Scope all claims to the explicit-field cue.

### 2.6 Fairness interventions in LLM decisions (`intervention`, 8)

**What it shows.**
- **Evidence that instructions work:**
  - `tamkin2023evaluating` (Claude 2.0): "Illegal to discriminate" and "Ignore demographics" cut discrimination scores close to zero while keeping decisions highly correlated with the originals. **Our neutrality paragraph is this type of instruction.**
  - `huijzer2025discrimination`: the best instruction cut the max–min group gap by only 27% on average.
  - `ganguli2023moral`: instructed self-correction emerges at about 22B parameters and improves with RLHF.
  - `schick2021self` and `gallegos2025self`: prompt-only self-debiasing reduces stereotyping.
- **Evidence that they fail or backfire:**
  - `karvonen2025robustly`: instructions fail once realistic company context is added (up to 12 pp, favouring Black and female candidates).
  - `nguyen2025race`: all prompting strategies fail in small models.
  - `salinas2024whats`: numeric anchors help, but qualitative detail can increase disparities.
- **Related:**
  - `bui2025dialects`: naming the attribute amplifies bias.
  - `mohammad2026mirage` and `aizaz2026persona`: mitigations change surface outputs, not decision or status patterns.

**Cannot answer.**
- The effect of an instruction on *nationality* effects.
- The effect on *within-group dispersion*. We found no study that measures dispersion under mitigation.

**Implies for us.**
- RQ3 stays two-sided, allowing attenuation, amplification and overcorrection.
- Expect the effect to depend on model size across the Qwen ladder.
- Our minimal job ads are a "simple setting", so state that as a limitation (`karvonen2025robustly`).
- Report changes in both the mean (H3b) and the dispersion (H3a).
- The paragraph names nationality, which may raise its salience (`bui2025dialects`).

### 2.7 Principle–behaviour consistency (`principle_behaviour`, 8)

**What it shows.** This is a crowded, named family:
- stated vs revealed preferences (`gu2025alignment`, formal "preference deviation");
- the value–action gap (`shen2025value`);
- explicitly unbiased but implicitly biased models, with relative evaluations more diagnostic than absolute ones (`bai2025explicitly`);
- overt vs covert prejudice (`hofmann2024dialect`);
- a veneer of fairness and task dependence (`gupta2024bias`; `kumar2026redirected`, divergence up to 0.43);
- unverbalized biases (`arcuschin2026blind`).

For nationality specifically:
- `mazeika2025utility`: implied exchange rates value lives unequally by country, and a model asked outright may deny it.
- Informal contrasts appear in `mao2025gatekeepers`, `zhu2024quite`, `shahid2026orientalism` and `aizaz2026persona`.

**Cannot answer.** How stated endorsement of non-discrimination relates to measured
nationality effects in hiring.

**Implies for us.**
- Frame the probe as an *application* of stated-vs-revealed comparison to non-discrimination in hiring. Claim no new construct or index.
- Keep control items and reverse keying (A11).
- `mentions_nationality` will undercount influence (`arcuschin2026blind`; `karvonen2025robustly` finds biases invisible in chain-of-thought).

### 2.8 Fairness and discrimination theory (`fairness_theory`, 14)

**What it shows.**
- **Fairness definitions:**
  - Individual fairness (`dwork2012fairness`) and counterfactual fairness (`kusner2017counterfactual`). Our clones test whether decisions are invariant to a *stated signal*, which is an audit-level counterfactual, not causal counterfactual fairness.
  - A principled critique of counterfactual audits: `kohlerhausmann2019eddie`.
- **Economics of discrimination:**
  - taste-based discrimination: `becker1957economics`, including customer discrimination;
  - statistical discrimination: `phelps1972statistical`;
  - customer contact and hiring: `holzer1998customer`, HUMAN.
- **Stereotype Content Model (SCM):**
  - `fiske2002model` and `cuddy2009stereotype`.
  - `lee2006not`: immigrant stereotypes reflect nationality combined with SES.
  - `froehlich2019warmth` (Germany): status predicts competence; recent groups from conflict regions such as North Africa are rated low in competence.
  - `kotzur2019stereotype`: refugee subgroups differ in warmth more than in competence.
- **Computational SCM:** `fraser2021understanding` (embeddings) and `cao2022theory` (the ABC model, related to but not the same as the SCM).
- **Evaluation mode:** `bohnet2016performance` (HUMAN) finds that joint evaluation reduces stereotype use.

**Cannot answer.** Whether LLM hiring decisions reproduce these structures. All
sources except `fraser2021understanding` and `cao2022theory` are human, and those two
measure representations, not decisions.

**Implies for us.**
- H1d rests on SCM theory. State the Kotzur qualifier: the competence gradient may be flat for refugee-associated origins.
- Code occupations by skill, customer contact and trust (Becker, Phelps, Holzer; A12).
- Always word findings as effects of a "national-origin signal", never as the effect of being Syrian.
- For RQ4, the human prediction is attenuation under joint evaluation (`bohnet2016performance`), while the no-ties property predicts amplification.

---

## 3. Corrections to seed citations

| # | Seed as given | Correction | Key |
|---|---|---|---|
| 1 | Wilson & Caliskan 2024 as an LLM hiring audit with gender results | It audits **text-embedding (MTE) retrieval, not generative LLMs**. AIES 7:1578–1590. The **erratum** (arXiv:2407.20371v3, revised 29 Aug 2026) says a code bug **inverted the gender-only results**; the race and intersectional results are unaffected. Cite the race and intersectional results only. | `wilson2024gender` |
| 2 | "An et al." | **Two different papers.** (a) Jiafu An, Huang, Lin & Tai, *PNAS Nexus* 4(3) pgaf089 (2025): résumé scoring, about 361k résumés. (b) Haozhe An, Acquaye, Wang, Li & Rudinger, ACL 2024 short: an acceptance or rejection email task. Do not merge them. | `an2025measuring`, `an2024large` |
| 3 | Veldanda et al. 2023 | The arXiv preprint 2310.05135 is titled "Are Emily and Greg Still More Employable than Lakisha and Jamal? …". The peer-reviewed workshop version is titled **"Investigating Hiring Bias in Large Language Models"** (NeurIPS 2023 R0-FoMo). | `veldanda2023emily` |
| 4 | Gaebler et al. 2024 | The arXiv title is "Auditing the Use of Language Models to Guide Hiring Decisions". The **published title and venue differ**: "Auditing large language models for race & gender disparities: Implications for artificial intelligence-based hiring", *Behavioral Science & Policy* 10(2):46–55 (print 2024, online 2025). | `gaebler2024auditing` |
| 5 | Rozado 2025 (arXiv) | **Now published:** *PeerJ Computer Science* 12:e3628 (2026). The methodology documents say "Rozado 2025" but carry the key. | `rozado2026gender` |
| 6 | Yin, Vardi & Choudhary (arXiv) | **Now published:** *PNAS Nexus* 5(8) pgag246 (2026). | `yin2026fragile` |
| 7 | Geiger et al. 2025 as a "salary audit varying nationality" | **It does not vary nationality.** *PLOS ONE* 20(2):e0318500 varies gender, 50 US universities and 19 majors. | `geiger2025salary` |
| 8 | Sorokovikova et al. 2025 as a "salary audit varying nationality" | **It does not vary nationality.** GeBNLP 2025, pp. 206–227, varies sex, ethnicity and migrant type (expatriate, migrant, refugee). | `sorokovikova2025surface` |
| 9 | MENAValues | arXiv:2510.13154. v1 (Oct 2025) was "I Am Aligned, But With Whom? MENA Values Benchmark …" by Zahraei & Asgari. **v2** (updated 18 Jun 2026) is **"The Alignment Veto: How Safety Training Suppresses Cultural Knowledge in LLMs"** and adds Tur and Hakkani-Tür. The bib cites v2; cite the version actually used. | `zahraei2025menavalues` |
| 10 | Törnberg 2026, arXiv:2603.13891 | **WITHDRAWN** by the author: "a confound in stimulus assignment … invalidates the main results". **DO NOT CITE**, including its Arab-name finding. It is not in the matrix or the bib. | – |
| 11 | Bai et al. PNAS 2025 | The published title is "Explicitly unbiased large language models still form biased associations" (PNAS 122(8)). The arXiv title differs. | `bai2025explicitly` |
| 12 | "ArGAN" | A dataset of Arabic stereotype prompts (Aly et al., GeBNLP 2025) covering gender, ability and 20 nationalities. It is not a GAN and not a hiring study. | `aly2025argan` |
| 13 | Tamkin et al. 2023 | The demographics are age, gender and race. **No nationality.** | `tamkin2023evaluating` |
| 14 | Salinas et al. 2023 | 20 nationalities, but **Jordan is the only Arab country**. | `salinas2023unequal` |
| 15 | "Haim, Salinas & Nyarko 2024" (methodology §11) | The first author is **Alejandro Salinas**: Salinas, Haim & Nyarko (arXiv:2402.14875). Fixed in §11. | `salinas2024whats` |
| 16 | Nghiem et al. 2024 as "name-induced nationality bias" (methodology §11) | It studies **race and gender**, not nationality. Fixed in §11. | `nghiem2024you` |
| 17 | Naous et al. 2024 as "cultural bias towards Arab culture" (methodology §11) | It measures a **Western-default** bias when models handle Arabic contexts. Wording fixed in §11. | `naous2024beer` |
| 18 | Kotzur et al. 2019 cited for "wealthier-origin groups seen as more competent" (hypotheses H1d) | The abstract reports **fewer competence differences** among refugee subgroups; warmth varies by origin. The claim was minimally corrected in `hypotheses.md`. | `kotzur2019stereotype` |
| 19 | Wang et al. 2023, "LLMs are not fair evaluators" | Published at ACL 2024. | `wang2024large` |
| 20 | Bilon 2025 | The author is "Bilon, X. J.". The abstract, now read, reports only **U.S. vs non-U.S.**; the country levels are unverified. | `bilon2025sociodemographic` |
| 21 | Abid et al. 2021 | AIES 2021, pp. 298–306. The *Nature Machine Intelligence* piece is a separate short item and is not in the bib. | `abid2021persistent` |
| 22 | Bloomberg 2024 | Journalism (Yin, Alba & Nicoletti), metadata only. Cite it as journalism. | `yin2024bloomberg` |
| 23 | Lancee 2021 | Print 2021 (online 2019). Cite the print year consistently. | `lancee2021ethnic` |

---

## 4. Design implications

The "Status" column refers to `design_contract.md` v0.2 (A-numbers) and the methodology documents.

| # | Finding (keys) | Design choice | Status |
|---|---|---|---|
| 1 | Large position bias: first-listed candidate chosen 63.5%; order effects as large as the largest demographic effect; order effects depend on quality (`rozado2026gender`, `vohra2026audit`, `yin2026fragile`) | **Quad design**: swap nationality between CVs and show both orders; estimate position γ; test order × tier | In the contract (§4). Pre-register the order × tier check. |
| 2 | Models recognise transparent audits and **tie identical-content pairs**; the tie rule manufactures effects (`vohra2026audit`, `chen2026beyond`, `castleman2026measuring`) | Pair **different same-tier CVs**; leave the choice field unconstrained; **pre-register tie and refusal handling** (primary: NA plus reported rate; sensitivity: 0.5) | CVs and schema in the contract. The tie rule must be written into the preregistration. |
| 3 | Explicit fields amplify and are transparent (`rozado2026gender`, `tamkin2023evaluating`, `bui2025dialects`, `needham2025large`) | Independent evaluation primary; constant personal-details fields (A8); `mentions_testing` flag (A18); claims scoped to the explicit-field cue (`tonneau2026cues`) | Adopted. Scope the wording in the paper. |
| 4 | Pooled Arab penalty already shown in LLMs (`lippens2024computer`, `saeed2024desert`; pooled Arabic-name group also in `hoffmann2026evaluating`) and in humans (`lippens2023state`) | **Within-Arab contrasts primary** (RQ1); the pooled Arab-vs-benchmark contrast is secondary (RQ2) and framed as a replication | Adopted (hypotheses RQ1/RQ2). |
| 5 | A nationality line signals **non-citizenship**; citizenship carries large human penalties (`quillian2026racialized`) | Within-Arab comparisons hold the citizenship signal constant, **Arab-vs-German comparisons do not**; Polish is the EU-foreign benchmark; the work-authorisation line fixes legal status on the record | Adopted. Interpret Δ(Ā, DEU) as origin plus citizenship signal. |
| 6 | Origin-country characteristics predict human callbacks (`distasio2024same`); cultural distance explains German penalties (`koopmans2019taste`); SCM status→competence (`lee2006not`, `froehlich2019warmth`) | Frame the **status gradient (H1d) as an LLM-specific test**, not a new idea; authoritarianism and gender inequality stay exploratory only; covariates from the World Bank API (A14) | Framing action for the team. |
| 7 | `zahraei2025menavalues` (14 Arab states, values) and `keleg2025arabs` (the homogeneity critique) | **Novelty limited to hiring decisions with qualifications held fixed**; cite both as prior work on Arab heterogeneity outside decisions | Framing action. See `novelty_assessment.md`. |
| 8 | "Heterogeneity" is trivially true without a noise floor: 22 levels at T = 0.7; competence-preserving changes flip 29.6–41.4% of pairwise decisions (`chen2026competence`); nondeterminism (`atil2024nondeterminism`, `he2025defeating`) | **Pre-register a noise-floor test**: debiased σ_A with a within-CV permutation noise floor (D25), plus a comparison of σ_A with σ_placebo from 8 placebo nationality signals (`stimuli/nationalities.csv`, group `placebo`; baseline IE only), with the 19-origin σ_A as a co-requirement for the headline claim; judge against the SESOI (A2) | Adopted by the lead after the adversarial review (H5); see `novelty_assessment.md` §7a. |
| 9 | Many noisy unit effects (`kline2022systemic`, `kline2024discrimination`) | Hierarchical model with the pre-registered sub-regional grouping; empirical-Bayes shrinkage; FDR control for 22 contrasts | Partly adopted (sub-regions in contract §2). |
| 10 | Pseudo-replication; clustered SEs up to about 3× naive (`miller2024adding`, `hurlbert1984pseudoreplication`) | Unit = base CV × nationality; replicates are within stimulus; random effects for CV, occupation and quad | Adopted (contract §5). |
| 11 | Prompt and format sensitivity (`sclar2024quantifying`, `an2024large`, `rottger2024political`) | K = 3 wording variants crossed with nationality (A3) | Adopted. |
| 12 | Version drift and nondeterminism (`chen2024chatgpt`, `atil2024nondeterminism`, `he2025defeating`) | `model_revision`, seeds from non-nationality fields, randomised execution order (A5, A6, A17) | Adopted. |
| 13 | The "no nationality" condition is an outlier, not a zero (`salinas2023unequal`); anonymous controls behave inconsistently (`armstrong2024silicon`) | German as reference; `not_stated` descriptive only and excluded from forced choice (A9) | Adopted. |
| 14 | Neutrality instructions work in minimal settings (`tamkin2023evaluating`), fail in realistic ones or small models (`karvonen2025robustly`, `nguyen2025race`), and may backfire through salience (`bui2025dialects`) | RQ3 two-sided (attenuate / amplify / overcorrect); expect size dependence (`ganguli2023moral`); state the minimal job ads as a limitation | Adopted (hypotheses RQ3). Limitation to be stated. |
| 15 | Mitigation studies report only means or max–min gaps (`tamkin2023evaluating`, `huijzer2025discrimination`) | Report the change in **dispersion** (H3a) as well as the mean | Adopted. A possible secondary novelty. |
| 16 | Explanations may amplify bias (`tan2026small`); biases are often unverbalized (`arcuschin2026blind`, `karvonen2025robustly`) | Keep the `reason` field identical across conditions; text flags are exploratory and undercount | Adopted. Caution in interpretation. |
| 17 | Language markers leak ethnicity (`tan2026small`, `leininger2026fairness`, `rao2025invisible`) | Languages constant, no Arabic; language-line robustness arm (A13) | Adopted. |
| 18 | Religion channel: "Muslim by default" (`distasio2021muslim`), `mohammad2026mirage`, `abid2021persistent` | Religion is part of the total effect; `mentions_religion` exploratory; religion cue arm parked | Adopted. |
| 19 | The principle–behaviour gap is a crowded construct (`gu2025alignment`, `shen2025value`, `bai2025explicitly`, `hofmann2024dialect`, `mazeika2025utility`) | Present the probe as a stated-vs-revealed **application**; no new "index"; control items and reverse keying (A11) | Framing action. |
| 20 | Positive controls and equivalence tests make nulls defensible (`pavlopoulos2026minimal`); models often fail validity checks (`castleman2026measuring`) | Positive-control clone (A7); SESOIs (A2) | Adopted. |
| 21 | Recent models reverse the human direction (`gao2026can`, `gaebler2024auditing`, `an2025measuring`, `rozado2026gender`) | Two-sided tests; log model vintage | Adopted. |
| 22 | Anonymised applications are a real German practice (`krause2012anonymous`); names carry class and citizenship signals (`crabtree2023validated`) | Pseudonymised applicant reference with a constant system-prompt sentence (A23); no names in the primary design | Adopted. |
| 23 | Refugee association: refugee subgroups are seen as low in status (`kotzur2019stereotype`); refugees get lower salary advice (`sorokovikova2025surface`) | Interpret Syrian, Iraqi, Sudanese, Somali and Palestinian signals with care; the optional Ukrainian benchmark would separate "refugee-associated" from "Arab" | OPEN (CR-22). |

---

## 5. Open items

1. **Bilon 2025:** read the full text for the national-origin levels before citing any country detail. A second retry through Unpaywall, Semantic Scholar, Crossref, CORE, the web, tandfonline and the author's site found no open copy; library access is needed.
2. **Busetta et al. 2025:** the ethnicity levels are not in the abstract. Low priority, because it has no nationality factor.
3. **Lee & Cheon 2026** (SSRN 7118103, "Does Bias Drift?"): not assessed (no abstract; SSRN 403).
4. `leininger2026fairness`: confirm the name groups in the full text. "German vs Turkish" comes from an HTML snippet.
5. `tan2026small`: check that it appears in the EMNLP 2026 proceedings.
6. "First Come, First Hired?" (MIT Computational Law Report, position bias): still 403, unverified, and not included.
7. Arabic-language databases: not searched. Name this as a coverage limit, or search them if time allows.
8. Every `abstract`-level source used for a specific number in the paper needs a full-text check.
