# L2 literature notes (part 2 of 2): Arab/MENA bias, nationality bias, the key question, interventions, principle-behaviour

Internal research notes, not report prose. Do not paste into the paper (see AI-usage rule in CLAUDE.md).

- Compiled: 2026-09-29/30.
- Companion files: `L2_matrix.csv` (54 rows, one per source), `L2_refs.bib` (same keys), `L2_novelty_draft.md`.
- Verification levels: **fulltext** = relevant sections of the PDF read (methods, category lists, key tables); **abstract** = abstract read from arXiv/ACL/publisher; **metadata** = bibliographic record confirmed (Crossref/publisher) but content not read. Nothing below is `unverified`; unverifiable or withdrawn items are listed under "Excluded / to check" and are not in the bib.
- Counts: 12 fulltext, 40 abstract, 2 metadata.
- Scope boundary: general LLM hiring audits (race/gender) and human correspondence audits are part 1. Lippens (2024) appears here too because it is the only LLM hiring audit that carries an explicit "Arab" group.

## Seed-citation check

| Seed in the brief | Status |
|---|---|
| Saeed et al., "Desert Camels and Oil Sheikhs" | Correct. arXiv:2410.24049 (2024). No peer-reviewed version found via Crossref. |
| MENAValues | Exists, but the record changed: arXiv:2510.13154. v1 title was "I Am Aligned, But With Whom? MENA Values Benchmark..." (Zahraei & Asgari). v2 is retitled "The Alignment Veto: How Safety Training Suppresses Cultural Knowledge in LLMs" and adds Tur and Hakkani-Tür. Cite the version you actually use. |
| Naous et al., "Having Beer after Prayer?" (CAMeL, ACL 2024) | Correct. ACL 2024 long, pp. 16366-16393. |
| Abid et al. 2021, persistent anti-Muslim bias | Correct. AIES 2021, pp. 298-306. A companion short piece also appeared: "Large language models associate Muslims with violence", *Nature Machine Intelligence* 3(6):461-463 (metadata only; not in the bib). |
| "ArGAN" / Arabic nationality bias | Exists. Aly, Allam, Gaber & Basta (2025), GeBNLP workshop, pp. 256-267. It is an Arabic (MSA) stereotype dataset covering gender, ability and 20 nationalities. It is not a GAN and not a hiring study. |
| Venkit et al. EACL 2023 | Correct. pp. 116-122. |
| Zhu et al. LREC-COLING 2024 | Correct. pp. 13489-13502. |
| Kamruzzaman et al. ACL Findings 2024 | Correct. pp. 8940-8965. |
| **Geiger et al. 2025 as a "salary audit varying nationality"** | **Wrong on content.** Published as *PLOS ONE* 20(2):e0318500 (2025). It varies gender, 50 **US** universities and 19 majors. The paper states it tested only US universities. There is **no nationality factor**. |
| **Sorokovikova et al. 2025 as a "salary audit varying nationality"** | **Wrong on content.** Published at GeBNLP 2025, pp. 206-227. Its personas vary sex, ethnicity (Asian/Black/Hispanic/White) and migrant type (expatriate/migrant/refugee). There is **no nationality factor**. |
| Salinas et al. EAAMO 2023 (job recommendations) | Correct. Varies 20 nationalities, but Jordan is the only Arab country. |
| Tamkin et al. 2023 | Correct (arXiv:2312.03689). The demographics are age, gender and race. **Nationality is not included.** |
| Bai et al., PNAS 2025 | Correct. Published title: "Explicitly unbiased large language models still form biased associations", PNAS 122(8):e2416228122. The arXiv title differs ("Measuring Implicit Bias in Explicitly Unbiased Large Language Models"). |

## A. Arab / MENA / Muslim bias in LLMs

The pattern is that Arab-focused LLM work measures stereotypes, cultural alignment, safety or knowledge, and usually treats "Arab" as one group. The exceptions that do resolve individual Arab countries are about values or knowledge, not decisions about people.

- **Saeed et al. 2024 (Desert Camels)** [abstract]: red-teamed 6 frontier models on Arab vs Western bias across 8 domains. Found negative bias toward Arabs in 79% of cases. For us: anti-Arab bias at the pooled level is established, so a pooled "Arab penalty" alone would not be new.
- **Saeed et al. 2026 (LREC; debate benchmark)** [abstract]: 8,400 debate prompts in 7 languages. Arabs were cast in Terrorism/Religion roles in ≥89% of cases. For us: conflict and religion are the most likely channels, which supports the exploratory `mentions_conflict` and `mentions_religion` flags.
- **Naous et al. 2024 (CAMeL)** [abstract]: Arabic-language models default to Western cultural entities. A different construct from ours.
- **Abid et al. 2021** [abstract]: GPT-3 shows a Muslim-violence association. Positive-adjective prompts cut violent completions from 66% to 20% but not to parity. For us: Arab ≠ Muslim, but religion is a plausible part of what the nationality signal evokes. It is also early evidence that prompt counter-signals only partly work.
- **Zahraei et al. 2025 (MENAValues)** [fulltext, partial]: value alignment with survey data across 16 MENA countries (14 Arab League members plus Iran and Turkey). Found clear country-level inequity (Algeria worst-served, Palestine best, about a 19.8% gap). Under Arabic prompting, models **collapse Arab countries into one cluster**. For us: this is the strongest prior evidence that LLMs both differentiate and homogenise individual Arab countries, but it measures values, not treatment of individuals. It is the main reason "within-Arab heterogeneity" cannot be claimed as new *in general*.
- **Aly et al. 2025 (ArGAN)** [fulltext]: MSA stereotype prompts over 20 nationalities for 5 models (incl. JAIS). All models directed the most negativity at Arabs, Egyptians, Mexicans and Indians, and the most positivity at Americans, Germans and Japanese.
- **Elsafoury & Hartmann 2025** [abstract]: offensive-stereotyping bias for 270 marginalized groups across Egypt, the other 21 Arab countries, Germany, the UK and the US, in 23 LMs. Egyptian Arabic yields more measured bias than MSA. It covers all 22 countries, but the targets are minorities *within* countries, not applicants' national origin.
- **Keleg 2025 (C3NLP)** [abstract]: position paper arguing that the "Arabs share one culture" assumption is invalid yet widely built into LLMs. It is the conceptual anchor for disaggregation, so we cannot claim the critique itself.
- **Almheiri et al. 2025** [abstract]: commonsense reasoning across 13 Arab countries. A few in-country examples transfer to other Arab countries (about +10%). Models represent Arab countries as distinct but related.
- **Asseri et al. 2025** [abstract; authors flag "research is incomplete"]: systematic review found only 8 empirical studies of prompt-based mitigation for anti-Arab/Muslim bias, none in hiring. It documents the RQ3 gap.
- **Shahid 2026 (MECSS)** [abstract]: coins "Said-washing": a model disclaims generalising about the Middle East, then reproduces the structure it disclaimed. This is a region-specific named principle-behaviour gap (see E).

## B. Nationality / country-of-origin bias

Nationality is studied far less than gender or race. Ghosh & Wilson (AIES 2025) [abstract] report that nationality appears in 13.2% of 189 bias papers, against 79.9% for gender. Many-country studies exist, but they measure text generation, perceptions or recommendations.

- **Venkit et al. 2023** [fulltext]: GPT-2 stories for 193 demonyms. Sentiment tracks internet use and economic status. The **five most negative demonyms were Libya, Sierra Leone, Sudan, Tunisia and South Sudan**, three of them Arab League members. This is old-model evidence that individual Arab demonyms are treated very differently.
- **Zhu et al. 2024** [abstract]: ChatGPT over 195 countries in Chinese and English. Output is mostly positive. ChatGPT rates its own text as neutral, yet detects nationality bias when it annotates pairwise, a say-do-type discrepancy (see E).
- **Kamruzzaman et al. 2024 (Findings ACL)** [abstract]: template associations incl. nationality coded by GDP. **Kamruzzaman & Kim 2024** [abstract]: with 193 nationality personas, models favour Western Europe and rate African, Latin American and Eastern European nations more negatively.
- **Manvi et al. 2024 (ICML)** [abstract]: models rate lower-SES places lower on intelligence, morality and attractiveness. This suggests an exploratory wealth moderator within the Arab set (e.g., GCC vs others). Label it exploratory; it must not become a new factor.
- **Jha et al. 2023 (SeeGULL)** [abstract]: stereotype resource spanning 178 countries. It could inform exploratory coding of nationality-specific stereotype content.
- **Salinas et al. 2023 (EAAMO)** [fulltext]: job recommendations for 20 nationalities (Jordan the only Arab country), with a no-nationality US baseline. Mexican workers got lower-paid jobs. **The no-nationality baseline was itself an outlier.** For us: this closely mirrors our `not_stated` control and warns that "not stated" is not a neutral zero.
- **Forcada Rodríguez et al. 2025 (GeBNLP)** [fulltext: country list]: occupation recommendations for 25 countries, incl. Morocco and Saudi Arabia, in English, Spanish and German. Country and intersectional biases appear, and prompt language matters.
- **Mao & Zhao 2025** [fulltext]: GPT-3.5/4 in a discrete choice experiment on US immigration admission (10,000 choice sets). Countries of origin were Germany, France, Mexico, Philippines, Poland, China, **Sudan, Somalia, Iraq** and India. Most country coefficients were not significant. In interviews the models said origin matters little, yet reasoned by origin ("additional scrutiny" for Iraq/Sudan/Somalia). For us: it is the only decision study found with several Arab League origins, and it contains an informal stated-vs-revealed contrast.
- **Pelosio et al. 2025** [abstract]: BBQ nationality items with names in place of explicit labels. Most of the bias survives the swap.
- **Nguyen et al. 2026 (FAccT)** [abstract]: narratives cast Global-Majority national identities in subordinated roles. Representational, not allocative.
- **Geiger et al. 2025; Sorokovikova et al. 2025**: see the seed corrections above. Neither varies nationality. From Sorokovikova, the finding that refugees get lower salary advice is relevant as a possible channel for Syrian, Yemeni or Sudanese signals.
- Hiring-adjacent studies where "nationality" means two levels: **ABLEIST** (Phutane et al. 2025) [fulltext] uses American vs Indian; **Rao et al. 2025 (AIES)** [abstract] compares UK vs Indian transcripts, and name swaps alone showed no effect. **Bilon 2025** [metadata]: a ChatGPT hiring study with a national-origin factor (24,000 evaluations per a search snippet); the country levels could not be verified (publisher 403). Read it before citing.
- German setting: **Leininger et al. 2026** [abstract] studies German résumé generation with German- vs Turkish-associated names. Ethnicity leakage was weak. There are no Arab origins, and it supports Turkish as the German migrant-origin benchmark.

## C. The key question: controlled LLM hiring experiments comparing multiple individual Arab (or MENA) nationalities

**Result: none found within our coverage** (see the search log: about 35 web queries in English and German, 25 arXiv API field queries, 5 OpenAlex queries, ACL Anthology pages, and Crossref for verification; Semantic Scholar was mostly rate-limited). Treat this as "not found", not as "does not exist".

What does exist, ordered by closeness:
1. LLM CV-screening audits that include **one pooled Arab category** (Lippens 2024; Arab names drawn from several name sources).
2. LLM decision or advice tasks that include **a few individual Arab League countries** but in a non-hiring task, with no within-Arab estimand: Mao & Zhao 2025 (Iraq, Sudan, Somalia; immigration admission), Forcada Rodríguez et al. 2025 (Morocco, Saudi Arabia; occupation recommendation), Salinas et al. 2023 (Jordan; job recommendation), Huijzer & Chen 2025 (Moroccan background; generic decisions).
3. Work that resolves **many individual Arab countries** but not in decisions about people: MENAValues (values), Elsafoury & Hartmann (in-country marginalized groups), Venkit 2023 and Zhu 2024 (generation over all countries), Almheiri 2025 (knowledge).
4. A precedent for the **logic of disaggregating a pooled category** in LLM judgments: Sakunkoo & Sakunkoo 2025 (Asian subgroups, US status rankings).

## D. Fairness interventions in LLM decisions (RQ3)

The evidence is mixed, so RQ3 is a live question rather than a foregone conclusion.

- **Tamkin et al. 2023** [fulltext]: Claude 2.0 on 70 decision scenarios varying age, gender and race (explicit or via names). Appended interventions, esp. "Illegal to discriminate" and "Ignore demographics" (and their combination), cut discrimination scores close to zero while keeping decisions highly correlated with the originals. **Our neutrality paragraph is essentially an "Illegal/Ignore"-type instruction.** Tamkin did not test nationality or dispersion within a group.
- **Huijzer & Chen 2025** [fulltext]: Tamkin's templates translated into Dutch, with Dutch/Turkish/Moroccan/Mexican/European-American/African-American backgrounds and explicit vs name-based salience. The best mitigation instruction cut the max-min group gap by only 27% on average; GPT-4o was less biased in English.
- **Ganguli et al. 2023** [abstract]: instructed "moral self-correction" emerges around 22B parameters and grows with RLHF. This predicts a size-dependent neutrality effect across our model ladder.
- **Schick et al. 2021** [abstract] (self-diagnosis/self-debiasing) and **Gallegos et al. 2025** [abstract] (zero-shot self-debiasing by explanation or reprompting) show prompt-only reductions in stereotyping, mostly in QA tasks.
- Evidence of failure or reversal: **Karvonen & Marks 2025** [abstract] find anti-bias prompts fail once realistic hiring context is added, with effects up to 12 points that favour Black and female candidates. **Nguyen & Tan 2025 (COLM)** [abstract] find that all prompting strategies fail in small instruction models (Gemma 2B, LLaMA 3.2 3B).
- Naming the attribute can backfire: **Bui et al. 2025 (EMNLP)** [abstract] find an explicit demographic label amplifies bias more than implicit cues (German dialects). This bears on both the explicit `Nationality:` line and a neutrality paragraph that names nationality. **Tan et al. 2026** [abstract] find that asking for explanations may amplify hiring bias, so our `reason` field is not inert. **Salinas, Haim & Nyarko 2024** [abstract] find that numeric anchors counteract name bias while added qualitative detail can increase it.
- **Asseri et al. 2025**: essentially no Arab-specific evidence on instruction-based mitigation in decisions.

## E. Principle-behaviour consistency

A "principle-behaviour gap" is already a well-populated, named family of constructs. Any measure we build is an operationalisation of an existing idea.

- **Stated vs revealed preferences:** Gu et al. 2025 [abstract] formally define a "preference deviation" (KL divergence between choices under general-principle prompts and under contextualised prompts).
- **Value-action gap:** Shen et al. 2025 (EMNLP) [abstract] built ValueActionLens (14.8k actions, 12 cultures) and found stated values and actions misaligned.
- **Explicit vs implicit bias:** Bai et al. 2025 (PNAS) [abstract] show models that pass explicit bias tests still make biased relative decisions, and that relative (pairwise) evaluations are more diagnostic than absolute ones. This also supports our forced-choice arm.
- **Overt vs covert prejudice:** Hofmann et al. 2024 (Nature) [abstract] show positive overt stereotypes alongside very negative covert ones that drive decisions.
- **Veneer of fairness / task dependence:** Gupta et al. 2024 (ICLR) [abstract] and Kumar et al. 2026 [abstract] find models reject stereotypes on explicit probes but reproduce them on implicit tasks (Stereotype Score divergence up to 0.43).
- **On nationality specifically:** Mazeika et al. 2025 [fulltext, partial] find GPT-4o's implied exchange rates value lives unequally by country, and note that the model may deny such a preference when asked outright. No Arab countries appear in the shown figure. Mao & Zhao 2025 show the same informal contrast in immigration decisions.
- **Explanation-behaviour gaps:** Arcuschin et al. 2026 (ICML) [abstract] define "unverbalized biases", effects that never appear in the reasoning. For us, the `mentions_nationality` flag will undercount influence. Shahid 2026 names "Said-washing".
- **Normative anchors:** Kusner et al. 2017 (counterfactual fairness) [abstract] and Dwork et al. 2012 (individual fairness) [metadata]. Our clones change the *stated signal*, not the person, so we test invariance of decisions to that signal. This is an audit-level counterfactual, not full causal counterfactual fairness, and it should be worded that way.

## Design implications from this literature (no new factors)

1. Report the pooled Arab-vs-German contrast **and** the between-country dispersion. The pooled penalty is established (Lippens; Saeed), so the dispersion is the contribution.
2. Keep ties and refusals observable and counterbalance position. Chen & Xiao 2026 found forbidding ties manufactures a 0.39 selection ratio; Vohra & Ravikiran 2026 found position effects rival demographic ones and that models recognise transparent audits.
3. Interpret `not_stated` carefully: Salinas 2023 found the no-nationality baseline is itself an outlier.
4. Scope claims to the explicit nationality-field cue. Tonneau et al. 2026 show that different cues for the same group give inconsistent conclusions, and Bui et al. 2025 show explicit labels amplify.
5. Describe the principle probe as a stated-vs-revealed (Gu) or value-action (Shen) comparison applied to non-discrimination in hiring, not as a new construct.

## Closest prior work (ranked by closeness to our exact experiment)

Criteria: (a) hiring/screening decision, (b) national-origin manipulation, (c) several individual Arab origins, (d) counterfactual clones, (e) instruction mitigation or principle probe.

1. **Lippens (2024), *Computers in Human Behavior: Artificial Humans*** [fulltext]. *Does:* LLM (GPT-3.5) CV-screening correspondence audit, 34,560 vacancy-CV combinations, 9 name-signalled ethnic groups incl. "Arab" and "Turkish", Dutch reference, Arab-named applicants penalised. Meets (a) and (d). *Does not:* disaggregate Arab by nationality; use a nationality field (names bundle ethnicity, religion and gender); test more than one model; test mitigation or a principle probe; use a German setting.
2. **Huijzer & Chen (2025), arXiv:2509.09735** [fulltext]. *Does:* Tamkin-style decisions in English and Dutch with Dutch, Turkish, Moroccan and other backgrounds, explicit vs name salience, and several mitigation instructions (best: −27% gap). Meets (b) partly and (e). *Does not:* run a CV audit or hiring-specific screening; include more than one Arab origin; estimate within-group heterogeneity.
3. **Salinas et al. (2023), EAAMO** [fulltext]. *Does:* employment advice (job recommendations, salaries) for 20 nationalities with a no-nationality baseline, in two models. Meets (b) and (d) loosely. *Does not:* screen candidates; include more than one Arab country (Jordan); ground nationality selection (ChatGPT-generated list); test mitigation.
4. **Mao & Zhao (2025), arXiv:2506.21574** [fulltext]. *Does:* person-level allocative choice (US immigration DCE, 10,000 choice sets) with 10 origins incl. Iraq, Sudan and Somalia, plus interviews contrasting stated principles with origin-based reasoning. Meets (b), (c) weakly and (e) informally. *Does not:* study hiring; analyse within-Arab dispersion; use counterfactual CV clones; use a German setting; pass peer review (preprint).
5. **Forcada Rodríguez et al. (2025), GeBNLP** [fulltext: country list]. *Does:* 25 countries incl. Morocco and Saudi Arabia × gender, prompts incl. German, 5 Llama models; finds country biases in occupation recommendations. Meets (b) and (c) minimally. *Does not:* screen candidates; hold qualifications fixed in a CV; test mitigation; analyse Arab heterogeneity.

Honourable mentions (construct-level threats, not design-level): **MENAValues** (within-Arab heterogeneity in cultural alignment across 14 Arab states); **Venkit et al. 2023** (Libya, Sudan and Tunisia among the most negative demonyms); **Tamkin et al. 2023** (the intervention template for RQ3).

## Excluded / to check (not in bib)

- **Törnberg 2026**, "Large Language Models Reproduce Racial Stereotypes When Used for Text Annotation" (arXiv:2603.13891). Its abstract mentions Arab names and hireability, but the **author withdrew it** "due to a confound in stimulus assignment that invalidates the main results". Do not cite.
- **Bilon 2025** (J. Decision Systems): in the matrix at metadata level only. The national-origin levels must be checked before any claim about it.
- **Busetta, Campolo & Ficarra 2025**, "Artificial Intelligence and Discrimination: A Vignette Experiment of Labour Market Discrimination in LLMs" (Springer, *Statistics for Innovation II*, pp. 303-308). Metadata only. It is unknown which groups it varies (possibly migrants in Italy), so it is a potential threat to check.
- **Deshmukh et al. 2025** (ICAAI, "Bias in Recruitment Systems Utilizing LLMs"): WEAT on BERT/GPT-2/GPT-Neo for gender, race and age, per a search-engine summary of its White Rose repository record (not read directly). Not nationality; excluded.
- **Li, Li & Lu 2023** (arXiv:2307.08624): national-origin discrimination in word-embedding resume screening. Pre-LLM; origins not extracted.
- Read at abstract level but left out of the matrix for low relevance: Liu et al. 2025 (Findings ACL; the published title begins "7 Points to Tsinghua but 10 Points to 清华?..."; national bias in agentic advice across languages); Kamruzzaman et al. 2025 (IJCNLP-AACL; nationality personas and emotion attribution); Rotar et al. 2026 (prompt debiasing in recommenders; "might overpromote specific groups"); Zhou & Ackerman 2026 (utility-behaviour gap); Hoffmann et al. 2026 (LLM hiring implicit weights, freelance marketplace); Pavlopoulos 2026 (*Analytics*; gender/race résumé audit; part 1 scope).
- For part 1: the German human field experiments with many national origins (e.g., the WZB "Ethnische Hierarchien in der Bewerberauswahl" field experiment) are the natural human benchmark for our design. They were surfaced in a German-language search but not verified here.

## Search log

Dates: 2026-09-29 and 2026-09-30. "Relevant" means relevant to scope A-E. The key-question column (KQ) counts studies that run an LLM hiring/screening experiment over **more than one individual Arab nationality**. It is 0 for every query.

### arXiv API (export.arxiv.org, field-restricted boolean queries; top 25-40 by relevance inspected)

| Query | Total | Relevant | KQ |
|---|---|---|---|
| `all:nationality AND all:hiring AND all:"language model"` | 3 | 1 (ABLEIST) | 0 |
| `all:Arab AND all:"language model" AND all:bias` | 37 | 7 (Asseri, ArabJobs, Naous, Elsafoury, Saeed, Lippens, Abdoli) | 0 |
| `all:nationality AND all:resume AND all:LLM` | 1 | 0 | 0 |
| `all:"country of origin" AND all:LLM AND all:bias` | 8 | 0 | 0 |
| `all:immigrant AND all:hiring AND all:LLM` | 1 | 1 (Armstrong; part 1) | 0 |
| `abs:nationality AND abs:bias AND abs:hiring` | 9 | 2 (Saldivar synthetic CVs; ABLEIST) | 0 |
| `abs:nationality AND abs:recruitment AND abs:LLM` | 2 | 0 | 0 |
| `abs:Arab AND abs:hiring` | 2 | 1 (Törnberg; withdrawn) | 0 |
| `abs:"national origin" AND abs:"language model"` | 4 | 2 (Nguyen FAccT'26; Weissburg) | 0 |
| `abs:MENA AND abs:bias AND abs:LLM` | 0 | 0 | 0 |
| `abs:nationality AND abs:"large language models" AND abs:decision` | 70 | 2 (Mao & Zhao; Salinas) | 0 |
| `abs:nationality AND abs:LLM AND abs:discrimination` | 9 | 2 (Mao & Zhao; ABLEIST) | 0 |
| `abs:Arabs AND abs:LLMs` | 311 | 2 bias-relevant in top 40 (Keleg; Palm) | 0 |
| `abs:"nationality bias"` | 9 | 4 (Zhu; Venkit ×2; Salinas) | 0 |
| `abs:"nationality" AND abs:"resume"` | 9 | 0 | 0 |
| `abs:"nationality" AND abs:"candidates" AND abs:"LLMs"` | 21 | 1 (ABLEIST) | 0 |
| `abs:"Middle Eastern" AND abs:LLM AND abs:bias` | 0 | 0 | 0 |
| `abs:"Arab" AND abs:"names" AND abs:"LLM"` | 17 | 1 (Törnberg; withdrawn) | 0 |
| `ti:"value-action gap"` | 1 | 1 (Shen) | - |
| `ti:"knowing-doing gap" OR ti:"say-do"` | 2 | 0 | - |
| `abs:explicit AND abs:implicit AND abs:bias AND abs:decision AND abs:LLM` | 15 | 4 (Bai; Kumar 2026; Bui 2025; Lin survey) | - |
| `abs:say AND abs:do AND abs:LLM AND abs:bias AND abs:consistency` | 1 | 0 | - |
| `ti:stated AND ti:revealed AND abs:LLM` | 3 | 1 (Gu) | - |
| id_list lookups (≈60 IDs) for abstracts/comments/withdrawal notices | - | - | - |

### Semantic Scholar Graph API (paper/search)

Most calls returned HTTP 429 (rate limit), even with backoff up to about 30 s. Only 3 of 12 queries returned results.

| Query | Result | Relevant | KQ |
|---|---|---|---|
| nationality bias large language models hiring | 15,845 total, top 20 read | 4 (Zhu; ArGAN; Rao; Nghiem) | 0 |
| Arab applicants large language model hiring | 1,239, top 15 read | 2 general hiring audits (Valkanova; An) | 0 |
| country of origin resume LLM discrimination | 18 | 1 (Bilon 2025) | 0 |
| Middle Eastern names resume screening language model; Arabic names resume LLM bias; migrant background LLM recruitment discrimination; nationality bias LLM resume screening; country of origin bias large language model job candidates; Arab names large language model employment bias; migrant applicants large language model hiring discrimination; Middle Eastern applicants ChatGPT hiring; Arab nationality bias large language model | HTTP 429, no results | - | - |

### OpenAlex API (works?search=, from 2021; top 15 read)

| Query | Total | Relevant | KQ |
|---|---|---|---|
| nationality bias large language model hiring | 7,230 | 2 (Naous; Fabris hiring-fairness survey) | 0 |
| Arab applicants large language model | 5,088 | 2 (Lippens; Bai) | 0 |
| national origin discrimination ChatGPT recruitment | 1,739 | 2 (Lippens; Fleisig dialect) | 0 |
| Middle Eastern North African LLM bias employment | 294 | 3 (Pawar; Ghosh & Wilson; Tan & Lee) | 0 |
| migrant background large language model CV screening | 589 | 0 | 0 |

### Web search (general engine; results pages and snippets read, candidate papers then verified via arXiv/Crossref/ACL)

| # | Query | Relevant new | KQ |
|---|---|---|---|
| 1 | LLM hiring bias nationality Arab countries resume experiment Egyptian Syrian Saudi applicants | 2 (Lippens; Rao) | 0 |
| 2 | "Desert Camels and Oil Sheikhs" Arab-centric red teaming LLMs | 1 (seed) | 0 |
| 3 | large language model resume screening nationality heterogeneity Arab countries Gulf Levant Maghreb applicants bias | 2 (Pelosio; Liu 2025) | 0 |
| 4 | LLM recruiter bias Germany applicants nationality "Staatsangehörigkeit" OR "migration background" GPT CV audit study | 2 (Mao & Zhao; Leininger) | 0 |
| 5 | arXiv 2025 LLM hiring audit "nationality" dozens of countries candidate evaluation discrimination | 3 (Vohra; Karvonen; ABLEIST) | 0 |
| 6 | MENAValues benchmark cultural alignment multilingual bias ... MENA | 2 (MENAValues; MECSS) | 0 |
| 7 | "nationality" LLM "job applicants" bias Syrian Lebanese Moroccan Egyptian GPT evaluation study | 1 (Huijzer & Chen) | 0 |
| 8 | intra-regional heterogeneity nationality bias LLM Arab countries "within-group" differences GPT | 5 (Nguyen FAccT; Almheiri; Saeed 2026; Kamruzzaman 2025; Keleg) | 0 |
| 9 | LLM hiring discrimination Gulf GCC expatriate nationality Saudi Emirati candidates ChatGPT audit | 0 | 0 |
| 10 | "LLM Alignment for the Arabs: A Homogenous Culture or Diverse Ones" | 1 (Keleg) | 0 |
| 11 | Diskriminierung KI Bewerbung Staatsangehörigkeit ChatGPT Studie Lebenslauf arabisch | 0 (German news only) | 0 |
| 12 | "Middle Eastern" candidates large language model resume ranking bias study 2025 | 1 (Tan 2026) | 0 |
| 13 | LLM hiring bias "nationalities" "Arab" names resume screening multiple countries arXiv 2026 | 0 | 0 |
| 14 | "Arab" "nationality" counterfactual CV LLM recruiter experiment "22" countries OR "Arab League" | 0 | 0 |
| 15 | LLM bias against Syrian refugees applicants job evaluation GPT experiment | 0 | 0 |
| 16 | aclanthology nationality bias hiring large language models 2025 countries applicants evaluation | 0 (Sjåvik & Touileb; Helwe - tangential) | 0 |
| 17 | Arabic language LLM hiring bias CV screening Arabic prompts nationality gender study Jais AceGPT | 0 | 0 |
| 18 | "nationality" "large language models" "job" bias "Egypt" "Saudi Arabia" "Morocco" evaluation fairness 2025 OR 2026 | 1 (Forcada Rodríguez) | 0 |
| 19 | debiasing instruction prompt backfire LLM "overcorrection" OR "increases bias" ... | 2 (Nguyen & Tan; Rotar) | - |
| 20 | stated versus revealed preferences large language models consistency paper arXiv 2025 | 3 (Gu; Zhou & Ackerman; Wang et al.) | - |
| 21 | "Bias in Recruitment Systems Utilizing Large Language Models" Deshmukh Le Quy Hopfgartner | 0 (not nationality) | 0 |
| 22 | German résumé LLM screening Turkish-sounding names bias audit GPT Germany labor market study | 1 (Leininger) | 0 |
| 23 | "Staatsangehörigkeit" OR "Herkunft" Large Language Model Bewerberauswahl Experiment Studie 2025 Diskriminierung Namen arabisch türkisch | 0 LLM (human field experiments only) | 0 |
| 24 | Muslim applicants LLM hiring bias religion resume GPT experiment 2025 | 1 (Arcuschin) | 0 |
| 25 | LLM replication Oreopoulos immigrant resumes foreign experience country of origin GPT callback audit | 0 | 0 |
| 26 | "Large Language Models are Geographically Biased" Manvi ICML 2024 proceedings PMLR | verification | - |
| 27 | disaggregated ethnic subgroups LLM hiring bias Asian subgroups ... within-group | 1 (Sakunkoo) | 0 |
| 28 | LLM bias "country-level" heterogeneity Arab nations stereotypes Gulf Levant Maghreb ... | 1 (Kamruzzaman & Kim 2024) | 0 |
| 29 | LLM endorses non-discrimination principle but discriminates in decisions "stated" "behavior" gap ... | 1 (Hoffmann 2026) | - |
| 30 | Palestinian OR Syrian OR Yemeni applicant large language model bias evaluation hiring "nationality" audit results | 0 | 0 |
| 31 | SSRN large language models hiring discrimination national origin experiment economists 2025 GPT résumé immigrants | 2 (Bilon; Busetta et al.) | 0 (levels unknown) |
| 32-33 | Bilon title / author searches for country levels | 0 (levels not found) | - |
| 34 | "national origin" signal LLM screening candidates heterogeneity across countries "MENA" OR "Arab world" fairness audit | 1 (Li et al. 2023, pre-LLM) | 0 |
| 35 | large language model job candidate evaluation Emirati Egyptian Jordanian Saudi nationality differences bias study | 0 | 0 |

### Verification sources

- Crossref REST API: about 45 lookups for DOIs, pages, published titles and full author lists.
- ACL Anthology pages: 2025.gebnlp-1.23, 2025.gebnlp-1.32, 2025.findings-acl.883, 2024.lrec-main.1180.
- PMLR (Manvi 2024), PLOS ONE (Geiger 2025).
- Full-text PDFs (via curl + pdftotext): Salinas 2023, Mao & Zhao 2025, Lippens 2024 (arXiv version), Sorokovikova 2025, Huijzer & Chen 2025, ABLEIST, Kamruzzaman 2024, Tamkin 2023, Venkit 2023, Zhu 2024, Mazeika 2025, MENAValues, Forcada Rodríguez 2025, ArGAN.
- Access failures: tandfonline (403), ACM DL (403), MDPI (403), Semantic Scholar (429).

### Coverage limits

- There was no direct Google Scholar access, and Semantic Scholar was largely rate-limited.
- FAccT/AIES proceedings were reached only through web search and Crossref, not browsed issue by issue.
- SSRN was searched only through the general web engine.
- Non-English searches covered German only; there were no Arabic-language searches.
- Workshop papers and 2026 preprints posted in the last weeks may be missed.
