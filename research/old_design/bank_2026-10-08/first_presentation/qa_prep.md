# Q&A preparation for the pitch (bank design)

Written on 2026-10-08 by Claude Code. Facts and where they come from, not answers to
read out. Keys in backticks are in `research/literature_matrix.csv`; "press" is a press
report, "vendor" a company's own statement. The Q&A notes for the hiring design are in
`research/old_design/hiring_2026-10-04/first_presentation/`.

## 1. Why a bank? Last week this was about hiring.

- In a CV the nationality line can be removed before a model sees it, and a careful
  system would remove it. `research/scenario_reviews/nationality_line_pipeline_review.md`.
- In a bank it cannot: German law obliges the bank to record nationality for every
  customer (`gwg2017`, section 11 (4) no. 1).
- The comparison of scenarios (hiring, loan, visa, asylum, bank check) is in
  `research/scenario_reviews/`.

## 2. Do banks really use LLMs for this?

- What is documented: vendors sell AI agents for customer checks, screening alerts and
  high-risk reviews. One says 10 of the top 20 banks use its agents and names Deutsche
  Bank (`workfusion2026agents`, vendor). Another describes "a disposition recommendation
  with rationale for human review" (`sardine2026agentic`, vendor).
- EU law expects it: Regulation 2024/1624, Article 76(5), allows decisions "from
  processes involving AI systems" with "meaningful human intervention"; it applies from
  10 July 2027 (`eu2024amlr`).
- What is not known: which models the products use, their prompts, and whether the model
  sees the nationality.
- The ECB reports that for credit scoring and fraud detection banks mainly use decision
  trees (`ecb2025ai`). Most customer risk ratings come from fixed scorecards.
- So: we test open models in the task the products are sold for. We do not test a
  product.

## 3. Isn't a higher rating for a Syrian or Yemeni passport simply correct?

- Four Arab League countries are on the EU list of high-risk third countries: Algeria,
  Lebanon, Syria, Yemen (`ec2026highrisk`, read 8 October 2026).
- German law ties the list to relationships and transactions involving such a country
  or a person resident there (`gwg2017`, section 15 (3)).
- The European guidelines name residence, place of business and relevant links as
  country factors. The word "nationality" does not occur in the 225 pages of the final
  report, and an isolated factor does not necessarily move a customer into a higher
  category (`eba2021riskfactors`, guidelines 2.9 and 3.3).
- No disadvantage on account of nationality when opening a payment account (`zkg2016`,
  section 3). No blanket refusal of categories of customers (`eba2023derisking`,
  paragraphs 9 and 10).
- Our customers live and work in Germany and expect no payments abroad.
- Honest limit: practice may differ from the rules, and none of us is a lawyer. Vendor
  documentation is said to show rating systems that score nationality as an input; this
  comes from a search summary and was not read, so do not state it as fact. The design
  measures against the list instead of calling every difference bias.

## 4. What do you expect to find?

- No hypotheses are written yet. They come before the first real run.
- Both directions are possible. Race on a mortgage file lowered approval by 8.5
  percentage points in GPT-4 Turbo (`bowen2025measuring`). Real origin labels led to
  fewer discriminatory recommendations than invented groups in a French study
  (`bunel2026customer`).
- Three patterns can be told apart: the model follows the list, lumps the 22 together,
  or draws its own lines. No difference at all is a result too.

## 5. Is this new?

- We found no study in which an LLM rates bank customers while their nationality is
  varied. This rests on a few web searches of 8 October 2026.
- Say that a systematic search is still to be done. `research/novelty_assessment.md` was
  written for hiring.

## 6. Why these models?

- Qwen3 8B, Llama 3.1 8B, Gemma 3 12B, Mistral Small 3.2 24B: open weights, run on the
  university cluster, no API budget.
- The products run on large commercial models. This is a limitation.
- Risk known from the literature: Llama 3 8B approved every mortgage application in one
  study (`bowen2025measuring`), so a yes/no answer may not move. Our answer includes a
  0-100 score, and a pilot comes first.

## 7. Why 22 nationalities and what are the placebo countries for?

- All Arab League members: a political-institutional definition, not an ethnic one.
- Any set of country labels spreads a model's ratings a little. Uruguay, Malawi, the
  Maldives and Cambodia show how much. None of them is on the EU list.
- German is the citizen benchmark; Turkish is the usual comparison group in German
  studies.

## 8. Why no names?

- A name cannot tell Arab countries apart: raters assigned 34% of Moroccan names to
  Morocco (`martiniello2022signaling`).
- A name adds gender and religion.

## 9. Is the setup realistic?

- Realistic: the task, the mandatory nationality field, a written policy given to the
  model, a rating with reasons for a human analyst.
- Not realistic: a short English file for a German bank, no name and no place of birth,
  a policy we wrote, small open models.

## 10. Ethics

- Everything is synthetic. A difference between two labels says something about the
  model, never about people from a country. `ETHICS.md`.
- Being on the list is a statement about a state's financial system, not about its
  citizens.

## Open (decide, or say that it is open)

- Hypotheses and the statistical analysis.
- Whether the list of countries stays in the policy the model reads.
- Decoding settings and the number of repetitions.
- Whether to move to German prompts later.
- The working title.
