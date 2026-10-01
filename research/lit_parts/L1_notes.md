# Literature part 1: LLM hiring audits, audit methodology, human correspondence audits

Scope: (A) LLM and language-model hiring and résumé-screening audits; (B) how counterfactual, paired and forced-choice audits of LLMs are built; (C) HUMAN correspondence audits of Arab, North African, Middle Eastern and Muslim applicants, with a focus on Germany/Europe and on studies that compare many origin groups.
Part 2 covers Arab/MENA/nationality work in LLMs outside hiring and gives the final novelty verdict.

Compiled 2026-09-29/30. Companion files: `L1_matrix.csv` (49 rows) and `L1_refs.bib` (49 entries, same keys).

**Verification levels.** `fulltext` means I read the relevant sections, `abstract` means I read the abstract only, and `metadata` means I confirmed the source exists but did not read its content. Counts: 13 fulltext, 33 abstract, 3 metadata. No unverified source is in the matrix or the bib. Numbers are given only where I read them in the source.

**Human studies are labelled HUMAN.** Their findings must not be presented as if they were LLM findings.

---

## 0. Key points for the design

1. **Critical flag: no LLM hiring study with several individual Arab nationalities.** Within my scope (A–B), I found no controlled LLM hiring or screening experiment that varies more than one individual Arab or MENA national origin. The closest are:
   - `lippens2024computer`: GPT-3.5 CV screening in Flanders. It uses one pooled "Arab" name group plus a Turkish group, and holds nationality constant as "Belgian". Novelty threat: medium.
   - `salinas2023unequal`: explicit nationality in job-recommendation prompts. Jordan is the only Arab country among 20.
   - `tan2026small`: ethnicity signalled through subtle markers, in Singapore.
   - `chen2026beyond`: Australian groups.

   Part 2 should confirm this against the Arab/MENA-specific LLM literature.
2. **Within-Arab heterogeneity is an established HUMAN question.** It is not yet an LLM one. `distasio2024same` (22 origin countries of Muslim applicants; lower callbacks with origin-country authoritarianism and gender inequality) and `koopmans2019taste` (35 origin groups in Germany; cultural value distance predicts penalties) are the human analogues. The contribution must therefore be framed as LLM-specific. These studies also supply candidate moderators for exploratory analysis.
3. **Human evidence mostly pools "Arab/Maghrebi/Middle Eastern".** The standard human benchmark (`lippens2023state`: DR 0.5937, roughly a 41% lower callback chance) pools these groups, and so do most single-country audits (`carlsson2007evidence`, `blommaert2014discrimination`, `arai2016reverse`). That pooling is exactly what our design takes apart.
4. **An explicit attribute field is a stronger signal than names, and a more obvious test.**
   - Explicit fields enlarge effects: `rozado2026gender` (gender field) and `tamkin2023evaluating` (explicit vs names).
   - Transparent audits are recognised, and models tie identical-content pairs (`vohra2026audit`).
   - Side-by-side comparisons trigger safeguards that isolated prompts avoid (`lippens2024computer`).

   This supports keeping the independent-evaluation arm primary and pairing *different* base CVs in forced choice, as the contract already specifies.
5. **The nationality line is also a citizenship signal.** In humans, lacking citizenship carries a large penalty (`quillian2026racialized`). Arab-vs-German contrasts therefore mix origin with citizenship. Within-Arab contrasts hold non-EU citizenship constant, which is one more reason to make them primary. Polish serves as a non-German, EU-citizen benchmark.

---

## A. LLM and language-model hiring audits

**`lippens2024computer`: Lippens 2024, *Computers in Human Behavior: Artificial Humans* (fulltext). The most important precedent.**
- What it did:
  - GPT-3.5 (13 June 2023 snapshot) rated fictitious CVs against 1,920 real Flemish vacancies, giving 34,560 vacancy–CV combinations.
  - Names signalled nine groups (Arab, Asian, Black American, Central African, Dutch, Eastern European, Hispanic, Turkish, White American) crossed with gender.
  - The nationality field was always "Belgian". Prompts were in Dutch; scores ran from 1 to 100.
  - Temperature varied between 0 and 1.5 in about two-fifths of prompts.
- Results:
  - Every group scored below Dutch-named candidates, by about −0.96 to −2.42 points. Arab was −1.41 (SE 0.21) and Eastern European was the largest penalty.
  - At a cutoff of 75, the discrimination ratio was 0.85 for Arabs and 0.86 for Turks. These are smaller penalties than human meta-analytic ratios.
  - Isolated prompts bypassed safeguards that appeared when candidates were compared directly.
- For us:
  - Supports the independent-evaluation arm, a European setting, and Turkish as a benchmark.
  - Threat: "LLMs penalise Arab applicants in European CV screening" is already shown. We are different because we use an explicit nationality signal instead of names, 22 individual origins instead of one pooled group, a German setting, several open-weight models, and a within-Arab estimand.

**`rozado2026gender`: Rozado 2026, *PeerJ CS* (fulltext of arXiv v2).**
- What it did:
  - 22 LLMs, 70 professions and 10 job descriptions each, choosing between pairs of CVs.
  - Each pair was shown twice with names swapped, giving 30,800 decisions (30,690 analysed).
- Results:
  - Female-named candidates were chosen 56.9% of the time, and adding an explicit gender field increased this.
  - The first-listed candidate was chosen 63.5% of the time; 21 of 22 models were individually significant.
  - Rating CVs one at a time showed only a negligible gender effect.
  - Temperature was drawn uniformly between 0 and 1 for each pair, and the same value was used for both orders.
- For us:
  - Supports the quad design (swap attributes and swap order).
  - Shows that explicit fields amplify effects.
  - Shows that pairwise and isolated designs can disagree, so both arms are needed.
  - The position bias is large enough that order has to be cancelled by design, not just controlled in analysis.

**`armstrong2024silicon`: Armstrong et al. 2024, EAAMO (fulltext).**
- What it did: GPT-3.5; 32 names plus two "anonymous" controls; 10 occupations and 3 prompt types; 50 trials per resume and prompt, giving 48,000 scores. Name was analysed as a random effect.
- Results:
  - The anonymous controls behaved inconsistently and were dropped.
  - When GPT generated resumes, those for Asian and Hispanic names carried immigrant markers such as non-native English and non-US education.
- For us:
  - Precedent for treating repetitions as within-stimulus.
  - Warns that our `not_stated` control is not a neutral baseline.
  - Supports holding languages constant.

**`gaebler2024auditing`: Gaebler et al. 2024, *Behavioral Science & Policy* (fulltext of arXiv version).**
- What it did: correspondence-style audit of 8 models on real K-12 teaching applications, with names and pronouns manipulated.
- Results:
  - Moderate disparities, with models slightly favouring women and non-White candidates.
  - Disparities persisted when an EEOC anti-discrimination statement was added (tested on GPT-3.5). Blinding names barely changed them, and models inferred demographics from blinded materials.
  - The authors discuss the limits of correspondence audits for algorithms.
- For us:
  - The neutrality paragraph may not remove effects.
  - The direction may reverse compared with human audits, so hypotheses must be two-sided.

**`salinas2023unequal`: Salinas et al. 2023, EAAMO (fulltext).**
- What it did:
  - ChatGPT and LLaMA at temperature 0.8.
  - Explicit country in the prompt: a laid-off friend in the US who "may have to go back to <COUNTRY>".
  - 20 nationalities that ChatGPT itself generated as "common nationalities" (Jordan is the only Arab country), crossed with 2 pronoun genders, with 50 generations per cell.
- Results: Mexico was an outlier (low-paying jobs, lowest salaries). The baseline with no nationality was also an outlier.
- For us:
  - Closest precedent for an explicit nationality manipulation in an employment prompt.
  - The omission baseline is not neutral, which supports using German as the reference and treating `not_stated` as descriptive.
  - It does not examine Arab heterogeneity. Novelty threat: low.

**`an2025measuring`: An, Huang, Lin & Tai 2025, *PNAS Nexus* (abstract).**
- What it did: five models scored about 361,000 resumes with randomised race × gender identities.
- Results: higher scores for women and lower scores for Black men, amounting to about 1–3 percentage-point hiring gaps at a threshold.
- For us: supports reporting both the score and the interview decision, plus threshold-based gaps.

**`an2024large`: An, Acquaye, Wang, Li & Rudinger 2024, ACL (abstract).**
- What it did: a name-conditioned task asking the model to write an acceptance or rejection email.
- Results: White names favoured over Hispanic names, but group rankings shifted across templates.
- For us: prompt sensitivity, which supports frozen, hashed templates and several prompt conditions.

**`wilson2024gender`: Wilson & Caliskan 2024, AIES (abstract plus erratum).**
- What it did: resume retrieval with text-embedding (MTE) models, not instruction-following LLMs.
- Results: White-associated names favoured in 85.1% of cases.
- **Erratum (arXiv v3, 29 Aug 2026):** a code bug inverted the gender-only results. Race and intersectional results are unaffected and were replicated by an independent team.
- For us: cite only the race and intersectional findings. It also shows that name frequency and document length matter, which supports holding format constant across clones.

**Other A sources (abstract level unless noted).** For us, taken together, these point to two-sided tests, model-version logging, and a positive control for qualification tier.
- `iso2025evaluating` (NAACL Industry 2025): explicit gender and race bias has shrunk in recent models, while education bias remains.
- `veldanda2023emily`: arXiv preprint and NeurIPS 2023 workshop. Found LLMs robust on race and gender, with differences on pregnancy and political affiliation.
- `nghiem2024you` (EMNLP 2024): more than 750,000 prompts. Models preferred White female names, and salaries varied by up to 5%.
- `wang2024jobfair` (Findings EMNLP 2024): separates bias in the average score from bias in the spread of scores, and taste-based from statistical bias.
- `wen2025faire` (preprint): scoring and ranking benchmark.
- `tan2026small` (preprint, states EMNLP 2026): language markers alone let models infer ethnicity, and asking for explanations may amplify bias. For us, this justifies never listing Arabic.
- `leininger2026fairness` (German-language resumes, Qwen3): weak ethnicity leakage.
- `gao2026can` (14 models): 2024-and-later models show null or pro-Black gaps, so reversals and model vintage matter.
- `karvonen2025robustly` (fulltext): anti-bias prompts work in minimal settings but fail once realistic company context is added. For us, a neutrality null in our minimal job ads may not generalise.
- `castleman2026measuring`: models often fail to pick the more qualified CV and do not abstain on equally qualified ones.
- `pavlopoulos2026minimal` (Analytics 2026): positive control, equivalence tests and mixed models. The open-weight model reacted to explicit minority signals.
- `yin2024bloomberg` (Bloomberg journalism, metadata only): cite as journalism only.

## B. How counterfactual audits of LLMs are built

**Name-based vs attribute-based manipulation.**
- Most LLM audits copy the name paradigm from `bertrand2004emily`: `an2024large`, `armstrong2024silicon`, `nghiem2024you`, `lippens2024computer`, `gaebler2024auditing`.
- Explicit attributes give larger effects: `tamkin2023evaluating` (fulltext) and `rozado2026gender`. They also avoid confounds from name frequency and perceived class (`wilson2024gender`).
- The cost is higher test transparency (`vohra2026audit`).
- Our explicit `Nationality:` line is ecologically natural on German CVs. It estimates the total effect of the national-origin signal, not an ethnic-name effect.

**Forced choice and position bias.**
- LLMs systematically prefer one position:
  - `rozado2026gender`: first-listed candidate chosen 63.5% of the time.
  - `yin2026fragile` (PNAS Nexus 2026): order effects depend on quality. With high-quality options the first is favoured; with lower quality, later ones are.
  - `vohra2026audit`: first-listed candidates gain 0.11 rank positions, about as much as the largest demographic effect.
  - General LLM-judge evidence: `wang2024large` and `zheng2023judging`.
- Design response: show both orders and swap attributes (our quads). Pre-register order as a design check. Test order × qualification tier, because `yin2026fragile` predicts that order effects change with quality.

**Ties, refusals and verdict space.**
- `chen2026beyond` (fulltext): forbidding ties produced an apparent selection-rate ratio of 0.39. Permitting ties produced 94% or more ties in 7 of 9 models.
- `vohra2026audit`: models tie every identical-content pair.
- `castleman2026measuring`: models do not reliably abstain when candidates are equally qualified.
- Design response: our choice field is deliberately not constrained. Pre-register how ties and refusals are coded (primary: NA and report the rate; sensitivity: count as 0.5). Pairing *different* CVs of the same tier, as specified, avoids identical-content ties.

**Repeated sampling, temperature and pseudo-replication.**
- `atil2024nondeterminism`: "deterministic" settings still vary from run to run, with accuracy swings of up to 15%. `vohra2026audit` confirms that temperature 0 is not deterministic.
- How prior audits handled sampling:
  - `lippens2024computer`: mixed temperatures, temperature as a control.
  - `rozado2026gender`: random temperature per pair.
  - `salinas2023unequal`: temperature 0.8 with 50 generations.
  - `armstrong2024silicon`: 50 trials with name as a random effect.
  - `pavlopoulos2026minimal`: mixed models for clustered repeated evaluations.
- `miller2024adding` (fulltext): standard errors that ignore clustering can be too small by a factor of up to about 3. Resampling helps less and less with each extra sample.
- `hurlbert1984pseudoreplication` (metadata) is the classic definition of pseudo-replication.
- Design response: the 5 repetitions are within-stimulus replicates. The unit is base CV × nationality. Use random effects or clustering for base CV, occupation and quad, and analyse paired within-CV contrasts.

**Many units, noisy ranks.**
- `kline2022systemic`: unit-level heterogeneity estimated with false-discovery-rate control.
- `kline2024discrimination`: empirical-Bayes grades that show uncertainty.
- Both are good templates for reporting 22 nationality effects without over-reading raw ranks. This fits the pre-registered hierarchical model by sub-region.

**Prompt interventions.**
- `tamkin2023evaluating`: "illegal to discriminate" and "ignore demographics" instructions work.
- `gaebler2024auditing`: an EEOC statement did not remove disparities.
- `karvonen2025robustly`: instructions fail in realistic contexts.
- Expect the effect of the neutrality paragraph to depend on the model, and state clearly that our job ads are minimal.

## C. HUMAN correspondence audits (human findings only)

**Germany.**
- `koopmans2019taste` (HUMAN, fulltext): German arm of the GEMM project.
  - Design: German-born applicants from 35 groups, almost 6,000 vacancies. Ethnicity was signalled by name plus a second mother tongue; phenotype by photo; religion by a volunteering association.
  - Callback: 60% for German origin, 47% for Turkish. Several groups fell below Turkish, including Iraqi and Moroccan; Albanian was lowest at 41%.
  - Small groups had only about 100 applications each, so single-group effects were not estimated.
  - Cultural value distance explained group differences better than group education.
  - For us: supports origin-level heterogeneity and a theory to motivate it. The LLM design can afford far larger samples per origin.
- `kaas2012ethnic` (HUMAN): Turkish names; German names got about 14% more callbacks. The gap disappeared with favourable reference letters, which predicts smaller effects for strong-tier CVs.
- `weichselbaumer2020multiple` (HUMAN): women with a Turkish migration background were penalised, more so with a headscarf.

**Multi-country, multi-origin (GEMM).**
- `lancee2021ethnic` (HUMAN): N = 19,181; 53 groups in 6 countries.
- `distasio2021muslim` (HUMAN, fulltext): 15 origin countries with sizeable Muslim populations, including Egypt, Iran, Iraq, Lebanon, Morocco and Turkey, in five countries including Germany. The penalty for coming from such a country without any religious signal ("Muslim by default") was significant everywhere except Spain. Disclosed Muslim affiliation added a further penalty.
- `distasio2024same` (HUMAN, abstract): 22 origin countries; authoritarianism and gender inequality in the origin country predict lower callbacks, for men.
- `distasio2020understanding` (HUMAN, methodological): the case for designs that cover many origin groups.
- For us: an Arab nationality may carry a "Muslim by default" reading. That belongs inside our total effect, and any claim about mechanism stays exploratory.

**Pooled Arab-name audits.** For us, these are the typical pooled comparisons that we disaggregate.
- `carlsson2007evidence` (HUMAN, Sweden): every fourth employer discriminates.
- `arai2016reverse` (HUMAN, Sweden): Arabic-named men are penalised more than Arabic-named women.
- `blommaert2014discrimination` (HUMAN, Netherlands, 636 resumes): Dutch-named applicants 60% more likely to get a positive reaction.
- `adida2010identifying` (HUMAN, France): a Muslim candidate is 2.5 times less likely to get a callback than a Christian one with the same origin.

**Meta-analyses.**
- `lippens2023state` (HUMAN, fulltext): Arab/Maghrebi/Middle Eastern discrimination ratio 0.5937 [0.5548, 0.6353], the largest ethnic penalty. Western Asian: 0.7508.
- `bartkoski2018meta` (HUMAN): discrimination is stronger for "Arab" than for "Muslim" targets, and primary studies confuse the two. For us, this supports keeping the construct precise.
- `zschirnt2016ethnic` (HUMAN): 738 tests in 43 studies.
- `quillian2019countries` (HUMAN): Germany is among the lower-discrimination countries.
- `quillian2026racialized` (HUMAN): lacking citizenship or holding a foreign degree carries large penalties.
- `thijssen2022discrimination` (HUMAN): penalties for Muslim groups are similar across countries.

---

## Design implications (supports / threatens)

**Supports.**
- Explicit nationality field instead of names.
- Quads with both orders.
- Pairing different CVs from the same tier.
- Independent evaluation as the primary arm.
- Languages held constant, with no Arabic.
- German as the reference, and `not_stated` as descriptive only.
- Hierarchical and empirical-Bayes reporting across 22 origins.
- Repetitions treated as within-stimulus.
- Temperature 0.7 with 5 repetitions and logged seeds.
- Sensitivity analysis excluding the three contested members.

**Threats.**
1. The Arab-vs-native LLM penalty is not new (`lippens2024computer`), and within-origin heterogeneity is a known human question (`distasio2024same`, `koopmans2019taste`).
2. The explicit field makes the audit obvious (`vohra2026audit`), which could lead to masking in forced choice.
3. Forced-choice results can be driven by the tie and position rules (`chen2026beyond`).
4. The nationality line mixes origin with citizenship (`quillian2026racialized`).
5. Directions may reverse after safety training, possibly by different amounts for more salient origins. Mechanism claims stay exploratory.
6. The neutrality effect may be specific to our minimal job ads (`karvonen2025robustly`).
7. Listing a nationality with no matching language (for example, a Moroccan applicant listing German and English only) may look implausible. This is a trade-off already fixed by the design contract.

## Excluded or flagged (not in matrix or bib)

- **Törnberg (2026), arXiv:2603.13891, "LLMs reproduce racial stereotypes when used for text annotation": WITHDRAWN** by the author because of a confound in how stimuli were assigned. It reported that 19 models rated Arab-named applicants as *more* hireable. Do not cite.
- **"First Come, First Hired?"** (MIT Computational Law Report, on position bias): the page returned 403, so authors and content are unverified. Left out.
- Handed to part 2 (nationality or Muslim identity in LLMs outside core hiring screening):
  - Germani & Spitale, *Science Advances* 2025 (doi 10.1126/sciadv.adz2924): texts attributed to "a person from China" drew less agreement from models (reported via t3n; not verified by me).
  - MIRAGE, arXiv:2606.16562: anti-Muslim bias, including hiring screens.
  - Mao & Zhao, arXiv:2506.21574: LLMs in immigration decisions, with nationality stereotypes.
  - "Representational Harms … Against Global Majority Nationalities", arXiv:2604.22749.
- Seen but not included (low relevance): Nghiem et al. 2026 (arXiv:2604.19984); Bone et al. 2026, COLM (arXiv:2609.22169); Kim et al. 2026, *J. Personnel Psychology* (doi 10.1027/1866-5888/a000388); Rao et al. 2025, AIES (arXiv:2508.16673); Seshadri et al. 2025 (arXiv:2501.04316); Salinas, Haim & Nyarko 2024 (arXiv:2402.14875); Quillian et al. 2017, PNAS.

## Seed citation checks

- **An et al., PNAS Nexus 2025: correct.** Authors are Jiafu An, Difang Huang, Chen Lin and Mingzhu Tai; 4(3), pgaf089. **Beware:** a *different* "An et al." (Haozhe An, … Rudinger) is at ACL 2024. Do not merge them.
- **Iso et al., NAACL Industry 2025: correct.** Pages 672–683.
- **Armstrong et al., "The Silicon Ceiling": correct.** EAAMO 2024, doi 10.1145/3689904.3694699.
- **Wilson & Caliskan: venue correct (AIES 2024, vol. 7, pp. 1578–1590).** It audits embedding retrieval models, not generative LLMs, and **its gender-only results are inverted per the 2026 erratum.**
- **Veldanda et al. ("Emily and Greg …"): an arXiv preprint (2310.05135).** The peer-reviewed workshop version carries a different title: "Investigating Hiring Bias in Large Language Models" (NeurIPS 2023 R0-FoMo).
- **Gaebler et al.: the published title differs from the arXiv title.** Published: "Auditing large language models for race & gender disparities: Implications for AI-based hiring", *Behavioral Science & Policy* 10(2), 46–55 (print 2024, online 2025). arXiv title: "Auditing the Use of Language Models to Guide Hiring Decisions".
- **Rozado 2025 is now published:** *PeerJ Computer Science* 12:e3628 (2026).
- **Yin, Vardi & Choudhary ("Fragile preferences") is now published:** *PNAS Nexus* 5(8), pgag246 (2026).
- **JobFair: correct.** Findings of EMNLP 2024.
- **FAIRE: an arXiv preprint only.**
- **Nghiem et al.: correct.** EMNLP 2024.
- **Salinas et al.: correct.** EAAMO 2023.
- **Bloomberg 2024: journalism.** Authors are Yin, Alba and Nicoletti, confirmed through secondary pages.
- **Human seeds: all verified.**
  - Koopmans, Veit & Yemane: ERS 42(16), 233–252 (2019).
  - Kaas & Manger: GER 13(1) (2012).
  - Weichselbaumer: ILR Review 73(3) (2020 print; online 2019).
  - Adida, Laitin & Valfort: PNAS 2010.
  - Carlsson & Rooth: Labour Economics 2007.
  - Zschirnt & Ruedin: JEMS 2016.
  - Lancee: JEMS 47(6) 2021 (online 2019). Cite the print year consistently. The GEMM codebook (Lancee et al.) is a separate SSRN item from 2019.

---

## Search log (reproducible)

All searches were run 2026-09-29 to 2026-09-30 (Europe/Berlin), by script or tool from this session.

**arXiv API** (`export.arxiv.org/api/query`, sortBy=relevance):
1. `all:resume AND all:bias AND all:language` (max 50)
2. `all:hiring AND all:"language models" AND (all:nationality OR all:"national origin" OR all:ethnicity OR all:religion)`
3. `all:"large language models" AND all:hiring AND all:nationality`
4. `all:LLM AND all:recruitment AND all:migrant`
5. `all:LLM AND all:resume AND all:"country of origin"`
6. `all:LLM AND all:hiring AND all:Arab`
7. `all:LLM AND all:hiring AND all:Muslim`
8. `all:LLM AND all:hiring AND all:immigrant`
9. `all:LLM AND all:candidate AND all:screening AND all:German`
10. `all:"correspondence" AND all:audit AND all:"language models" AND all:hiring`
11. `abs:nationality AND abs:hiring AND abs:LLMs`
12. `abs:nationality AND abs:resume`
13. `abs:nationality AND abs:recruitment AND abs:language`
14. `abs:"national origin" AND abs:language AND abs:model`
15. `abs:ethnicity AND abs:resume AND abs:LLM`
16. `abs:Europe AND abs:hiring AND abs:LLM AND abs:discrimination`
17. `abs:correspondence AND abs:LLM AND abs:discrimination`
18. `abs:"position bias" AND abs:hiring`
19. id_list lookups for abstracts: 2603.05189, 2609.22188, 2307.08624, 2608.26899, 2606.28978, 2406.10486, 2602.10117, 2403.15281, 2407.20371, 2504.01420, 2406.15484, 2503.19182, 2310.05135, 2505.17049, 2506.14092, 2309.07664, 2508.16673, 2609.16501, 2609.09048, 2603.13891, 2507.02087, 2604.19984, 2404.03086, 2405.04412, 2312.03689, 2402.14875, 2411.00640, 2308.02053, 2406.12232, 2501.04316, 2408.04667, 2506.21574, 2609.18106, 2507.11548, 2602.18550, 2506.10922, 2606.16562, 2305.17926, 2306.05685, 2308.11483, 2609.22169

**Semantic Scholar API** (`api.semanticscholar.org/graph/v1`):
- `paper/search?query=large+language+models+hiring+bias+resume+audit` returned HTTP 429 (rate-limited, no results).
- `paper/DOI:10.1016/j.rssm.2019.100463` (abstract obtained).
- `paper/DOI:10.1093/sf/sot124` (abstract withheld by publisher; read from the repository PDF instead).

**Crossref** (`api.crossref.org/works?query.bibliographic=…`, plus `works/<DOI>` for dates):
- LLM seeds: "Measuring gender and racial biases in large language models intersectional evidence automated resume evaluation"; "The Silicon Ceiling auditing GPT race gender disparities hiring"; "You Gotta be a Doctor Lin name-based bias large language models employment recommendations"; "unequal opportunities large language models demographic bias job recommendations"; "Auditing the use of language models to guide hiring decisions"; "Gender and positional biases in LLM-based hiring decisions Rozado"; "Rozado gender positional biases LLM hiring"; "Are Emily and Greg still more employable than Lakisha and Jamal algorithmic hiring bias ChatGPT Veldanda"; "JobFair benchmarking gender hiring bias large language models"; "Gender race intersectional bias resume screening language model retrieval Wilson Caliskan"; "Evaluating bias in LLMs for job-resume matching gender race education Iso"; "Do large language models discriminate in hiring decisions race ethnicity gender An Rudinger"
- Human audits: "Koopmans Veit Yemane taste or statistics comparative analysis ethnic discrimination Germany field experiment"; "Kaas Manger ethnic discrimination in Germany's labour market field experiment"; "Weichselbaumer multiple discrimination against female immigrants wearing headscarves"; "Adida Laitin Valfort identifying barriers to Muslim integration France"; "Carlsson Rooth evidence of ethnic discrimination Swedish labor market field experiment"; "Quillian Heath Pager meta-analysis field experiments hiring discrimination countries"; "Zschirnt Ruedin ethnic discrimination in hiring decisions meta-analysis correspondence tests 1990-2015"; "Lancee ethnic discrimination in hiring comparing groups across contexts cross-national field experiment"; "Di Stasio Lancee understanding why employers discriminate where and against whom multi-group field experiments"; "Lippens Vermeiren Baert state of hiring discrimination meta-analysis correspondence experiments"; "Blommaert Coenders van Tubergen discrimination of Arabic-named applicants Netherlands internet-based field experiment"; "Arai Bursell Nekby reverse gender gap ethnic discrimination Arabic names"; "Bartkoski meta-analysis of hiring discrimination against Muslims and Arabs"
- Methodology: "Large language models are not fair evaluators"; "Large language models sensitivity to the order of options in multiple-choice questions"; "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena"; "Fragile preferences order effects large language models Yin Vardi Choudhary"; "Evaluating and mitigating discrimination in language model decisions Tamkin"; "What's in a name auditing large language models for race and gender bias Haim Salinas Nyarko"; "Bertrand Mullainathan Are Emily and Greg more employable American Economic Review 2004"; "Kline Rose Walters systemic discrimination among large U.S. employers"; "Kline Rose Walters a discrimination report card"; "Hurlbert pseudoreplication design ecological field experiments"

**OpenAlex** (`api.openalex.org/works/doi:<DOI>`), used for abstracts and open-access locations of:
10.1080/01419870.2019.1654114, 10.1080/1369183x.2019.1622744, 10.1080/1369183x.2019.1622826, 10.1093/sf/soag028, 10.1177/01979183211045044, 10.1080/1369183X.2023.2286212, 10.1093/pnasnexus/pgaf089, 10.1093/pnasnexus/pgag246, 10.1145/3689904.3694699, 10.1177/23794607251320229, 10.7717/peerj-cs.3628, 10.1111/j.1468-0475.2011.00538.x, 10.1177/0019793919875707, 10.1073/pnas.1015550107, 10.1016/j.labeco.2007.05.001, 10.1073/pnas.1706255114, 10.15195/v6.a18, 10.1080/1369183x.2015.1133279, 10.1016/j.euroecorev.2022.104315, 10.1093/qje/qjac024, 10.1257/aer.20230700, 10.1016/j.rssm.2019.100463, 10.1093/sf/sot124, 10.1111/imre.12170, 10.1027/1866-5888/a000388, 10.3390/analytics5030030, 10.25035/pad.2018.02.001

**Web search** (WebSearch tool):
- "LLM hiring bias nationality country of origin resume audit large language models 2025"
- "large language models resume screening Arab applicants discrimination experiment"
- "LLM recruiter bias migration background Germany CV experiment ChatGPT Bewerbung Diskriminierung"
- "Koopmans Veit Yemane "Taste or statistics" correspondence study Germany thirty-five ethnic groups Middle East North Africa callback results pdf"
- "Carlsson Rooth 2007 Labour Economics "Middle Eastern" names Swedish labor market field experiment callback 50 percent abstract"
- ""nationality" LLM "resume" OR "CV" screening bias experiment "Syrian" OR "Egyptian" OR "Moroccan" large language model"
- "arXiv 2025 LLM hiring discrimination religion Muslim Christian candidate resume counterfactual audit"
- "Bloomberg 2024 OpenAI GPT recruiter tool tests show racial bias resume ranking names analysis"
- ""Leon Yin" "Davey Alba" "Leonardo Nicoletti" OpenAI GPT recruiter racial bias March 2024"
- "LLM bias "Arab countries" nationality hiring evaluation "Saudi" "Emirati" "Yemeni" language model audit"
- ""within-Arab" OR "intra-Arab" heterogeneity bias large language models nationality"
- "LLM job applicant evaluation "country of origin" explicit nationality field CV experiment GPT-4 Llama bias 2025 2026"
- "Veldanda Grob Thakur Pearce Tan Karri Garg "Emily and Greg" LLM hiring bias published venue NeurIPS workshop 2023 "Investigating Hiring Bias in Large Language Models""
- "Studie ChatGPT Bewerbungen Diskriminierung arabischer Name Staatsangehörigkeit KI Personalauswahl Experiment 2025"
- "LLM hiring audit refugees Syrian Ukrainian applicants large language model bias experiment"
- "Princeton 2026 study LLM hiring agents develop stereotypes from experience discriminate more than humans applicants arXiv"
- "LLM resume screening bias MENA applicants Gulf Levant Maghreb nationality comparison study"
- ""large language model" hiring "Lebanese" "Moroccan" "Egyptian" "Syrian" candidates bias audit"

**Full texts read (PDF, extracted with pdftotext):**
- Koopmans et al. 2019 (EconStor open-access version)
- Di Stasio et al. 2021 (EconStor)
- Lippens et al. 2023 (UGent biblio open-access version)
- Blommaert et al. 2014 (Radboud repository; first page and abstract)
- arXiv PDFs: 2309.07664v3, 2505.17049v2, 2308.02053v2, 2404.03086v1, 2312.03689v1, 2407.20371v3, 2405.04412v3, 2506.10922v1, 2609.09048v1, 2609.16501v1, 2411.00640v1

**WebFetch pages:**
- Read successfully: RePEc and IZA DP 2281 abstract pages (Carlsson & Rooth); ML Anthology page for Veldanda 2023; Bloomberg GitHub repository README; t3n news pages (used only to identify pointers).
- Returned 403: tandfonline, sciencedirect, peerj.com, bloomberg.com, law.mit.edu, hogrefe, the UU and EUI repositories.
