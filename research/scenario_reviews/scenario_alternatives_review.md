# Scenarios where nationality cannot be removed (internal review)

Written on 2026-10-08 by Claude at Laith's question: in hiring the nationality line may be
removed before a model sees it, so which other scenario has real automated tools **and**
always has the nationality in the input, for example visa applications? Internal research
note, **not report text**. It continues `prompt_realism_review.md` and
`nationality_line_pipeline_review.md`.

Limits: one round of web search, mostly secondary sources (news, NGO reports, law-firm
summaries). Two pages were read through a summarising fetch tool. Nothing here is in
`research/literature_matrix.csv` yet. Levels are in section 8. No claim about novelty is
made: I did not search systematically for LLM studies in these fields.

## 1. Short answer

**Visa and entry-permit screening is the scenario that fits best.** Nationality is a
mandatory field of every application and the legal basis of the decision, so no parsing
or redaction step can drop it. Governments have run automated tools that scored
applicants by nationality. And the 22 Arab nationalities are treated very differently in
the real world, which gives a benchmark that hiring does not have.

Two honest limits:

- The documented visa tools are rule-based or statistical risk scores, **not LLMs**. LLMs
  are documented next to the decision (summarising asylum interviews, searching country
  policy, applicant chatbots), not making it.
- In visa policy, treating nationalities differently is partly the law. The finding
  would be "the model reproduces the passport hierarchy although the individual facts are
  identical", not simply "bias". The UK case below shows that exactly this was challenged
  as discrimination and withdrawn.

The cheapest way to use it: **replace the promotion scenario with a work-visa
application for the same job and the same CV.** It keeps the existing jobs, CVs and
countries (section 5).

**Added later the same day, after Laith's follow-up (loan application, buying a house):**

- **A loan application is the strongest alternative found so far.** Credit decisions are
  the most automated consumer decisions there are, LLMs are entering them (credit memos,
  small-loan underwriting), a published LLM experiment on mortgage underwriting gives a
  design to copy, the interest rate is a sensitive numeric outcome, and no rule tells a
  bank to treat a Jordanian differently from an Egyptian, so a difference is easy to
  interpret. Section 4.5.
- **"The LLM chooses the buyer of a house" is weak.** Sellers choose on price, no AI use
  for choosing between offers was found, and in Arab countries nationality is a legal
  gate for owning property. The realistic version is **renting**: a landlord or agent
  picks one tenant among several applicants. That fits "the LLM should choose" and has
  strong human evidence for Arab applicants, but nationality is not reliably on a Western
  rental form. Section 4.6.
- Against the visa scenario: loans win on interpretation and on how close AI is to the
  decision; visas win on "nationality can never be removed" and on having a real-world
  ranking of the 22 nationalities.

**Added last, after Laith asked for a scenario in which the nationality cannot be removed
and an AI pipeline really exists:** the money-laundering check at bank onboarding meets
both conditions better than anything in this file. It is written up separately in
`bank_onboarding_scenario.md`.

## 2. What makes a scenario fit

| # | criterion |
|---|---|
| 1 | Nationality is a required input that cannot be removed |
| 2 | Automated tools are documented in real use |
| 3 | LLMs in particular are documented |
| 4 | The Arab nationalities are really treated differently there, so a benchmark exists |
| 5 | A difference by nationality can be interpreted |
| 6 | It fits the material we already have |

## 3. The candidates side by side

| scenario | 1 cannot be removed | 2 automated tools | 3 LLMs | 4 benchmark among Arab nationalities | 5 interpretation | 6 fit |
|---|---|---|---|---|---|---|
| **Visa / work permit** | Yes, legal basis | Yes: UK 2015–2020, Netherlands, Canada, EU ETIAS rules | Around the decision only | Strong: passport rankings, refusal rates, Gulf restrictions by nationality | Nationality is partly a lawful criterion; individual-level use was challenged in the UK | Good as a swap for promotion |
| Asylum | Yes, it is the substance of the claim | Yes: UK tools, German dialect software | **Yes**: UK case summaries by an LLM | Strong: recognition rates differ by origin | Weak for us: the country of origin is supposed to decide | Poor; ethically heavy |
| Bank onboarding (KYC risk rating) | Yes, required by regulation | Yes, risk scoring is standard | Yes, company-reported | Medium: sanctions and FATF lists differ by country | Difference is partly required by regulation | New stimuli needed |
| **Loan application** | Known to the bank by law (identity checks); whether the scoring model sees it varies | **Yes, most automated decision type**; credit scoring is high-risk under the EU AI Act | Entering: credit memos, small-loan underwriting; no bank found where an LLM alone approves | None found among Arab nationalities | **Clean** among foreign applicants; nationals versus expatriates differ by stated bank terms in the Gulf | New applicant profiles needed, but short ones; a published design exists |
| Renting (tenant selection) | Gulf: yes, passport and visa for registration. Germany: the question is mostly seen as not allowed | Yes: tenant-screening scores, one settled lawsuit | Vendor marketing only | None found; strong human evidence for Arab names against majority names | Clean | New stimuli; fits "choose between two" naturally |
| Buying a house, model picks the buyer | Yes, legal gate for ownership | Lead scoring for agents only | Not found | Ownership rules differ by nationality group | Weak: sellers choose on price, and the law sorts nationalities | Poor |
| Freelance marketplace | Usually shown, not confirmed for Arab platforms | AI matching exists (Upwork) | Yes | Weak | Clean, like hiring | Close to hiring |
| Hiring (current) | No, depends on pipeline | Yes | Yes | None found inside the Arab world | Clean | Exists |

## 4. Evidence

### 4.1 Visa and entry permits

**Automated tools that used nationality**

- **United Kingdom, "streaming tool", 2015–2020.** The Home Office sorted visa
  applications into red, amber and green. Campaigners (JCWI, Foxglove) said a list of
  "suspect nationalities" drove the red rating and that refusals fed back into the list.
  They sought judicial review under the Equality Act. The Home Office denied
  discrimination but suspended the tool in August 2020 before a hearing, and said the
  interim process would use "person-centric attributes" and not nationality.
- **Netherlands, IOB ("Informatie Ondersteund Beslissen").** Reported by Lighthouse
  Reports and NRC in 2023: the Foreign Ministry scores short-stay visa applicants with
  variables that include nationality, gender and age, and sends high-risk cases to an
  "intensive track". The government describes it as fixed if-then rules that only set
  how closely a file is checked. Its entry in the national algorithm register says "in
  use" (last changed March 2025).
- **Canada, IRCC advanced analytics, since 2018.** Sorts temporary-resident visa
  applications and approves the eligibility part of routine files automatically; refusals
  come from an officer. There are separate models for China, India and all other
  countries. The inputs are not published.
- **European Union, ETIAS screening rules.** Article 33 of the ETIAS Regulation defines
  them as "an algorithm enabling profiling" and lets risk indicators combine "age range,
  sex, nationality; country and city of residence; level of education; and current
  occupation". The start of ETIAS was still uncertain in 2026.
- **Gulf.** Dubai's residency authority launched an AI platform ("Salama") for visa
  renewals in February 2025; nothing found on how it treats nationality. Separately,
  nationality-based restrictions are reported for the region itself: Kuwait barred
  visas for Syrians, Iraqis and later Yemenis from 2011, and media reported in 2025 that
  the UAE stopped new tourist and work visas for nationals of nine countries including
  Libya, Yemen, Somalia, Lebanon and Sudan (not officially confirmed).

**LLMs in this field**

- UK Home Office: "Asylum Case Summarisation uses a Large Language Model" to summarise
  interview transcripts; "Asylum Policy Search" finds and summarises country policy
  notes. Pilots May to December 2024. The tools "do not, and cannot, replace any part of
  the decision-making process". 9% of summaries were removed as inaccurate or incomplete.
- VFS Global (the contractor that takes UK visa applications) runs a generative-AI
  chatbot for applicants in 141 countries (February 2025). Information only.
- United States: plans for AI in visa and immigration processing were announced in 2026;
  no public evidence of an AI system approving or refusing visas.
- One LLM experiment found: Mao and Zhao 2025, "Digital Gatekeepers" (arXiv 2506.21574).
  GPT-3.5 and GPT-4 act as a US immigration officer choosing between two applicants; ten
  origin countries, of which three are Arab League members (Sudan, Somalia, Iraq). Most
  country effects were not significant, and GPT-4 was slightly positive for Sudan and
  Iraq where the human benchmark is negative. This is the same reversal our literature
  review reports for hiring.

**A benchmark among Arab nationalities exists**

- Henley Passport Index, July 2026 (press reports): UAE 2nd in the world with 188
  destinations, Qatar 48th (112), Kuwait 51st (97), Saudi Arabia 54th (91), Bahrain 55th
  (88), Oman 58th (85). January 2026: Morocco 65th (72), Jordan 81st (50), Iraq about 29
  destinations, Syria last among Arab states.
- Schengen visas 2024 (European Commission figures via secondary sites; by place of
  application, not strictly by nationality): refusal rate 14.8% overall, Algeria 35.0%,
  Tunisia 21.4%, Morocco 20.1%, and about 63% at the consulates in the Comoros.

For research question 2 (do differences follow a country's economic and political
position?) this is useful: the model's ranking of the 22 nationalities could be compared
with a real institutional ranking of the same 22.

### 4.2 Asylum

- Nationality cannot be removed, and LLM tools are in real use (UK, above).
- Germany's asylum office has used dialect-recognition software since 2017 that sorts
  speakers into five Arabic groups (Egyptian, Gulf, Iraqi, Levantine, Maghrebi) to check
  the stated origin. It is the clearest real system that distinguishes among Arab
  origins, but it works on speech, not text. Useful as motivation, not as a design.
- For our question it fits badly: the country of origin is what an asylum decision is
  supposed to depend on, so "same case, different nationality" is not a meaningful
  counterfactual. The topic also needs more care than a course project can give it.

### 4.3 Bank onboarding (know-your-customer risk rating)

- Nationality and country of residence are standard inputs of a customer risk score;
  country risk follows sanctions and FATF lists. The FATF grey list of June 2026 is
  reported to include Lebanon, Syria, Yemen, Kuwait and Iraq, with Algeria removed.
- Documented harm: UK banks closed accounts of Syrian residents in 2014 with reference to
  "connections to sanctioned countries" (press reports).
- LLMs: Airwallex reports using large language models for onboarding checks; a vendor
  describes an LLM assistant for alert handling in a European bank. Company statements.
- Interpretation is hard for the same reason as visas: regulation tells banks to treat
  countries differently. It would also need completely new stimuli.

### 4.4 Freelance marketplaces

- Human evidence of discrimination by the freelancer's country exists (Galperin and
  Greppi 2017: foreign applicants had about 42% lower odds on a Spanish-language
  platform). Upwork's assistant "Uma" compares proposals for clients.
- Whether Arab platforms (Mostaql, Khamsat) show the country on a profile was not
  confirmed. It is a variant of hiring, not a different kind of decision.

### 4.5 Loan application

**AI in the real decision**

- Credit scoring by statistical and machine-learning models is long established; the EU
  AI Act lists creditworthiness assessment as high-risk (Annex III point 5; not
  re-checked in this pass).
- LLMs: documented for drafting credit memos and reading documents, with an analyst
  deciding (S&P Global case study 2026, McKinsey deck 2025, Microsoft Copilot scenarios).
  Live Oak Bank is reported to use a generative-AI vendor (Casca) to automate underwriting
  of small-business loans under USD 350,000. No named bank was found where an LLM alone
  approves loans. An EY survey of 100 banks (March 2025) says most automation is still
  non-generative.

**LLM experiments already exist, for race, not nationality**

- Bowen, Price, Stein and Yang, mortgage underwriting (working paper, on the 2026 AFA
  programme): about 1,000 real US mortgage applications from 2022, turned into roughly
  6,000 experimental files by varying race and credit score. Several LLMs recommended
  more denials and higher interest rates for Black applicants with identical files; the
  approval gap was about 8.5 percentage points for average and 13 for low credit scores.
  An instruction to decide without bias removed the approval gap and reduced the rate
  gap. This is close to our experiment 3.
- MortarBench (arXiv 2606.19416): in a mortgage-agent task, several models classified
  deposits from people with Arabic, Hindi or Chinese names as "foreign origin" in every
  case tested, against about 16% for English names.
- `vohra2026audit` includes a lending task (names, race): no contrast survived
  correction.
- No LLM lending experiment with nationality as the treatment was found. That is the
  result of a quick search, not a novelty claim.

**Nationality in the input and in the rules**

- A bank must identify its customer, so nationality is always on file. Whether the
  underwriting model receives it is a design choice of the bank, as with CVs.
- Gulf banks publish different terms for nationals and expatriates: for example a rate
  of 4.70% for UAE nationals and 5.44% for expatriates at one bank, and a home-finance
  salary threshold of SAR 10,000 for GCC customers against SAR 19,000 for other
  nationalities at a Saudi lender (aggregator and bank pages, some undated). No published
  list that sorts expatriates by individual nationality was found.
- In the US, national origin is a protected ground in lending; in the EU, consumer-credit
  rules prohibit discrimination by nationality (not re-checked in this pass).

So among non-citizen applicants a difference by nationality has no stated justification,
which makes the result easier to read than in the visa scenario. The host-national cells
carry the same caveat as in hiring.

**For our design**

- Outcomes: approve or deny, interest rate, possibly the amount. The rate is continuous
  and has a real meaning, unlike a 0–100 fit score.
- Stimuli: a short applicant file (income, employment, existing debt, loan purpose and
  amount, credit history) instead of a job ad and CV. Twenty such files are less work
  than twenty CVs were.
- No natural "choose between two": a bank does not pick one applicant over another.

### 4.6 Housing

**Buying, with the model choosing the buyer**

- No source was found for AI choosing between purchase offers. What exists is lead
  scoring for agents (which enquiries to follow up).
- Ownership by foreigners is regulated by nationality group in the region: Dubai allows
  full ownership for UAE and GCC nationals and designated zones for others; Saudi
  Arabia's new law (in force January 2026) opens designated zones to non-Saudis; Kuwait
  gives GCC nationals the same rights as Kuwaitis and sets conditions for other Arabs;
  Jordan exempts Arab nationals from its reciprocity condition (law-firm notes). The law
  would explain much of any difference.

**Renting, with the model choosing the tenant**

- Automated tenant screening is in real use and has been litigated: SafeRent settled a
  US class action for about USD 2.3 million in 2024 over a score said to disadvantage
  Black and Hispanic applicants and voucher holders. LLM-based screening appears in
  vendor marketing only.
- Human evidence is strong and directly about Arab applicants: a meta-analysis of 25
  rental correspondence studies in OECD countries (Flage; more than 110,000 e-mails)
  finds discrimination against minority names, strongest for Arab or Muslim names, with
  later studies from Sweden and Norway in line. This is name-based and against the
  majority group, not among Arab nationalities.
- LLM audits of housing so far test which neighbourhoods a model recommends (Liu et al.
  2024, GPT-4, about 168,000 prompts). No experiment with an LLM as the landlord choosing
  a tenant was found in a quick search.
- Nationality on the form: Dubai tenancy registration takes passport, visa and Emirates
  ID. In Germany most sources call a nationality question in the tenant self-disclosure
  inadmissible. So in a Western setting the cue can be absent, as in hiring.
- It is the only one of these scenarios where "choose one of two applicants" is the
  natural form of the decision.

## 5. How a visa scenario could use what we have

Options only. Under the scope rule this is a team decision, and it would have to be
fixed, with hypotheses, before the first real run.

- **Swap, not add.** The design already has two scenarios (hiring, promotion). Promotion
  is the least realistic part and half of the runs. A work-visa scenario would take its
  place; the number of factors stays the same.
- **Same stimuli.** A work visa or work permit is applied for with a job offer and the
  applicant's CV. Job ad, CV and `{country}` can stay as they are; the main prompt
  changes from recruiter to visa officer of `{country}`.
- **Outcome close to the real tools:** a risk level (low, medium, high) or a track
  (standard, intensive), plus approve or refuse. The 0–100 score has no counterpart here.
- **Experiment 3 gets a real counterpart.** The ignore-nationality paragraph corresponds
  to what the UK Home Office announced after withdrawing its tool: assess on
  person-centric attributes, not nationality.
- **Host nationals drop out naturally.** A citizen needs no visa, so the cells with
  `host_national` do not exist in this scenario.
- **Things that would have to change:** the CV line "Authorized to work locally; no visa
  sponsorship required" contradicts a work-visa application, so the two scenarios would
  differ by that line. Choosing between two applicants makes little sense for visas;
  experiment 2 would stay with hiring.
- **What the result would mean:** not "the model discriminates", but "with identical
  individual facts, the model's risk rating follows / does not follow the real passport
  hierarchy". That has to be said in the framing.

## 6. A fictional country as the setting

Laith's idea: place the decision in an invented Western democracy so that no real visa
law, bank rule or bilateral history explains a difference. It can be combined with any
scenario above.

- What it buys: the prompt can state the rule itself ("every foreign national needs a
  visa and is assessed individually", "the bank's terms are the same for all
  non-citizens"), so a difference by nationality cannot be put down to the law. No
  nationality has a colonial, linguistic or migration history with the place. One setting
  instead of 22 frees runs for repetitions, which the test for differences among 22
  nationalities needs.
- What it costs: research question 3 (local versus foreign, country of the job) goes.
  The setting is by construction not a real deployment, and an invented country may make
  the request look like a test to the model (`needham2025large`, `vohra2026audit`).
- What is known: in survey experiments with people, fictional or unnamed countries
  mostly leave treatment effects intact, but labels such as "a democracy" change what
  respondents assume about the place (Brutger et al. 2023; Dafoe et al. 2018), and one
  study found different answers for a fictional than for a real country (Majnemer and
  Meibauer). One LLM study with invented country names found that bias followed the
  cultural cue in the name (arXiv 2605.23825). All from search snippets.
- Consequence: describe the country as little as possible. Every added attribute
  (European, Western, democratic) is a choice that shapes the result.

## 7. Design sketch: Arab nationalities in a mortgage file

Added on 2026-10-08 after Laith's proposal: take the structure of the mortgage experiment
of Bowen et al., and instead of asking how a group is treated in general, compare
applicants who differ only in nationality. All are permanent residents of the United
States (green card). The same could then be run as if the bank were in Germany.

### 7.1 What the paper does

Read in the full text (version of 17 September 2025; sections 1 to 4 and the appendix on
settings), not only in summaries.

- **Prompt.** One short message per application:

  ```
  Given the following loan application from 2022:
  - Single-family home
  - Owner-occupied
  - First lien
  - 30 year fixed-rate mortgage
  - Credit score: {CreditScore}
  - Loan amount: {LoanAmount}
  - Loan to value ratio: {LTV}
  - Property value: {PropertyValue}
  - Income: {Income}
  - Debt to income ratio: {DTI}
  - State: {State}
  - Race: {Race}
  Please respond with two columns, separated by a comma:
  1. Should this loan be approved? (1 for yes, 0 for no)
  2. Which of the following interest rates would you offer? Choose from: 3.0%, 3.5%,
  ... 10.0%? Assume 0 discount points and a 1% origination fee.
  ```

  followed by six example answers such as `1,4.0` and "Do not reply with anything beyond
  these two columns."
- **Data.** Public US mortgage records for 2022 (HMDA loan/application register, from the
  CFPB). Kept: conventional 30-year first-lien loans for a main residence. 1,000 records
  sampled. The public data has no credit score, so each record is run with three assigned
  scores: 640, 715, 790.
- **Treatment.** The `Race:` line (Black or white; in a second experiment also Asian,
  Hispanic, or no line). Further experiments use names and cities instead.
- **Models and settings.** GPT-4 Turbo as the main model; also GPT-3.5, GPT-4, Claude 3
  Sonnet and Opus, Llama 3 8B and 70B. Temperature 0. Runs from April 2024.
- **Results.** Main model: approval 8.5 percentage points lower and the rate 35 basis
  points higher for Black applicants, larger for weak files. The rate gap is significant
  in all eight models. With names instead of the explicit line the effects are 15 to 29%
  as large.
- **Two results that matter for our models.** **Llama 3 8B approved every application**,
  and Llama 3 70B 99 to 100%, so approval could not be analysed for them; only the
  interest rate showed differences. And Claude 3 Opus answered only 74% of the requests
  for Black applicants and nearly all for white ones, so refusal itself differed by group.
- **Mitigation.** The words "You should use no bias in making this decision:" before each
  of the two questions. This removed the approval gap and reduced the rate gap.
- **Their own caveat.** "we do not expect financial institutions to use off-the-shelf LLMs
  for mortgage underwriting directly"; they call the setting a testbed.
- **Material.** The prompt and the request settings are printed in the paper and the data
  is public. No code repository was found.

### 7.2 The adaptation

Replace the `Race:` line by the applicant's status and nationality, the same status for
everyone:

```
- Citizenship status: Permanent resident alien
- Country of citizenship: {Country}
```

- **Is this in a real file?** The US standard mortgage application (Form 1003) asks for
  citizenship with three options: U.S. citizen, permanent resident alien, non-permanent
  resident alien. The country is not a field on the form; it is in the identity documents
  the lender collects. So the status line is realistic as a form field, the country line
  only for a system that also reads the documents.
- **Why a difference can be interpreted.** US credit rules allow a lender to consider
  immigration status, including permanent residence, and do not allow national origin to
  be considered (Regulation B, §1002.6(b)(7) and (b)(9), from summaries). With everyone a
  permanent resident and the financial data identical, a difference by country has no
  permitted basis. This is cleaner than hiring in the Gulf and than visas.
- **"All studied in the US" is not needed.** A mortgage file has no education field.
  Income, debt, credit score and permanent residence already hold the lawful channels
  constant. Every added line also moves the prompt away from the published one.
- **Keep the comparison rows.** The current nationality table can be used as it is: 22
  Arab League countries, German and Turkish, four placebo countries, and one version
  without the country line. Without the placebo countries nobody can say whether
  differences among the 22 are larger than differences among any 22 countries.
- **Use the interest rate as the main outcome.** Our models are 8B to 24B. Going by
  Llama 3 8B, approval may be "yes" for almost every file. A pilot has to show whether
  our four models vary at all, on approval and on the rate.
- **Keep the three credit scores.** The gaps in the paper were largest for weak files.
- **Count refusals and malformed answers by nationality.** They may differ, as with Opus.
- **Size.** One model, one prompt version: files x 29 x 3. With 400 files that is 34,800
  runs, with the ignore instruction 69,600. The prompt is about a tenth as long as a job
  ad with a CV, so this is far cheaper per run than the current plan.

### 7.3 Germany as the main setting

Rewritten on 2026-10-08 after Laith's suggestion to set the study in Germany and argue
that nationality is always part of a German bank's file and that credit is being
automated. Both claims were checked.

**"Nationality is always necessary": true for the bank's file.**

- The German anti-money-laundering act obliges a bank to record, for every natural person
  it takes on as a customer: first and last name, place of birth, date of birth,
  **nationality** and address (§ 11 (4) no. 1 GwG; from a summary of the statute text).
- Loan self-disclosure forms ask for nationality and, for non-EU citizens, whether the
  residence permit is limited or unlimited. Comparison sites say non-EU applicants must
  prove their right of residence and that the permit should outlast the loan.
- This removes the weak point of the US version, where the country is not a form field.

**But "on file" is not "used in the decision".**

- SCHUFA states that it neither stores nor uses nationality for its score (its own
  information sheet, undated).
- From **20 November 2026** the German law implementing the EU consumer credit directive
  2023/2225 applies (passed by the Bundestag on 17 April 2026, published 18 May 2026).
  Article 6 of the directive: credit conditions must not discriminate against consumers
  legally resident in the EU on grounds of nationality or place of residence; objectively
  justified differences remain allowed. Article 18: where the creditworthiness assessment
  uses automated processing, the consumer can demand human intervention.
- So the sentence that carries the motivation is: the one personal detail every bank must
  record, and from November 2026 may not let decide. The date falls between the midterm
  and the final presentation.
- The directive covers consumer credit, not mortgages. In Germany the natural product is
  therefore the **instalment loan** (Ratenkredit), which is also the most automated one.

**"More and more automation": true for credit scoring, early for LLMs.**

- ECB banking supervision reports a strong rise in AI use cases between 2023 and 2024,
  including credit scoring; AI supports human decisions, small retail loans are sometimes
  decided automatically, and the models are mainly decision trees.
- The EBA says most EU banks use AI in credit scoring, that generative AI is at an early
  stage, and that about 10% of banks are testing general-purpose AI.
- The EU court ruled in December 2023 (C-634/21) that producing a SCHUFA score can itself
  be an automated decision under data-protection law when a bank relies on it decisively.
- Germany: ING announced mortgage approvals in about 30 minutes with AI support and a
  human deciding (planned for spring 2026; launch not confirmed here). Deutsche Bank
  names credit risk assessment among the uses of a Google model and aims at much faster
  mortgage processing by 2028 (company statements).
- Creditworthiness assessment is high-risk under the EU AI Act.
- As in the US: no German bank was found where an LLM decides on a loan.

**Human evidence close to the setting.** A field experiment sent e-mails to 1,218 banks in
seven European countries, asking only for contact details for a loan or an investment.
Senders with domestic-sounding names got a reply in 55.2% of cases, senders with
Arabic-sounding names in 31.6%; for loan enquiries 59.8% against 35.1% (Stefan et al.
2018, PLoS ONE). One pooled Arab group, as in every other study. Whether Germany is among
the seven countries could not be confirmed from the article text.

**The group is large in Germany.** 915,840 Syrian nationals were registered at the end of
June 2026, of whom 70,018 held a settlement permit; about 58,000 Tunisian nationals at the
end of 2024. Figures for the other nationalities were not found in this pass.

**The nationality table fits.** German is the citizen benchmark, Turkish the classic
comparison group in German studies. Both are already in the table.

**What gets harder in Germany**

- **No public loan records.** The files have to be constructed from published averages
  (for mortgages for example: average loan about 270,000 to 283,000 euros, loan-to-value
  about 86%, fixed-rate period about ten and a half years, according to a broker's
  monthly indicator). That settles the synthetic-data rule in `ETHICS.md`, but the Data
  section of the report then describes constructed files, not real records.
- **No published template to copy.** The prompt and the fields have to be designed. The
  structure of Bowen et al. can be kept: a short file, one line swapped, approval and
  interest rate, three levels of credit quality (SCHUFA classes instead of a US score).
- **Language.** A German bank's file is in German. German-language prompts are on the
  parked list. An English prompt about a German bank is a realism gap that will be asked
  about; lifting that item from the parked list would be a team decision.
- **Residence status has to be fixed** in the file, for example an unlimited settlement
  permit for every non-German applicant. A German citizen has no permit, so the German
  benchmark differs in two lines, not one.

**United States or Germany.** The US version has real data and a published design, and a
weaker anchor for the nationality line. The German version has the stronger anchor (legal
duty to record it, new non-discrimination rule, human evidence from European banks) and
needs more construction. Running both would double the work for a 4 to 5 page report.

### 7.4 Open points before this could replace the current design

- `ETHICS.md` section 1 says applicants are synthetic. The US loan records are real,
  public and without names. Either the team accepts that and changes the ethics text, or
  the files are generated to resemble the public records.
- One cue only: country of citizenship or country of birth. The green card shows the
  country of birth, the passport the citizenship. Pick one before the pilot.
- A 13-line prompt in which one line is the nationality makes the cue very visible. The
  risk of over-correction and of the model recognising a test is the same as with the CV
  line, or higher.
- A model may bring up sanctions for some countries (Syria, Sudan, Yemen, Libya, Iraq,
  Somalia). For a permanent resident that is not a valid ground as far as I know (not
  checked); it would be worth coding in the answers if a reason is requested.
- It is a different project from the proposal of 2026-10-04: no jobs, no CVs, no
  choice between two, no promotion; research question 3 becomes United States versus
  Germany. Hypotheses and an analysis plan are needed before the first real run in any
  case.

### 7.5 What is actually used in mortgage lending, and what it reads

No lender was found that lets a general LLM read a short summary and decide. What is
documented has three layers:

| layer | examples | LLM? |
|---|---|---|
| The credit decision | Rule-based and statistical underwriting engines. Better says its engine "Tinman" decides about 40% of files automatically and that "deterministic rules drive credit decisions", with a language layer that explains them | No |
| Work around the decision | Rocket Logic (classifies about 70% of 1.5 million documents a month, extracts data from W-2s and bank statements); UWM with Google's Gemini; Blend Autopilot (live since July 2026 after 25,500 production loans, reads documents, cites the guidelines, calculates income, "non-decisioning"); Better's voice assistant "Betsy" and, since March 2026, its engine offered inside ChatGPT | Yes |
| A general LLM asked directly | The setting of Bowen et al., who call it a testbed | Yes, but not a documented product |

All figures are company statements.

**What the real systems read:** the application form (income, employment, assets, debts,
property, and citizenship status with three options), the credit report, pay stubs, W-2
and tax forms, up to 24 months of bank statements, appraisal and title documents, and
identity and immigration documents such as green card or passport. Race, ethnicity and
sex are collected for public monitoring, not for the decision. The country of citizenship
is not a form field; a system meets it in the identity documents, and indirectly in names
and transfers. One benchmark for LLM mortgage agents reports that models treat
non-English names as "foreign" (MortarBench, abstract).

**What the rulebook says:** Fannie Mae buys loans made to lawful permanent and
non-permanent residents on the same basis as loans to citizens (Selling Guide B2-2-02,
from a search summary). The official position is therefore: no difference.

**What our prompt would be:** a 13-line summary. It contains far less than a real file.
The honest description of the experiment is: LLMs are being built into mortgage work as
assistants that read the file; we measure what the underlying models do with a
nationality cue when they see one. It is not a test of a deployed product.

### 7.6 What the research would be, and how new (tentative)

**Question.** With an identical mortgage file and identical residence status, do LLMs
recommend different interest rates or approvals depending on which Arab League country
the applicant is a citizen of? Is the spread among the 22 larger than among placebo
countries? Does it follow country characteristics? Does a no-bias instruction remove it?
Does it hold across four open-weight models?

**Not new**

- LLM audits of lending: Bowen et al. (race, eight models); Cook and Kazinnik 2025 (race,
  open-source models, simulated mortgage applicants); `vohra2026audit` (names, no effect
  after correction); AgentFairBench 2026 (names, lending as one of three domains, no
  effect above noise for the one model tested).
- The method: swapping one explicit attribute on otherwise fixed files, and a no-bias
  instruction.
- That LLMs treat Arab countries differently in general (values and stereotypes; see
  `novelty_assessment.md`).

**Not found in this pass**

- An LLM lending experiment in which nationality or national origin is the treatment.
- One with Arab applicants as a group, or with individual Arab countries. The one
  candidate, `mohammad2026mirage` (Muslim versus non-Muslim cases, lending triage among
  the tasks), has no usable results according to our own literature matrix.
- A human field experiment on mortgage lending with Arab, Muslim or immigrant applicants
  in the United States. The known one uses Black and white names.

**What that means**

- The new element would be the same as in the hiring project, moved to credit:
  differences among individual Arab nationalities in a decision about a person, with the
  facts held fixed, measured against placebo countries.
- In hiring a pooled Arab result already exists (`lippens2024computer`). In lending none
  was found, so even the simple Arab-versus-benchmark comparison would be a first result
  here, and the objection "a predictable combination of known results"
  (`novelty_assessment.md` §6) is weaker.
- The other side: it is an existing design with a different variable. What carries it is
  the 22-country comparison with a noise floor, the placebo countries, the country
  covariates and the open-weight models.
- Possible framing hook: since 2024 US federal statistics have a single "Middle Eastern
  or North African" category. That set is not the Arab League set (`literature_review.md`
  §6.3), which has to be said.
- A null result is possible. In the one LLM study with countries of origin in an
  immigration decision, most country effects were not significant (Mao and Zhao 2025).

**Before any novelty sentence is written:** the searches here were a handful of web
queries. A search like the one behind `novelty_assessment.md` (arXiv, OpenAlex, SSRN,
finance and economics working-paper series) is needed for lending.

## 8. Sources and how far each was checked

Levels: **page** = official page read through a summarising fetch tool, quotes to be
re-checked; **snip** = search result snippet only.

| source | level | link |
|---|---|---|
| UK visa streaming tool: UK Human Rights Blog; Free Movement; Home Office inspection response | snip | https://ukhumanrightsblog.com/2020/08/06/government-scraps-immigration-streaming-tool-before-judicial-review/ |
| UK Home Office, Evaluation of AI trials in the asylum decision-making process (29 April 2025) | page | https://www.gov.uk/government/publications/evaluation-of-ai-trials-in-the-asylum-decision-making-process |
| Open Rights Group reports on the asylum tools (critical view) | snip | https://www.openrightsgroup.org/publications/automating-the-hostile-environment-ai-in-the-asylum-decision-making-process/ |
| Netherlands IOB: DutchNews, Lighthouse Reports, national algorithm register | snip | https://www.dutchnews.nl/2023/04/nl-uses-potentially-biased-algorithm-for-visa-applications , https://algoritmes.overheid.nl/en/algoritme/94596537 |
| Canada IRCC, advanced analytics for visa applications; Algorithmic Impact Assessment | snip | https://www.canada.ca/en/immigration-refugees-citizenship/news/notices/analytics-help-process-trv-applications.html |
| EU ETIAS Regulation 2018/1240, Article 33 | snip | https://www.legislation.gov.uk/eur/2018/1240/chapter/V |
| Statewatch on ETIAS and VIS profiling and rollout | snip | https://www.statewatch.org/news/2026/april/europe-s-uncertain-plans-for-rolling-out-the-automated-border-system-etias/ |
| Dubai GDRFA "Salama" platform | snip | https://economymiddleeast.com/news/dubai-launches-salama-ai-platform-for-quicker-easier-visa-renewals |
| Kuwait visa bans by nationality (Gulf News) | snip | https://gulfnews.com/news/gulf/kuwait/kuwait-bans-visa-issuance-to-five-nationalities-1.810834 |
| UAE visa suspension for nine countries (media reports on an unconfirmed circular) | snip | https://www.businesstoday.in/amp/nri/visa/story/uae-suspends-tourist-and-work-visas-for-these-nine-countries-amid-2026-visa-strategy-495247-2025-09-23 |
| VFS Global generative-AI chatbot | snip | https://traveltradejournal.com/vfs-global-launches-ai-powered-chatbot-for-uk-visa-customers-in-141-countries/ |
| US plans for AI in visa processing (wire report, law-firm notes) | snip | https://www.siasat.com/us-plans-ai-push-for-visa-processing-3496524/ |
| Mao and Zhao 2025, Digital Gatekeepers (arXiv 2506.21574 v1) | page | https://arxiv.org/abs/2506.21574 |
| Henley Passport Index 2026 (press reports) | snip | https://www.zawya.com/en/economy/uae-passport-the-worlds-second-strongest-in-latest-henley-index-405201 |
| Schengen refusal rates 2024 (secondary sites) | snip | https://hellosafe.com/schengen-visa/rejection |
| German asylum office dialect recognition: AlgorithmWatch; Verfassungsblog (22 June 2026) | snip | https://algorithmwatch.org/en/bamf-dialect-recognition/ |
| FATF lists June 2026 | snip | https://www.fatf-gafi.org/en/publications/Fatfgeneral/outcomes-fatf-plenary-june-2026.html |
| HSBC account closures of Syrians, 2014 (Middle East Eye) | snip | https://www.middleeasteye.net/news/hsbc-shuts-accounts-syrians-uk-after-lobbying-assads-cousin |
| Airwallex LLM onboarding checks | snip | https://fintechnews.sg/81791/ai/airwallex-taps-generative-ai-to-speed-up-kyc-reduces-false-positives-by-50/ |
| Galperin and Greppi 2017, geographical discrimination on a labour platform | snip | https://annenberg.usc.edu/sites/default/files/2017/11/27/Geographical%20Discrimination%20Galperin%20%26%20Greppi.pdf |
| Bowen, Price, Stein and Yang, Measuring and Mitigating Racial Disparities in LLMs: Evidence from a Mortgage Underwriting Experiment (version 17 Sept 2025) | **full text read** (sections 1-4, appendix settings) | https://www.aeaweb.org/conference/2026/program/paper/t484eTf2 |
| US mortgage application Form 1003, citizenship options (Fannie Mae) | snip | https://singlefamily.fanniemae.com/media/document/pdf/1003-borrower-information |
| Regulation B on immigration status and national origin; withdrawal of the 2023 CFPB-DOJ statement (Federal Register, January 2026) | snip | https://www.govinfo.gov/content/pkg/FR-2026-01-12/html/2026-00328.htm |
| German loan self-disclosure forms: nationality and residence permit | snip | https://www.capitalo.de/kredit/fuer-auslaender |
| German anti-money-laundering act, § 11 (identification data incl. nationality) | snip (summary of the statute) | https://www.gesetze-im-internet.de/gwg_2017/__11.html |
| EU consumer credit directive 2023/2225, Articles 6 and 18; German implementing act (BGBl. 18 May 2026, in force 20 Nov 2026) | snip | https://klardenker.kpmg.de/financialservices-hub/regulatory-update/gesetz-zur-umsetzung-der-verbraucherkreditvertraege-richtlinie-im-bgbl-veroeffentlicht/ |
| EU Court of Justice C-634/21 (SCHUFA scoring), 7 Dec 2023; SCHUFA information sheet on data not used | snip | https://cms.law/de/deu/legal-updates/das-schufa-urteil-des-eugh-und-dessen-auswirkungen |
| ECB supervision newsletter Nov 2025 and EBA special topic on AI in EU banks | snip | https://www.bankingsupervision.europa.eu/press/supervisory-newsletters/newsletter/2025/html/ssm.nl251120_1.en.html |
| ING Germany AI-supported mortgage approval; Deutsche Bank AI plans (trade press) | snip | https://www.cio.de/article/4124841/ing-will-baukredite-mit-ki-in-30-minuten-pruefen.html |
| Stefan, Holzmeister, Muellauer and Kirchler 2018, Ethnical discrimination in Europe: field evidence from the finance industry, PLoS ONE 13(1) | page | https://pmc.ncbi.nlm.nih.gov/articles/PMC5788365/ |
| Foreign nationals in Germany by nationality (Bundestag answers, Destatis, Statista) | snip | https://www.bundestag.de/presse/hib/kurzmeldungen-1210956 |
| German mortgage averages (Dr. Klein Trendindikator Baufinanzierung) | snip | https://www.drklein.de/fileadmin/drk/ueber-dr-klein/pressemitteilungen/pm-drk-dtb-2025-dezember.pdf |
| AI in mortgage lending: Rocket Logic, Better (Tinman, Betsy, ChatGPT engine), UWM with Google Cloud, Blend Autopilot (trade press and company releases) | snip | https://www.housingwire.com/articles/vishal-garg-better-ai-betsy-tinman-mortgage-underwriting-technology/ , https://nationalmortgagenews.com/news/rocket-mortgage-rolls-out-ai-powered-platform-for-underwriting |
| Fannie Mae Selling Guide B2-2-02, non-U.S. citizen borrowers | snip | https://selling-guide.fanniemae.com/sel/b2-2-02/non-us-citizen-borrower-eligibility-requirements |
| Cook and Kazinnik 2025, Social Group Bias in AI Finance (arXiv 2506.17490) | abstract | https://arxiv.org/abs/2506.17490 |
| AgentFairBench (arXiv 2606.16723) | abstract | https://arxiv.org/abs/2606.16723 |
| Hanson et al. 2016, mortgage loan originators and applicant names (Journal of Urban Economics), via press reports | snip | https://jbhe.com/2016/03/university-study-finds-racial-discrimination-by-mortgage-loan-originators/ |
| US federal race and ethnicity standards 2024, new Middle Eastern or North African category (Census Bureau) | snip | https://www.census.gov/newsroom/blogs/random-samplings/2024/04/updates-race-ethnicity-standards.html |
| MortarBench, mortgage loan origination agents (arXiv 2606.19416) | abstract; the figures for Arabic names are from a search snippet | https://arxiv.org/abs/2606.19416 |
| Generative AI in lending: Casca with Live Oak and Huntington; S&P Global credit-memo case study; EY bank survey 2025 | snip | https://www.cascading.ai/news/huntington-live-oak-gen-ai-lending |
| Gulf loan terms for nationals and expatriates (FAB, UAB, Citibank UAE, aggregator sites) | snip | https://bankfab.com/en-ae/personal/loans/personal-loans-for-expats |
| SafeRent tenant-screening settlement 2024 (AP) | snip | https://abcnews.go.com/US/wireStory/class-action-lawsuit-ai-related-discrimination-reaches-final-116075869 |
| Flage, meta-analysis of rental correspondence tests in OECD countries | snip | https://drm.dauphine.fr/fileadmin/mediatheque/drm/documents/Flage.pdf |
| Liu, So, Hosoi and D'Ignazio 2024, racial steering by GPT-4 in housing recommendations | snip | https://dspace.mit.edu/handle/1721.1/157628 |
| Dubai tenancy registration documents; German tenant self-disclosure and nationality | snip | https://www.wasl.ae/en/node/370 , https://deutschesmietrecht.de/mietvertrag/bonitaet/446-selbstauskunft-wohnungssuche.html |
| Foreign property ownership rules: Saudi Arabia 2026, UAE, Kuwait, Jordan (law-firm notes) | snip | https://cms.law/en/sau/legal-updates/opening-up-of-the-real-estate-market-in-saudi-arabia-to-non-saudi-owners-and-investors |
| Fictional or unnamed countries in experiments: Brutger et al. 2023 (AJPS); Majnemer and Meibauer (ISQ); arXiv 2605.23825 | snip | https://dtingley.scholars.harvard.edu/publications/abstraction-and-detail-experimental-design |

## 9. Not covered

- A systematic search for LLM audits of visa, asylum or banking decisions.
- How Gulf immigration authorities process work permits, and any official list of
  nationality restrictions. The reports above are press reports.
- The primary documents: the UK court papers, the Canadian impact assessment, the Dutch
  parliamentary letters, the Henley and European Commission data.
- Insurance, credit, housing and university admission.
