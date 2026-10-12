# Ethics statement and handling rules

This repository audits how large language models behave when the stated nationality of
a synthetic visa applicant changes. It is a measurement instrument for discriminatory
model behaviour. It is not a tool for assessing applicants, and nothing in it evaluates
real people.

Rewritten on 2026-10-10, when the project moved from bank customer checks to visitor
visa applications. The version for the bank design is in git history (commit 39d32f2),
the one for the hiring design in commit 272792d.

## 1. Synthetic applicants and employers

- The 20 applications in `experiment/applicants/applicants.csv` were written for this
  project. No real person, visa application or employer record was used or adapted.
  Incomes and savings are invented and were not taken from statistics.
- Applicants carry a reference number instead of a name. There are no photos, gender
  markers, religion fields or addresses. The application states a year and a city of
  birth; the city is in the United Arab Emirates for everybody.
- No visa office is named. The prompt speaks of "an Australian visa office". The
  Australian Department of Home Affairs does not run this system and has not seen this
  material. Employers are described, not named.
- The guidance text is a paraphrase of public rules written for the experiment. It is
  not an official text and not legal advice.
- Because no human participants are involved and no personal data is processed, the
  current study does not require review by a human-subjects ethics board. Section 9
  covers what changes if human validation is added.

## 2. No deployment for visa decisions

The code, prompts, guidance text and model outputs must not be used to rate, grant or
refuse real applications. The prompts deliberately simulate a case assistant so that
model behaviour can be measured under controlled conditions. That is not an endorsement
of LLM-based visa processing. No authority is documented as using a language model to
rate visa applications, and the systems that do sort applications leave every refusal to
a person. Annex III of the EU AI Act lists systems that assist in examining visa
applications among the high-risk uses (read on 2026-10-10 in an unofficial copy through
a summarising tool). [VERIFY in the Official Journal before saying more about the AI
Act.]

## 3. No claims about real national groups

The study manipulates a label and observes a model. A difference in model output
between two nationality labels is evidence about **the model**: the associations it has
absorbed and how it acts on them. It is never evidence about the honesty, the intentions
or the risk of people from those countries. By construction the person in every
application is the same and so is the legal status the application states; what
differs is the passport.

Reports, slides and figure captions must state this plainly wherever country-level
estimates appear.

## 4. Nationality and religion as sensitive attributes

- The motivation of the project is Islamophobia. The experiment does not state a
  religion anywhere. It varies a nationality. Nationality ≠ ethnicity ≠ religion. MENA ≠
  Arab. Arab ≠ Muslim. The manipulated construct is a **nationality signal**. We
  estimate the total effect of the signal and do not claim that a model "discriminates
  against Muslims" or against any ethnic group. What the design can show is whether a
  model treats the 22 Arab League nationalities differently from one another although
  the application and the official rules are the same.
- Visa law works with nationalities. Real systems grant and refuse at very different
  rates by nationality, Australian law still allows a list of risk groups defined by
  nationality (none in force since 2009, as far as could be checked), and the
  department's instruction lets officers use statistics about other nationals of a
  country to look closer. The same instruction defines the home country as the country
  of usual residence. The sources and the passages read are in
  `experiment/policy/README.md`. The study does not assess legality, nobody on the team
  is a lawyer, and practice may differ from the published rules. A model that rates a
  passport worse may be reproducing that practice. That explains where a difference
  may come from; it does not justify it for identical applications. The yardstick of
  the project is the official rules in force, which are the same for all 22
  (`experiment/countries/official_rules.csv`).
- Real grant and refusal rates by nationality describe real applicants in very different
  circumstances. They are never presented as a statement about the people of a country,
  and never as evidence that a difference is justified or unjustified.
- Arab League membership is a political definition. Three members (Somalia, Djibouti,
  Comoros) have contested Arab identity; they stay in every comparison and are pointed
  out. Palestine's statehood is contested internationally; it is included because
  "Palestinian" is a widely used national identity, not as a political statement.
- The four placebo nationalities (Uruguayan, Malawian, Maldivian, Cambodian) are a
  noise check and were chosen before any data. Being chosen says nothing about a
  country.

## 5. Risk of reproducing harmful stereotypes

- Free-text model reasons may contain stereotypes, for example links between a
  nationality and overstaying, asylum claims, terrorism or crime. Raw outputs are
  released only for research (Section 8). Stereotyped text is never quoted in
  presentations without context, and never used as a headline or pull-quote.
- One exception with context: the pitch starts, after the title screen, with three
  endings that GPT-3 wrote for "Two Muslims walked into a", quoted from a published
  study (Abid, Farooqi and Zou 2021). The slide names them as model output, gives the source and the count behind
  them (66 of 100), and is there to show the problem the project is about.
- Any coding of the reasons exists to detect unsupported inferences. It does not endorse
  them.

## 6. Responsible presentation of country-level findings

- Country-level point estimates carry uncertainty intervals. A "league table" of
  countries without intervals is not published.
- Country rankings are not described as stable properties of "LLMs" in general. They are
  specific to the model versions, prompts, guidance text and dates of the runs.
- Null results are reported with the same prominence as disparities. "p > .05" is never
  reported as "no bias".
- Findings about a country are not framed in ways that invite ridicule or hostility
  toward its people, for example headlines that rank nationalities by "risk".
- Money figures are illustrations of a model's behaviour, not forecasts of what visas
  cost anybody. Every figure says which measure it is (`experiment/costs/README.md`).
- How the estimates are tested is not decided yet. The analysis plan has to be written
  before the first real run and this section updated with it.

## 7. Limitations of nationality labels and temporal dependence

- Two lines in an application are a thin, stylised signal. Real unequal treatment at
  borders also works through names, places of birth, travel histories and interviews
  that this design deliberately removes or holds constant. Estimates are specific to
  this signal and do not bound real-world harm in either direction.
- All applicants are set in the United Arab Emirates, where people of many of these
  nationalities are born and raised without becoming citizens. Not every one of the 49
  nationalities has a sizeable community there, and the incomes are invented. Every
  application states the same legal status: a lawful long-term resident with the full
  right to live and work there.
- That line simplifies reality. An Emirati living in the Emirates is a citizen, citizens
  of the other Gulf states need no visa there, and most other residents hold a visa that
  depends on their job. A model may know this and act on it. A difference between two
  passports is therefore reported as the weight a model gives the passport, and not
  every difference is called prejudice.
- Model behaviour depends on version, decoding settings and prompts. Every run records
  exact model identifiers, parameters and timestamps. Results are claims about those
  configurations on those dates.
- Visa rules, fees, the passport index and travel bans change. Results and yardsticks
  refer to the dates stated with them.

## 8. Release of prompts, stimuli and data

- Released: code, prompt templates, the guidance text, applications, the nationality
  table, run records, processed tables, analysis outputs.
- Raw model outputs are released for reproducibility. Before public release they are
  scanned for content that could cause harm out of context (slurs, explicit
  stereotyping). Flagged records remain available to reviewers but are marked in the
  release notes.
- The parked table in `research/visa_scenario/parked_comparison_set/` contains figures
  from the Henley Passport Index and the Pew Research Center. Check their terms before a
  public release of that table.
- No API keys or credentials are ever committed (`.env` is gitignored).

## 9. If human validation is added later

Any extension involving people, such as rating the realism of the applications or
annotating reasons, requires:

- review under the University of Mannheim's procedures for research involving human
  participants before data collection;
- informed consent, data-protection compliance (GDPR), and pseudonymised storage;
- protection for annotators exposed to stereotyped model text (content warnings,
  opt-out, limited exposure).

## 10. Authorship and AI use

Claude (Anthropic) assisted with design, code, analysis and internal research documents
in this repository, including the guidance text, the applications, the prompts, the
table of official rules, the first drafts of the proposals and the
pitch slides. Per the course AI-usage policy, report and presentation prose is written
by the team, and AI use is declared per task.
