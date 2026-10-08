# A scenario where nationality cannot be dropped: bank customer checks (internal review)

Written on 2026-10-08 by Claude at Laith's request: find a way to compare the Arab
nationalities in a realistic scenario in which (1) the nationality is not just another
field that could be removed, (2) an AI pipeline for the task is in use or planned, and
(3) the experiment can stay close to the setup that companies or authorities really use.
Internal research note, **not report text**. It continues
`scenario_alternatives_review.md`.

Limits: one round of web search. Company figures are the companies' own statements. Two
legal texts were read directly (see section 8); the rest comes from summaries. Nothing
here is in `research/literature_matrix.csv` yet, and no novelty claim is made.

## 1. Short answer

The scenario that meets all three conditions best is the **money-laundering check a bank
runs when it takes on a customer** (customer due diligence, "know your customer").

1. **The nationality cannot be removed.** German law obliges the bank to record it, and
   the task itself is to rate the customer's risk, including geographic risk. Commercial
   rating systems score nationality as an input of its own.
2. **AI pipelines for exactly this task are in use.** This is the best-documented field
   for LLM-based "agents" in finance: products that review onboarding files, screening
   hits and high-risk cases and write the rating and its reasons. EU law already
   regulates such automated decisions.
3. **The setup can be copied closely.** The agents get a customer file and the bank's
   written policy, and return a risk rating, a recommendation and reasons. All three can
   be built from public rules.

It has one advantage no other candidate has: **an official ranking of the countries
exists.** The EU's list of high-risk countries contains four Arab League members
(Algeria, Lebanon, Syria, Yemen) and not the other eighteen. So "which Arab?" can be
measured against the rulebook: does the model separate the countries the way the law
does, does it lump all of them together, or does it draw its own lines?

The honest limits: the evidence on what the agents do is vendor material; the published
rules speak of where a customer lives and has ties, not of nationality as such; and no
study of this kind with LLMs was found in a quick search, which is not a novelty claim.

## 2. The candidates against the three conditions

| scenario | nationality needed for the task | LLM pipeline in use or planned | can be copied closely | verdict |
|---|---|---|---|---|
| **Bank customer check** | Yes: recorded by law, part of the risk rating | In use: agent products for onboarding, screening and high-risk review | Yes: file + policy in, rating + reasons out | **Best fit** |
| Asylum | Yes | In use in the UK: an LLM summarises interviews and searches country notes | Partly: the output is a summary, hard to score; sensitive topic | Real, but hard to measure |
| Visa | Yes | Rule-based risk scores in use; no LLM that recommends decisions found; Canada forbids generative AI in decision support | The documented tools are not LLMs | Fails condition 2 for LLMs |
| Loan | No | LLMs read documents around the decision | Yes | Fails condition 1 |
| Hiring | No | Yes, in direct use | Yes | Fails condition 1 |

## 3. The real setup

### 3.1 What the law requires

- **Recording.** For every customer a German bank must record first and last name, place
  and date of birth, **nationality** and address (§ 11 (4) no. 1 of the
  anti-money-laundering act, from a summary of the statute).
- **Rating.** The bank must assess the risk of each business relationship. The European
  guidelines name the country factors to consider: "the jurisdictions in which the
  customer and beneficial owner are based", their "main places of business", and "the
  jurisdictions to which the customer and beneficial owner have relevant personal links"
  (EBA guidelines on risk factors, paragraph 22, read in the 2017 version).
- **High-risk countries.** The EU keeps a list of high-risk third countries. Relationships
  and transactions involving them need enhanced checks. Since 29 January 2026 it has 26
  entries (read on the Commission's page).

### 3.2 What the rules say about nationality itself

- In the 108 pages of the 2017 guidelines the word "nationality" does **not occur**. The
  factors are residence, place of business and personal links. The 2021 revision was not
  checked.
- The same guidelines: "the presence of isolated risk factors does not necessarily move a
  relationship into a higher or lower risk category".
- The EBA's guidelines against "de-risking" (2023) call the refusal of whole categories of
  customers without looking at the individual a sign of poor risk management (from the
  EBA's own summary).
- A bank may not disadvantage a consumer who is legally resident in the EU on grounds of
  nationality when it comes to a payment account (EU payment accounts directive,
  Article 15; in Germany § 3 of the payment accounts act). Asylum seekers have a right to
  a basic account.

So the rulebook position for a customer who lives and earns in Germany and has no ties
abroad is: the passport alone is not a reason for a higher rating.

### 3.3 What practice does

- Vendor documentation shows rating systems that score nationality, residence and country
  of birth as separate inputs and, for people with two nationalities, take the riskier
  one (ComplyAdvantage, Pega; from a search summary).
- Documented consequences: UK banks closed accounts of Syrian residents in 2014 with
  reference to "connections to sanctioned countries"; in July 2024 the Netherlands
  Institute for Human Rights found that ING discriminated against customers whose
  payments were blocked or checked because of names that did not sound Dutch; in a field
  experiment across seven European countries banks answered loan enquiries from
  Arabic-sounding names far less often (35.1% against 59.8%).

This gap between rule and practice is what the experiment would measure in a model.

### 3.4 The AI pipelines

| product | what it does | evidence |
|---|---|---|
| WorkFusion | Named agents: "Kayla" for customer checks, "Edward" for enhanced checks and high-risk reviews, "Evelyn" for name-screening hits, "Tara" for payment screening. "Enhanced with GenAI". Says it is used by "10 of the top 20 banks"; names Deutsche Bank and Scotiabank | company website (read) |
| Sardine | Agents for onboarding reviews, sanctions and adverse-media hits, enhanced checks, report drafting. Gives "a disposition recommendation with rationale for human review"; drafts follow the customer's own procedures | company website (read) |
| Greenlite AI | Agents that work inside a bank's existing systems, collect context, assess risk and recommend a report or closure. Customers named: Ramp, Mercury, Betterment, Gusto and US banks | press release (summary) |
| Airwallex | Uses large language models for customer checks at onboarding; reports half as many false alerts | trade press (summary) |
| Hawk (Munich) | AI for transaction monitoring and screening; Commerzbank reported as a customer | trade press (headline only) |

What these agents read, as far as the vendors say: the customer profile, the documents,
the results of sanctions, politically-exposed-person and adverse-media screening,
transaction data, and the institution's own written procedures. What they return: a risk
rating or score, a recommendation to clear or escalate, and a written rationale. No
vendor publishes its prompts or says which profile fields the model sees.

Around them, most customer risk ratings are still calculated by fixed scorecards. The
agents review cases and write the reasoning. The experiment would imitate that step.

### 3.5 The rule on automated decisions

The EU anti-money-laundering regulation 2024/1624, Article 76(5) (read): banks "may
adopt decisions resulting from automated processes, including profiling ... or from
processes involving AI systems", provided that any decision to enter or refuse a business
relationship, or to raise or lower the level of checks, "is subject to meaningful human
intervention", and that the customer "may obtain an explanation of the decision" and
challenge it. The regulation applies from 10 July 2027 (date from a secondary source).
The law therefore expects exactly this use.

## 4. The benchmark among the 22 countries

| status | Arab League members |
|---|---|
| On the EU high-risk list (January 2026) | Algeria, Lebanon, Syria, Yemen |
| Not on it | the other eighteen, including Egypt, Iraq, Jordan, Morocco, Saudi Arabia, Tunisia, UAE |

Further public yardsticks that could go into `country_covariates.csv`: the FATF lists
(June 2026 reported: Lebanon, Syria, Yemen, Kuwait and Iraq under increased monitoring,
Algeria removed) and the Basel AML Index, which scores 177 countries (2025 reported:
Djibouti 6.93, Algeria 6.82, Morocco 5.04, Oman 4.25; other values not retrieved).

The lists disagree with each other and change several times a year. One list and one
date have to be fixed in advance.

## 5. An experiment close to the real setup

Options, not decisions. The team decides, and hypotheses are needed before the first real
run.

**What the model gets**

1. *The bank's policy*, as the agents get the institution's procedures: the risk factors
   (customer, geography, product, channel) in the wording of the guidelines, the list of
   high-risk countries, the rating scale, and when enhanced checks are required.
2. *One customer file* for a private current account, with the fields a German bank
   collects: customer reference, date of birth, **nationality**, identity document
   (passport of that country), residence in Germany with an unlimited settlement permit,
   occupation and German employer, net income, source of funds (salary), expected use of
   the account, no payments abroad expected, screening results (no sanctions hit, not
   politically exposed, no adverse media).

**What it returns:** risk rating (low, medium, high), whether enhanced checks are
required, a recommendation (open the account, open with enhanced checks, refuse), and a
short reason. This is the output the products describe.

**What varies:** only the nationality and the matching passport: the 22 Arab League
countries, German, Turkish and the placebo countries. A "not stated" version does not
exist here, because the field is mandatory.

**The second condition (our experiment 3):** the same policy with one added paragraph in
the sense of the de-risking guidelines: nationality alone is not a risk factor; assess
the individual. This is a real rule, not an invented instruction.

**What can be reused:** the nationality table, the country covariates, the model list.
The 20 occupations of `jobs.csv` can serve as the customers' occupations.

**What the comparisons would be**

- Arab nationalities not on the list against placebo nationalities not on the list:
  is "Arab" as such rated higher?
- The four listed countries against the eighteen others: does the model draw the line
  where the rulebook draws it, although by that rulebook the passport of a German
  resident should not matter at all?
- Spread among the eighteen unlisted Arab nationalities against spread among placebo
  countries: differences that no list explains.
- The same with the added paragraph: does a real rule remove them?

**Size:** 20 customer files x 28 nationalities x 2 policies is 1,120 runs per model and
wording. Even with three wordings and ten repetitions that is 33,600 short runs per
model.

**Closer still to practice, for the parked list:** a name-screening task (is this
customer the listed person?), payments to the home country as a second factor, and files
in German.

## 6. What could be said with it, and how new (tentative)

- The claim would be about model behaviour in a task where the law puts the nationality
  in front of the system, and where the law also says how far it may count.
- Not found in a quick search: any LLM study of customer checks or sanctions screening
  with nationality or Arab applicants. Nearest: a 2026 article reporting that AI models
  judged identical transactions as more likely fraudulent when the company was labelled
  Chinese rather than American or British, with neutrality instructions shrinking but not
  removing the gap (Journal of Business Ethics, from a search summary); and a mortgage
  benchmark in which models treat non-English names as foreign.
- A systematic search (arXiv, SSRN, compliance and finance outlets) is needed before any
  sentence about novelty.

## 7. Limits and open points

- **Vendor evidence.** How widely the agents are used, and what they see, is known only
  from the vendors. The claim "in use" is safe; "this is what they do with nationality"
  is not known.
- **Differences are partly defensible.** A practitioner may argue that a higher rating
  for a Syrian or Yemeni passport is prudent. The design answers this by measuring against
  the list and by using customers with no ties abroad, but the argument will come.
- **Models.** The products run on large commercial models. We would test 8B to 24B open
  models.
- **The 2021 version of the EBA guidelines and the German annex on geographic risk** were
  not read. They have to be checked before the policy text is written.
- **Language.** A German bank's file and policy are in German; German prompts are parked.
- **It is another new project** compared with the proposal of 2026-10-04, five days
  before the pitch.

## 8. Sources and how far each was checked

Levels: **read** = text read directly or through a fetch of the page; **summary** =
search summary or snippet only.

| source | level | link |
|---|---|---|
| EU regulation 2024/1624, Article 76(5) | read (legal database page) | https://www.springlex.eu/en/packages/aml/amlr-regulation/article-76/ |
| EBA/ESA joint guidelines on risk factors, JC 2017 37 (superseded by EBA/GL/2021/02, not read) | read (PDF text; word search) | https://www.eba.europa.eu/sites/default/files/documents/10180/1890686/66ec16d9-0c02-428b-a294-ad1e3d659e70/Final%20Guidelines%20on%20Risk%20Factors%20(JC%202017%2037).pdf |
| EU list of high-risk third countries, Commission page | read | https://finance.ec.europa.eu/financial-crime/anti-money-laundering-and-countering-financing-terrorism-international-level_en |
| German anti-money-laundering act § 11; annex 2 | summary | https://www.gesetze-im-internet.de/gwg_2017/__11.html |
| EBA guidelines on de-risking EBA/GL/2023/04 | summary | https://www.eba.europa.eu/eba-issues-guidelines-challenge-unwarranted-de-risking-and-safeguard-access-financial-services |
| EU payment accounts directive 2014/92, Articles 15 and 16; German payment accounts act § 3 | summary | https://www.gesetze-im-internet.de/zkg/__3.html |
| WorkFusion website | read | https://www.workfusion.com/ |
| Sardine, agentic AI for AML | read | https://www.sardine.ai/agentic-ai-for-aml |
| Greenlite AI funding announcement | summary | https://www.businesswire.com/news/home/20250521200064/en/Greenlite-AI-Raises-$15M-Series-A-to-Help-Banks-and-Fintechs-Fight-Financial-Crime-with-Trusted-AI-Workforce |
| Airwallex LLM customer checks | summary | https://fintechnews.sg/81791/ai/airwallex-taps-generative-ai-to-speed-up-kyc-reduces-false-positives-by-50/ |
| Hawk and Commerzbank; N26 | summary | https://hawk.ai/our-products/transaction-monitoring |
| Vendor documentation on nationality as a rating input (ComplyAdvantage, Pega) | summary | https://complyadvantage-knowledge-base.help.usepylon.com/articles/2926532454-how-are-risk-scores-calculated |
| FATF lists June 2026; Basel AML Index 2025 | summary | https://www.fatf-gafi.org/en/publications/Fatfgeneral/outcomes-fatf-plenary-june-2026.html , https://baselgovernance.org/publications/basel-aml-index-2025 |
| ING ruling of the Netherlands Institute for Human Rights, July 2024 | summary | https://nltimes.nl/node/74214 |
| HSBC account closures of Syrians, 2014 | summary | https://www.middleeasteye.net/news/hsbc-shuts-accounts-syrians-uk-after-lobbying-assads-cousin |
| Stefan et al. 2018, banks and Arabic-sounding names, PLoS ONE | read | https://pmc.ncbi.nlm.nih.gov/articles/PMC5788365/ |
| Country-label sensitivity in AI financial analysis, Journal of Business Ethics 2026 | summary | https://link.springer.com/article/10.1007/s10551-026-06385-7 |
| UK asylum LLM tools: Home Office evaluation (read earlier); Open Rights Group on rollout and model | read / summary | https://www.gov.uk/government/publications/evaluation-of-ai-trials-in-the-asylum-decision-making-process |
| Canada: no generative AI in support of decisions on applications (question period note 2025) | summary | https://search.open.canada.ca/qpnotes/record/cic,IRCC-2025-QP-00001 |
