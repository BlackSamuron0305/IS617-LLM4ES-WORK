# Novelty falsification draft (L2)

Internal analysis, not report prose (see AI-usage rule in CLAUDE.md). Written 2026-09-30 by the part-2 literature pass. Sources and keys are in `L2_matrix.csv` and `L2_refs.bib`; the full search log is in `L2_notes.md`.

## 1. Claim under test

> "Existing LLM hiring audits primarily examine broad race/gender categories, while Arab/MENA LLM audits focus primarily on stereotypes, cultural alignment, or safety. We investigate whether LLM hiring decisions exhibit systematic heterogeneity across individual Arab national-origin signals."

Split into three testable parts:

- **C1.** LLM hiring audits mostly vary broad race and gender categories.
- **C2.** Arab/MENA LLM work mostly measures stereotypes, cultural alignment or safety.
- **C3 (the contribution).** No prior study tests, in LLM hiring decisions, whether outcomes differ systematically across *individual* Arab national-origin signals.

## 2. Search strategy (summary)

- **Target:** any study that (a) has an LLM make a hiring, screening or comparable allocative decision about a person, (b) manipulates national origin, and (c) includes more than one individual Arab country. Near-misses were also recorded: one pooled "Arab" group, Arab countries in non-hiring tasks, or many countries in non-decision tasks.
- **Sources:**
  - arXiv API: 23 boolean title/abstract queries plus about 60 ID lookups.
  - General web search: 35 queries, in English and German.
  - OpenAlex: 5 queries.
  - Semantic Scholar: 12 attempted, 3 answered; the rest failed on rate limits.
  - ACL Anthology pages; Crossref for verification of every entry.
  - Full-text PDF checks for the 12 most relevant papers.
- **Phrasings covered:** nationality/country-of-origin/national-origin × hiring/resume/CV/recruitment/job; Arab/Middle Eastern/MENA/Gulf/Levant/Maghreb applicants; individual demonyms (Syrian, Egyptian, Saudi, Emirati, Palestinian, Yemeni, Moroccan, Jordanian); migrant/refugee/expatriate; within-group/intra-regional heterogeneity; disaggregation; German terms (Staatsangehörigkeit, Herkunft, Bewerbung, Diskriminierung).
- **Not covered:** Google Scholar directly; most of Semantic Scholar; Arabic-language queries; issue-by-issue browsing of FAccT/AIES; SSRN except via the web engine.

## 3. Closest threats

| Threat | What it does | Why it does not pre-empt C3 |
|---|---|---|
| Lippens 2024 (CHB: Artificial Humans) [fulltext] | GPT-3.5 CV-screening correspondence audit; 9 name-signalled groups incl. **one pooled "Arab"** group and Turkish; Arab-named applicants penalised | Arab is not disaggregated; names not a nationality field; one model; Dutch frame. It is the pooling our design tests. |
| Mao & Zhao 2025 (arXiv) [fulltext] | GPT-3.5/4 immigration-admission DCE with 10 origins incl. **Iraq, Sudan, Somalia**; most origin coefficients n.s.; interviews show origin-based reasoning despite stated neutrality | Not hiring; 3 Arab levels; no within-Arab estimand; preprint. |
| Zahraei et al. 2025, MENAValues (arXiv) [fulltext] | Cultural-value alignment across **14 Arab states** (+Iran, Turkey); clear country-level inequity; models **collapse Arab countries into one cluster** under Arabic prompts | Values, not decisions about people. But it pre-empts "within-Arab heterogeneity" as a general novelty. |
| Salinas et al. 2023 (EAAMO) [fulltext] | Job recommendations for 20 nationalities (+ no-nationality baseline) | One Arab country (Jordan); recommendations, not screening. |
| Forcada Rodríguez et al. 2025 (GeBNLP) [fulltext] | Occupation recommendations for 25 countries incl. Morocco and Saudi Arabia; German among prompt languages | Two Arab countries; not screening. |
| Huijzer & Chen 2025 (arXiv) [fulltext] | Tamkin-style decisions with Moroccan/Turkish/Dutch backgrounds plus mitigation instructions | One Arab origin; generic decisions; no heterogeneity estimand. |
| Keleg 2025 (C3NLP) [abstract] | Position paper: the Arab cultural-homogeneity assumption is invalid but widespread in LLMs | Conceptual only, but it means the critique itself is not ours. |
| Venkit et al. 2023 (EACL) [fulltext] | 193 demonyms; Libya, Sudan and Tunisia among the 5 most negative in GPT-2 stories | Generation sentiment only, old model. |
| Sakunkoo & Sakunkoo 2025 (arXiv) [abstract] | Disaggregates "Asian" in LLM status rankings | Shows the disaggregation logic is established; different group and setting. |
| Bilon 2025 (J. Decision Systems) [metadata] | ChatGPT hiring study with a national-origin factor | **Country levels unverified.** This is the one open item that could raise the threat. |

## 4. Verdict (conservative)

- **C3 is not falsified within our coverage.** We found no study that runs a controlled LLM hiring or CV-screening experiment varying national origin across multiple individual Arab countries, and none that estimates heterogeneity among them. Coverage: arXiv, a general web engine, OpenAlex, ACL Anthology and partial Semantic Scholar, searched 2026-09-29/30 in English and German. The closest hiring audit (Lippens 2024) pools "Arab" into one category. Studies that include several individual Arab countries do so for immigration admission (Mao & Zhao: Iraq, Sudan, Somalia), job or occupation recommendation (Salinas: Jordan; Forcada Rodríguez: Morocco, Saudi Arabia), text generation (Venkit; Zhu) or cultural values (MENAValues). This is absence of evidence under stated coverage, not proof of absence. The open items are Bilon 2025 and Busetta et al. 2025, whose national-origin levels could not be checked.
- **C1 is supported but overstated as written.** A 10-year review of 189 AI/LLM bias papers finds 79.9% study gender and 30.2% race/ethnicity, against 13.2% nationality (Ghosh & Wilson, AIES 2025; not hiring-specific). The hiring audits found here either vary race and gender, use two nationality levels (ABLEIST: US/India; Rao: UK/India), or pool a region (Lippens). A safer version: "LLM hiring audits mostly vary gender and race; when national origin appears, it is typically a pooled regional or ethnic category or a handful of countries."
- **C2 is supported with one qualification.** Saeed 2024 and 2026, Naous, ArGAN, Abid, Elsafoury and Shahid are stereotype, safety or discourse studies. MENAValues and Almheiri are alignment or knowledge studies. But MENAValues and Elsafoury do resolve individual Arab countries. The accurate contrast is therefore "not in allocative decisions about individuals", rather than "never at country level".

## 5. Where the claim is weak

1. **"Within-Arab heterogeneity" as such is not new.** Keleg argued it conceptually, and MENAValues showed it empirically for values. Framing the contribution as "LLMs treat Arab countries differently" would be pre-empted. The new element is the decision context: counterfactual hiring decisions with qualifications held fixed.
2. **"Heterogeneity" is trivially true unless it is defined against noise.** With 22 levels, sampling at temperature 0.7, and 5 repetitions, some country means will differ by chance. A Q&A reviewer will ask what counts as *systematic*.
3. **The pooled anti-Arab penalty is already known** (Lippens; Saeed). A pooled Arab-vs-German effect is a replication, not the contribution.

## 6. Smallest change that recovers a genuine contribution (no new factors)

**(a) Tighten the wording of the contribution.** Suggested content, for the team to phrase themselves: "the first counterfactual LLM hiring audit we know of that disaggregates the national-origin category prior hiring audits pool as 'Arab' into all 22 Arab League signals, using an explicit *Staatsangehörigkeit*-style field in a German setting." Cite Keleg and MENAValues as prior work on Arab heterogeneity outside decisions, and Lippens as the pooled-category hiring precedent.

**(b) Make "systematic heterogeneity" a pre-registered, falsifiable estimand.** Suggestion for the statistician:
- The between-country dispersion among the 22 Arab signals, e.g. the SD of a nationality random effect within the Arab group.
- A pre-specified noise floor, e.g. a label-permutation null or the dispersion across identical repeated reference clones.
- One test of whether the pooled Arab estimate misrepresents the countries, e.g. whether country effects differ in sign or exceed the pooled effect by a pre-set margin.
- Keep the pre-registered sub-regional grouping as the only structure used to model it.

This is what separates the study from both Lippens (pooled) and MENAValues (not decisions). It uses the existing design unchanged.

**(c) Optional sharpening with no new condition.** Report whether the neutrality instruction only shifts the mean nationality effect or also compresses the between-country dispersion. Tamkin et al. and Huijzer & Chen report mean or max-min gaps, not within-group dispersion, and we found no study measuring dispersion under mitigation. This also works as a fallback if Bilon or Busetta turn out to disaggregate Arab countries.

## 7. Is the principle-behaviour gap novel?

**No, not as a concept.** It is a crowded, named area:

- stated vs revealed preference deviation (Gu et al. 2025, KL-divergence measure);
- value-action gap (Shen et al., EMNLP 2025);
- explicitly unbiased but implicitly biased (Bai et al., PNAS 2025);
- overt vs covert prejudice (Hofmann et al., Nature 2024);
- veneer of fairness and task-dependent stereotyping (Gupta et al., ICLR 2024; Kumar et al. 2026);
- unverbalized biases (Arcuschin et al., ICML 2026);
- "Said-washing" for Middle East discourse (Shahid 2026).

It has also already been shown informally *for nationality*. Mazeika et al. 2025 note that a model may deny preferring one country's population while its choices imply unequal exchange rates across countries. Mao & Zhao 2025 find that models state origin matters little yet reason by origin.

What remains defensible is a narrow **application**: pairing each model's stated endorsement of the non-discrimination principle (`principle_probe`, per occupation) with its measured nationality effects in the same occupation. Present it as an instance of stated-vs-revealed deviation (cite Gu and Shen) specific to non-discrimination in hiring. It must not be presented as a new measure or construct. Calling it a new "principle-behaviour inconsistency index" would be a relabel and is likely to be challenged in Q&A.

## 8. Checks still open before the 13.10 pitch

1. Read the full text of Bilon 2025 (*J. Decision Systems*) and Busetta et al. 2025 (Springer) for their national-origin levels.
2. Re-run the 9 failed Semantic Scholar queries (listed in `L2_notes.md`) and the same phrasings in Google Scholar.
3. Run a short Arabic-language search, e.g. تحيز النماذج اللغوية التوظيف الجنسية.
4. Cross-check part 1's hiring-audit list for any study that uses an explicit nationality field across many countries.
5. Do not cite Törnberg 2026 (arXiv:2603.13891): the author withdrew it over a stimulus-assignment confound.
