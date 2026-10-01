# Ethics statement and handling rules

This repository audits how large language models behave when the stated national
origin of a synthetic job applicant changes. It is a measurement instrument for
discriminatory model behaviour. It is not a recruitment tool, and nothing in it
evaluates real people.

## 1. Synthetic applicants and employers

- Every CV was built from curated component pools (`stimuli/building_blocks/*.csv`,
  `scripts/build_cv_table.py`) into one table (`stimuli/cvs.csv`). No real CV,
  applicant, employee or employer record was used or adapted.
- Applicants carry an applicant reference number instead of a name. There are no
  photos, dates of birth, gender markers or religion fields.
- Employer names are invented. If an invented name turns out to coincide with a real
  organisation, it is replaced. Real universities and colleges in the eight base
  countries (UAE, Saudi Arabia, Qatar, Kuwait, Oman, Bahrain, Jordan, Egypt) appear
  as education entries because credential realism matters. They are held constant
  across clones, so no claim about any institution follows from the data.
- Because no human participants are involved and no personal data is processed,
  the current study does not require review by a human-subjects ethics board.
  Section 9 covers what changes if human validation is added.

## 2. No deployment for hiring

The code, prompts and model outputs must not be used to screen, rank or select real
applicants. The prompts deliberately simulate a recruiter so that model behaviour
can be measured under controlled conditions. That is not an endorsement of
LLM-based screening. Under the EU AI Act, where the research team is based, AI
systems used for recruitment and selection are classified as high-risk (Annex III);
any real deployment falls under obligations that this project does not attempt to
meet. [VERIFY exact annex wording before citing.]

## 3. No claims about real national groups

The study manipulates a label and observes a model. A difference in model output
between two national-origin labels is evidence about **the model**: the
associations it has absorbed and how it acts on them. It is never evidence about
the abilities, qualifications or employability of people from those countries. By
construction every clone is equally qualified, so any systematic difference is,
by definition, unjustified by the record.

Reports, slides and figure captions must state this plainly wherever country-level
estimates appear.

## 4. Nationality as a sensitive attribute

- The stimuli are set in Arab labour markets, where the legal treatment of
  nationality in hiring differs from Europe. Several Gulf states run nationalisation
  policies (for example Emiratisation and Saudisation) that explicitly favour
  citizens in parts of private-sector hiring, alongside labour-law provisions against
  some forms of discrimination. [VERIFY the specific laws and their wording before
  any of this appears in the paper.] The study does not assess legality. A model that
  prefers host nationals may be reproducing such policies, which is why host status
  (`host_national`) is recorded, adjusted for, and reported separately rather than
  being read as stereotyping. Whatever the legal classification, national origin is
  treated as a sensitive attribute throughout, because a label that carries no
  job-relevant information should not move a screening decision on the record.
- Nationality ≠ ethnicity ≠ religion. MENA ≠ Arab. Arab ≠ Muslim. The manipulated
  construct is a **national-origin signal**. We estimate the total effect of the
  signal and do not claim that a model "discriminates against Muslims" or against
  any ethnic group unless a separate, targeted design supports that.
- Arab League membership is a political definition. Three members (Somalia,
  Djibouti, Comoros) have contested Arab identity and are covered by a
  pre-registered sensitivity analysis. Palestine's statehood is contested
  internationally; it is included because "Palestinian" is a widely used national
  identity on real CVs, not as a political statement.

## 5. Risk of reproducing harmful stereotypes

- Free-text model reasons may contain stereotypes. Raw outputs are released only for
  research (Section 8). Stereotyped text is never quoted in presentations without
  context, and never used as a headline or pull-quote.
- The exploratory text coding (mentions of language, visa, "cultural fit",
  religion, conflict) exists to detect unsupported inferences. It does not endorse
  them.
- An optional red-team condition, if ever added, stays separate from the primary
  audit and is reported as such. "Forced choice" is a measurement format, not a
  jailbreak, and is never described as one.

## 6. Responsible presentation of country-level findings

- Country-level point estimates carry uncertainty intervals and are interpreted
  through the pre-registered hierarchy (global test → model-based estimates →
  pre-registered contrasts → FDR-corrected exploratory comparisons). A "league
  table" of countries without intervals is not published.
- Country rankings are not described as stable properties of "LLMs" in general.
  They are specific to the model versions, prompts and dates recorded in the run
  manifests.
- Null and equivalence results are reported with the same prominence as
  disparities. "p > .05" is never reported as "no bias". Equivalence is claimed only
  against the pre-specified smallest effect size of interest.
- Findings about a country are not framed in ways that invite ridicule or
  hostility toward its people, for example headlines that rank nationalities.

## 7. Limitations of nationality labels and temporal dependence

- A single CV line is a thin, stylised signal. Real discrimination operates through
  names, photos, accents, credentials and networks that this design deliberately
  removes. Estimates are specific to this signal and do not bound real-world harm
  in either direction.
- Model behaviour depends on version, provider-side updates, decoding settings and
  prompts. Every run records exact model identifiers, parameters, prompt hashes and
  timestamps. Results are claims about those configurations on those dates.

## 8. Release of prompts, stimuli and data

- Released: code, configs, prompt templates, base CVs, generated stimuli, validation
  diffs, run manifests, processed tables, analysis outputs.
- Raw model outputs are released for reproducibility. Before public release they are
  scanned for content that could cause harm out of context (slurs, explicit
  stereotyping). Flagged records remain available to reviewers but are marked in
  the release notes.
- No API keys or credentials are ever committed (`.env` is gitignored;
  `.env.example` holds placeholders only).
- Provider terms of service are checked before releasing outputs from commercial
  models.

## 9. If human validation is added later

Any extension involving people, such as rating CV realism, perceived
qualification equivalence or annotating reasons, requires:

- review under the University of Mannheim's procedures for research involving
  human participants before data collection;
- informed consent, data-protection compliance (GDPR), and pseudonymised storage;
- protection for annotators exposed to stereotyped model text (content warnings,
  opt-out, limited exposure).

## 10. Authorship and AI use

Claude (Anthropic) assisted with design, code, analysis and internal research
documents in this repository. Per the course AI-usage policy, report and
presentation prose is written by the team, and AI use is declared per task.
