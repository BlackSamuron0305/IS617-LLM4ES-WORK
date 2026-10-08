# Ethics statement and handling rules

This repository audits how large language models behave when the stated nationality of
a synthetic bank customer changes. It is a measurement instrument for discriminatory
model behaviour. It is not a tool for checking customers, and nothing in it evaluates
real people.

Rewritten on 2026-10-08, when the project moved from hiring to bank customer checks.
The version for the hiring design is in git history (commit 272792d).

## 1. Synthetic customers, bank and employers

- The 20 customer files in `experiment/customers/customers.csv` were written for this
  project. No real person, bank customer, account or employer record was used or
  adapted. Incomes are invented and were not taken from wage statistics.
- Customers carry a customer reference instead of a name. There are no photos, gender
  markers, religion fields, addresses or places of birth. The file states a year of
  birth.
- The bank ("Lindenufer Bank") is invented. A web search on 2026-10-08 found no bank of
  that name. If the name turns out to coincide with a real organisation, it is replaced.
  Employers are described, not named.
- The policy text is a paraphrase of public rules written for the experiment. It is not
  a real bank's policy and not legal advice.
- Because no human participants are involved and no personal data is processed, the
  current study does not require review by a human-subjects ethics board. Section 9
  covers what changes if human validation is added.

## 2. No deployment for customer checks

The code, prompts, policy text and model outputs must not be used to rate, accept or
refuse real customers. The prompts deliberately simulate a compliance assistant so that
model behaviour can be measured under controlled conditions. That is not an endorsement
of LLM-based customer checks. From 10 July 2027, Regulation (EU) 2024/1624 requires
meaningful human intervention and a right to an explanation where such decisions result
from automated processes or AI systems (Article 76(5), read on 2026-10-08). Whether a
system of this kind is high-risk under the EU AI Act has not been checked. [VERIFY
before saying anything about the AI Act.]

## 3. No claims about real national groups

The study manipulates a label and observes a model. A difference in model output
between two nationality labels is evidence about **the model**: the associations it has
absorbed and how it acts on them. It is never evidence about the honesty, the finances
or the risk of people from those countries. By construction every customer file is
identical, so any systematic difference is unjustified by the file.

Reports, slides and figure captions must state this plainly wherever country-level
estimates appear.

## 4. Nationality as a sensitive attribute

- Money-laundering law works with countries. The European Commission lists high-risk
  third countries, and four Arab League members are on the list used here (Algeria,
  Lebanon, Syria, Yemen; as of 29 January 2026). The published rules that were read tie
  this to where a customer lives and where payments go, and a customer who is legally
  resident in the EU must not be disadvantaged on account of nationality when opening a
  payment account. The sources and the sections read are in
  `experiment/policy/README.md` and `research/literature_matrix.csv`. The study does not
  assess legality, nobody on the team is a lawyer, and practice in banks may differ from
  the rules. A model that rates a listed country's passport higher may be reproducing
  that practice. This is why the list status is recorded and reported separately rather
  than every difference being read as stereotyping.
- Being on the list is a statement about a state's financial system. It is never
  presented as a statement about that country's people.
- Nationality ≠ ethnicity ≠ religion. MENA ≠ Arab. Arab ≠ Muslim. The manipulated
  construct is a **nationality signal**. We estimate the total effect of the signal and
  do not claim that a model "discriminates against Muslims" or against any ethnic group
  unless a separate, targeted design supports that.
- Arab League membership is a political definition. Three members (Somalia, Djibouti,
  Comoros) have contested Arab identity; they stay in every comparison and are pointed
  out. Palestine's statehood is contested internationally; it is included because
  "Palestinian" is a widely used national identity, not as a political statement.

## 5. Risk of reproducing harmful stereotypes

- Free-text model reasons may contain stereotypes, for example links between a
  nationality and terrorism, sanctions or crime. Raw outputs are released only for
  research (Section 8). Stereotyped text is never quoted in presentations without
  context, and never used as a headline or pull-quote.
- Any coding of the reasons exists to detect unsupported inferences. It does not endorse
  them.

## 6. Responsible presentation of country-level findings

- Country-level point estimates carry uncertainty intervals. A "league table" of
  countries without intervals is not published.
- Country rankings are not described as stable properties of "LLMs" in general. They are
  specific to the model versions, prompts, policy text and dates of the runs.
- Null results are reported with the same prominence as disparities. "p > .05" is never
  reported as "no bias".
- Findings about a country are not framed in ways that invite ridicule or hostility
  toward its people, for example headlines that rank nationalities by "risk".
- How the estimates are tested is not decided yet. The analysis plan has to be written
  before the first real run and this section updated with it.

## 7. Limitations of nationality labels and temporal dependence

- Two lines in a customer file are a thin, stylised signal. Real unequal treatment in
  banking also works through names, documents, payment patterns and screening hits that
  this design deliberately removes. Estimates are specific to this signal and do not
  bound real-world harm in either direction.
- The products sold for customer checks are not tested. Their models, prompts and inputs
  are not public.
- Model behaviour depends on version, decoding settings and prompts. Every run records
  exact model identifiers, parameters and timestamps. Results are claims about those
  configurations on those dates.
- The list of high-risk countries changes several times a year. Results refer to the
  list of one date.

## 8. Release of prompts, stimuli and data

- Released: code, prompt templates, the policy text, customer files, the nationality
  table, run records, processed tables, analysis outputs.
- Raw model outputs are released for reproducibility. Before public release they are
  scanned for content that could cause harm out of context (slurs, explicit
  stereotyping). Flagged records remain available to reviewers but are marked in the
  release notes.
- No API keys or credentials are ever committed (`.env` is gitignored).

## 9. If human validation is added later

Any extension involving people, such as rating the realism of the customer files or
annotating reasons, requires:

- review under the University of Mannheim's procedures for research involving human
  participants before data collection;
- informed consent, data-protection compliance (GDPR), and pseudonymised storage;
- protection for annotators exposed to stereotyped model text (content warnings,
  opt-out, limited exposure).

## 10. Authorship and AI use

Claude (Anthropic) assisted with design, code, analysis and internal research documents
in this repository, including the policy text, the customer files and the prompts. Per
the course AI-usage policy, report and presentation prose is written by the team, and AI
use is declared per task.
