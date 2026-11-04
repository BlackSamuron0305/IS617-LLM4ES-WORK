# L4 literature notes: is AI / LLM bias against Arab, MENA, North African and Muslim people documented?

Internal research notes, telegraphic. **Not paper prose.** Do not paste into `paper/` (AI-usage rule in `CLAUDE.md`).

- Compiled: 2026-10-04. One pass, one researcher (Claude).
- Companion files: `L4_matrix.csv` (13 rows), `L4_refs.bib` (same 13 keys). Nothing merged into `literature_matrix.csv` or `references.bib`.
- Verification levels as in `literature_review.md`: **fulltext** = relevant sections read; **abstract**; **metadata**. All 13 additions are fulltext. Every DOI checked in Crossref; arXiv items checked on the arXiv abstract page (version history, comments).
- Numbers below were read in the source at the stated level. "Not extracted" = present in the source but not read.

## 1. Bottom line (for the team to phrase themselves)

Premise under test: "bias against Arab / MENA applicants is already documented for LLMs".

- **Hiring / screening decisions: thin and mixed.** Controlled evidence for an Arab group rests on
  - `lippens2024computer` (GPT-3.5, pooled Arab names, -1.41 points on 1-100, ratio 0.85): small penalty, one 2023 model;
  - `hoffmann2026evaluating` (Gemini 2.0 Flash, pooled Arabic male names): about zero on average;
  - `bai2025explicitly` (arXiv version read here): GPT-4 more likely to send Arabic/Muslim-named applicants to the lower-status of two jobs. A relative job-assignment prompt, not a screening score.
  - Everything newer points to null or reversed effects when the group is named explicitly: `bunel2026customer`, `arcuschin2026blind` (full text), `huijzer2025discrimination` (Moroccan: minus under GPT-3.5, plus under GPT-4o), `arif2026grain`.
  - `mohammad2026mirage` cannot be used: its numbers are placeholders (see §4).
- **Other tasks: well documented for generation and stereotypes, mostly 2020-2023 models and pooled groups.** `abid2021persistent`, `hemmatian2023muslim`, `shieh2026intersectional`, `cheng2023marked`, `saeed2024desert`, `saeed2026surfacing`, `kirk2021bias`, `venkit2023nationality`. Direction depends on model vintage, cue (name vs explicit label) and prompt language.
- **Defensible content of the premise:** LLMs reproduce stereotypes about Arabs and Muslims in generated text; evidence that they *penalise Arab applicants in decisions* is one small GPT-3.5 effect plus an implicit-association-style result, against several nulls and reversals. The premise does not hold as "documented for LLM hiring" without that qualifier.

## 2. Key question (gap 5)

**Found: 0.** No study in which an LLM makes a hiring or screening decision and national origin is varied across more than one individual Arab country.

Closest new near-miss: `albaroudi2026addressing` (HITHIRE). 18 Arab nationalities are present in its 350 real CVs, but
- every model-level metric pools them into Arab vs non-Arab;
- it is observational (no clones, qualifications not held fixed);
- the direction of the Arab vs non-Arab gap is reported both ways in the text.
It does not meet conditions (b)+(c) of `novelty_assessment.md` §2. It should still be cited as prior work in an Arab-world labour market.

Two sibling HITHIRE papers exist (metadata only, not read): *Array* 2025, doi:10.1016/j.array.2025.100592 (governance framework); CCIS chapter, doi:10.1007/978-3-032-11352-8_16.

## 3. Additions (13)

| key | strand | what it adds | direction for the Arab / Muslim group |
|---|---|---|---|
| `albaroudi2026addressing` | llm_hiring | Saudi-context CV matcher (Llama 3.1), Arab vs non-Arab pooled | uninterpretable (text contradicts itself) |
| `bunel2026customer` | llm_hiring | 18 LLMs in French, hiring-quota vignette, Moroccan / Portuguese / French vs fictional group | **less** discrimination against real groups than fictional (33.4% vs 43.4%); Moroccan not worse than Portuguese |
| `yashwant2026counterfactual` | llm_hiring | French-context embedding ranker, North-African name cue bundled | within tolerance; cue not isolated |
| `shieh2026intersectional` | arab_mena_llm | 5 models, 500,000 stories, MENA names | against: representation ratio 0.22 in Labor; subordinated roles |
| `cheng2023marked` | arab_mena_llm | GPT-3.5 / GPT-4 personas, Middle-Eastern group | stereotyped (religion, orientalism), plus "positive" mitigation words |
| `hemmatian2023muslim` | arab_mena_llm | Pre-registered Abid replication | weak with explicit label (InstructGPT), stronger with names and in ChatGPT |
| `demidova2024john` | arab_mena_llm | GPT-3.5 / Gemini debates in Arabic, English, Russian | mixed; Middle Eastern among top winners; flips with language |
| `arif2026grain` | arab_mena_llm | Small Llama / Gemma, career advice, resume generation | no consistent direction for Muslim |
| `khorramrouz2026characterizing` | arab_mena_llm | Refusal rates by targeted group | guardrails protect Muslims most (with Jews) |
| `plazadelarco2024divine` | arab_mena_llm | Refusals for religious personas | over-refusal for Muslims in Llama2, near zero in Llama3-70b / GPT-4o |
| `kirk2021bias` | arab_mena_llm | GPT-2 occupation completions | Muslim men and women get low-status jobs; partly not group-specific |
| `ousidhoum2021probing` | arab_mena_llm | BERT / GPT-2 / CamemBERT / AraBERT toxicity probing | Arabs mid-table, not the worst-treated group |
| `parrish2022bbq` | arab_mena_llm | Canonical QA benchmark | no Arab-specific score; one tentative note on Middle Eastern women |

No `nationality_llm` additions: nothing new reported a result for an Arab nationality specifically.

## 4. Problems found in the existing matrix (action for the lead)

1. **`mohammad2026mirage` (arXiv:2606.16562): numbers are placeholders. Do not cite them.** Full text (v1, the only version) says:
   - Table 3 caption: "Numbers are illustrative placeholders";
   - Figures 2-6 captions: "(Illustrative results pending experimental replication.)";
   - Limitations: "The numerical results in this preliminary draft are placeholders";
   - reference list contains entries marked "Placeholder citation – replace with actual reference".
   The 9-22 pp "asymmetry", the 12-34% and the 18-27% are therefore not findings. Affected: `literature_matrix.csv` row; `literature_review.md` §2.4, §2.6, §4 row 18; `novelty_assessment.md` §3 row 13. Suggest removing the row or keeping it as "benchmark design only, no results".
2. **`bai2025explicitly`**: row says "nationality not among categories" (true) but omits an **Arab/Muslim name category** in a hiring-style task. arXiv full text: names such as Mohammed Al-Sheikh, Fatima Al-Ahmed; GPT-4 "more likely to recommend ... applicants with Black, Hispanic, Asian, and Arabic/Muslim names for lower-status jobs"; implicit negativity for Arab names "reduced but not gone"; religion: "small levels of pro-Christian bias over Islamic and Jewish believers". Same paper: GPT-4 answers "not enough info" on 98% of ambiguous BBQ items. So `literature_review.md` §2.1 "only two LLM hiring studies have an explicit Arab group" needs a qualifier (a third, pooled, relative job-assignment task). Read on arXiv:2402.04105, not in the PNAS text. Per-category numbers sit in appendix tables that did not extract cleanly: not quoted.
3. **`arcuschin2026blind`**: row is abstract-level and misses the disconfirming content. Full text:
   - across hiring, loan approval and admissions, "every detected race/ethnicity bias favors the minority-associated group (21 pro-minority vs. 0 pro-majority)" and every gender bias favours women (22 vs 0), six models;
   - loan approval, GPT-3.5-turbo: explicit Muslim over Jewish +0.057, over Buddhist +0.042; Muslim over Christian names +0.035 (approval-rate differences); authors call it a "pro-Muslim ... pattern";
   - Claude Sonnet 4 in loan approval: bias toward minority religious affiliations (0.037);
   - their SALT re-test on Gemma-2-9B-it found no significant demographic biases.
4. **`huijzer2025discrimination`**: row gives no Moroccan-specific result. Full text: coefficients for Moroccan background (reference European-American) are mostly negative under GPT-3.5 and positive under GPT-4o; text calls the Dutch / Mexican / Moroccan / Turkish effects "varied", with only Turkish significantly negative (GPT-3.5, explicit conditions). Column labels of the coefficient table did not extract cleanly, so no single number is quoted. Also: the paper describes Lippens as finding that "in GPT-4 ... Moroccans faced discrimination". That is wrong (Lippens used GPT-3.5 and a pooled Arab name group). Do not copy it.
5. **`saeed2024desert`**: "79% of cases" is the share of model x category cells in which Arabs, not Westerners, were classed as the "loser group" by prompts that ask the model to name a loser group (text: "79.125% of the categories"; Westerners 21.78%). It is not 79% of responses, and the design forces a choice. The matrix outcome "Share of responses biased against Arabs" is imprecise. Read: abstract, §5.1, conclusion.
6. **`kamruzzaman2024nation`**: listed as arXiv preprint. Now published: EMNLP 2025 main, pp. 3660-3678, doi:10.18653/v1/2025.emnlp-main.181 (Crossref).
7. **`chen2026beyond`**: its five ethnocultural conditions are Anglo, First Nations, Chinese, Indian, Vietnamese (arXiv HTML, via page summary only). No Arab group. No change needed; noted because a search result suggested otherwise.

## 5. Search log

KQ = studies meeting the key question. All KQ = 0.

| # | Source | Query / action | Hits | Added or learned |
|---|---|---|---|---|
| W1-W8 | Web (EN, FR, NL) | Arab / Middle Eastern / Muslim names x LLM resume screening; Gulf nationalities x LLM hiring; Muslim / hijab x hiring; FAccT 2025; FR "biais ChatGPT recrutement prénom maghrébin ..."; FR "IA générative recrutement discrimination origine prénom arabe ..."; NL "ChatGPT sollicitatie discriminatie Marokkaanse naam ..." | mostly known audits | **HITHIRE** (W3). FR and NL queries returned press and human audits only (next.ink piece = Bloomberg 2024) |
| W9-W16 | Web (EN) | religion / caste India; "Arabic-sounding" names in Nordic / German / UK / Australian audits; asylum / visa / loan / housing / sentencing; "Middle Eastern" x BBQ / Marked Personas; Arabic resume screening x Jais / ALLaM; GCC / Saudization / kafala; within-Arab job or salary recommendation; MENA countries x résumé experiment | known items; ArabJobs; agentic national bias | none new for KQ |
| W17-W24 | Web (EN, FR) | multilingual resume screening x Arabic; Arab names x implicit bias x hiring; null / reversed results; AIES 2025; five-race-group audits with Middle Eastern; asylum by nationality; FR "ChatGPT prénom Mohamed discrimination ..."; salary / loan advice x Arab or Muslim | – | `bai2025explicitly` Arab category noticed; `demidova2024john`; Arcuschin loan results; ATS preprint |
| W25-W27 | Web (EN) | Kirk NeurIPS record; discrim-eval x religion; Lippens follow-ups | – | no Lippens multi-model follow-up found |
| O1 | OpenAlex boolean | (Arab / Middle Eastern / Maghreb / North African / Muslim) x hiring terms x LLM, 2023+ | 17 | none new (Lippens, MIRAGE, withdrawn Törnberg) |
| O2 | OpenAlex, FAccT 2025 by DOI prefix 10.1145/3715275 (207 papers) | hiring / Arab / Muslim / nationality / religion / migrant | 10 | none relevant |
| O3 | OpenAlex, AIES 2025 by DOI prefix 10.1609/aies.v8 | same terms | 17 | Rao (known), Seth et al. (caste and religion, India; not added), Wilson et al. (race) |
| O4 | OpenAlex, ACM DOIs 2026 | Arab / Muslim / Middle East x LLM | 3 | none relevant |
| O5-O6 | OpenAlex, ACL Anthology 2026 by DOI prefix 10.18653/v1/2026 | (Arab / Muslim / nationality x bias); (hiring / resume / recruitment) | 3; 17 | `khorramrouz2026characterizing`, `arif2026grain` |
| O7 | OpenAlex boolean | Arab / Muslim x LLM x bias x decision terms, 2024+ | 47 | leads only (§8) |
| O8-O9 | OpenAlex boolean | 18 Arab demonyms x hiring x LLM, 2023+; nationality x hiring x LLM x Gulf / Arab terms | 37; 3 | HITHIRE family only. KQ = 0 |
| O10 | OpenAlex boolean | Maghrebi / Moroccan / Algerian / Tunisian / Turkish x LLM x bias x France / Belgium / Netherlands | 22 | none new (Lippens; MBBQ; Öztürk et al.) |
| H1-H6 | HAL API (French repository; first time searched) | FR and EN: biais / discrimination x modèle de langue / LLM x recrutement / embauche / CV; maghrébin / arabe / musulman x LLM x biais; prénom x LLM; stéréotypes x français; hiring x LLM x fairness | 4; 1; 0; 4; 13; 7 | **`bunel2026customer`**; French CrowS-Pairs (screened); Bouchaud & Ramaciotti (screened) |
| A1 | arxiv.org advanced search | hiring terms x LLM x bias, submitted 2026-09-18 to 2026-10-05 | 25 | none relevant (covers "since 2026-09-25") |
| A2 | arxiv.org advanced search | Arab / Middle Eastern / Muslim / MENA / Maghreb x LLM x bias, submitted 2026-06-01 to 2026-10-05 | 17 | Khan et al., Howard et al. (screened, §7) |
| A3 | arxiv.org advanced search | nationality / national origin / immigrant x hiring x LLM, 2025-06-01 to 2026-10-05 | 6 | none new (ABLEIST known) |
| C | Crossref | 10 DOI look-ups, 4 bibliographic queries | – | all 13 entries confirmed; Kamruzzaman now EMNLP 2025; Shieh et al. found via a Kirk query |
| F | Full texts read | HITHIRE; Bunel; Yashwant; Shieh; Cheng; Hemmatian; Demidova; Arif (SALT); Khorramrouz; Plaza-del-Arco; Kirk (arXiv v3); Ousidhoum; Parrish; plus existing-matrix items Bai (arXiv), Arcuschin, MIRAGE, Saeed 2024 (partial), Huijzer (partial) | 18 | §3, §4 |

Stopping point: the last three web queries and the last four OpenAlex filters returned no new relevant study.

## 6. Disconfirming and model-dependent evidence (collected)

- Explicit label, newest models, French: real origin labels (Moroccan) draw less recommended discrimination than a fictional group. `bunel2026customer`.
- Decisions, 2025 models: every detected race/ethnicity bias is pro-minority; GPT-3.5-turbo loan approvals favour Muslim applicants. `arcuschin2026blind` (full text).
- Vintage flip for a Moroccan background: negative under GPT-3.5, positive under GPT-4o. `huijzer2025discrimination` (full text, partial).
- Pooled Arabic names, Gemini 2.0 Flash: about zero. `hoffmann2026evaluating` (already in the matrix).
- Muslim signal in career advice and resume generation: no consistent direction. `arif2026grain`.
- Explicit "Muslim" label after debiasing: weak effect in InstructGPT; names still trigger it; ChatGPT stronger again. `hemmatian2023muslim`.
- Guardrails: highest refusal to produce harmful text about Muslims (and Jews). `khorramrouz2026characterizing`. Over-refusal for Muslim personas in Llama2, gone in Llama3-70b / GPT-4o. `plazadelarco2024divine`.
- Prompt language: Middle Eastern group wins more debates in Arabic prompts; Gemini in Russian the reverse. `demidova2024john`.
- Older masked models: Arabs and Muslims are not the most toxicity-associated groups. `ousidhoum2021probing`.
- Explicit benchmarks saturate: GPT-4 picks "not enough info" on 98% of ambiguous BBQ items. `bai2025explicitly` (arXiv full text); `parrish2022bbq` has no Arab-specific score anyway.
- Positive-sounding stereotypes as a likely mitigation artefact (Middle-Eastern women "independent"). `cheng2023marked`.

## 7. Screened and not added

| Item | Level | Why not added |
|---|---|---|
| Névéol, Dupont, Bezançon & Fort 2022, French CrowS-Pairs (ACL 2022, doi:10.18653/v1/2022.acl-long.583) | fulltext (skim) | results by bias type only; no Arab / Maghrebi group result |
| Khan, Umer, Mahmud & Rothenberg 2026, arXiv:2608.16909 (religious framing in AI financial advice) | abstract | no Muslim-specific direction in the abstract |
| Howard, Su & Fraser 2026, arXiv:2604.09945 (vision-language models; "race-conditional failures" for Middle Eastern persons) | abstract | vision-language; no numbers in abstract |
| Elbouanani, Tuo & Popescu 2026, arXiv:2601.12374 (entity-based audit; Western vs Global South) | abstract | no Arab-specific result in abstract |
| Seth et al. 2025, AIES 8(3):2319-2330 (caste and religion in GPT-4 Turbo stories about India) | abstract | Muslims in India, representation; not Arab |
| Liu et al. 2025, arXiv:2502.17945 (ACL 2025 Findings; multilingual "national bias" in agentic advice) | abstract | about which countries get recommended, not about persons |
| Liang & Mahmoud 2025, arXiv:2512.16029 | abstract | bias by prompt language (Arabic prompts higher), not Arab targets |
| Basu & Chakraborty 2026, arXiv:2603.18530 (ICE-Guard) | abstract | name / race swaps, groups not named; demographic flip rate 2.2% vs authority 5.8% and framing 5.0% |
| Bouchaud & Ramaciotti 2025, HAL hal-05410269 | abstract | linear demographic representations; no Arab-specific result |
| El-Haj 2025, ArabJobs (arXiv:2509.22589; ArabicNLP 2025) | abstract | job-ad corpus (Egypt, Jordan, Saudi Arabia, UAE); gender bias in ads; no LLM decisions about applicants |
| Kitahara & Yamaguchi 2026, arXiv:2609.18106 | fulltext (grep) | race pooled as non-White; no Arab group |
| Heierli & de Spindler 2026, SwissText 2026 | fulltext (grep) | gender only |
| Nghiem et al. 2026, arXiv:2604.19984 (EMNLP 2026); Webster 2025, arXiv:2507.11548; Yu, Park & Moon 2026, arXiv:2603.22714 (EMNLP 2026 main) | abstract | race-gender; no Arab group stated |
| MBBQ (Neplenbroek et al. 2024, arXiv:2406.07243); Öztürk et al. 2023, arXiv:2307.07331 | metadata | not checked for group-level results |

## 8. Unverified leads (not in matrix or bib)

- Hamidavi 2026, "Ten Novel Phenomena in Machine Psychology: ... Ethnically-Cued User Names", Research Square, doi:10.21203/rs.3.rs-10369594/v1. OpenAlex record only; not read; unreviewed.
- Mohammad 2026, "The Audit Regime Gap", OSF, doi:10.17605/osf.io/vnxcy. Same first author as MIRAGE; not read. Treat with the same caution.
- Ismaili 2026, "Whose data, whose culture? ... Moroccan identity across four large language models", *Globalisation, Societies and Education*, doi:10.1080/14767724.2026.2669938. Record only; qualitative discourse analysis.
- Bilon 2025: still not obtained. Not retried in this pass.
- A French-language LLM testing study with Maghrebi first names: none found in HAL or on the web. Absence under this coverage, not proof.
- Any FAccT 2026 or AIES 2026 paper on the topic: proceedings not located (§9).

## 9. Not accessible or not covered

- **arXiv API** (`export.arxiv.org`): HTTP 429, then timeouts, for the whole session. Replaced by arxiv.org abstract pages, PDFs and the advanced-search page. Field-restricted API queries were therefore not run.
- **HAL web pages**: bot wall (Anubis). Used the HAL API for records and the EconomiX site for the Bunel PDF.
- **FAccT 2026 and AIES 2026 proceedings**: not browsed. FAccT 2026 DOI prefix not identified; the ACM-2026 topic filter (O4) returned 3 irrelevant papers. AIES 2026 proceedings not found.
- **EMNLP 2026**: not in the ACL Anthology yet; covered only through arXiv comments ("EMNLP 2026").
- **Semantic Scholar, Google Scholar**: not used.
- **ACM DL, SSRN, tandfonline**: not tried; Springer HTML redirected to login (PDF was open).
- **PNAS text of Bai et al.**: not read; the arXiv version was.
- **Arabic-language databases**: still not searched. **German**: not searched in this pass.
- NeurIPS page numbers for `kirk2021bias` not verified (omitted from the bib).
