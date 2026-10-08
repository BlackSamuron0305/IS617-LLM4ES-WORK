# Does the nationality line reach the model in a real pipeline? (internal review)

Written on 2026-10-08 by Claude at Laith's request. Internal research note, **not report
text**. It follows up on one point of `prompt_realism_review.md`: whether a
`Nationality:` line on a CV would get as far as the model that scores the CV, or would be
removed on the way by parsing or redaction.

Limits: one afternoon of web search, English and some German, no systematic search.
Vendor pages were read through a fetch tool that summarises them, so quotes have to be
checked against the original before use. Vendor statements are the vendors' own
descriptions, not tested behaviour. Two GitHub repositories and one redaction tool were
checked directly. Verification levels are in section 6. The new sources are **not yet in
`research/literature_matrix.csv`**.

## 1. Short answer

My sentence in the first note ("parsing or redaction would likely drop it") was too
strong. The corrected picture:

1. **Direct use and raw-text tools: the line reaches the model word for word.** This
   covers a recruiter pasting or uploading a CV into a chat model, no-code workflows that
   extract the PDF text and send it to an LLM, and open-source screeners such as
   `sliday/resume-job-matcher`.
2. **Commercial CV parsers do not drop nationality. They extract it as a field of its
   own.** Textkernel, RChilli and Affinda all document a nationality field, and they keep
   the full CV text as well. After parsing, the information is in the system twice.
3. **The scoring step of the Western vendor features I could document does not get it.**
   Greenhouse sends only skills, job titles, years, dates and company names to its
   matching models. Workday says demographic data is never part of HiredScore grades.
   Ashby says it redacts PII before the CV goes to the model, without listing the fields.
4. **Redaction comes in two kinds, and only one removes nationality.** Narrow redaction
   (name, contact details, photo: Workable, Teamtailor) leaves the line in place.
   Bias-oriented redaction removes it: Greenhouse's anonymisation lists
   "race/ethnicity/nationality", and the open-source tool Presidio, in its default
   setting, removed the nationality value in 96% of our own CV versions (section 3.5).
5. **In the Arab region nationality is meant to be seen.** It is a standard CV field, a
   structured profile field on Bayt, GulfTalent and Naukrigulf, and a search filter for
   recruiters. I found no public statement on whether the AI ranking of regional tools
   uses it.

For the study this means: the treatment is realistic for direct use everywhere, and for
the region it is realistic that nationality is present and visible in the data. It is not
realistic for the AI scoring of Western enterprise systems. The pseudonymisation sentence
in our main prompt (names and contact details removed, nationality still there) matches
the narrow kind of redaction, which exists in real products.

## 2. The path of a CV, stage by stage

| stage | what happens to a `Nationality:` line | evidence |
|---|---|---|
| 1. Applicant writes the CV | Gulf and wider Arab-region CVs usually state nationality and visa status. US and UK CVs normally do not. Europass has the field, marked optional | recruiter-firm and CV-guide advice (weak sources); Europass template |
| 2. Applicant fills a profile or application form | Job portals in the region ask for nationality as a structured field. Workday can switch on nationality and citizenship fields per country | Talentera/Bayt help pages; Workday admin guide |
| 3. CV is parsed | Commercial parsers extract nationality into its own field and keep the full text. Open-source parsers built on JSON Resume or similar have no such field | Textkernel, RChilli, Affinda documentation; JSON Resume schema, OpenResume, pyresparser |
| 4. CV is redacted or anonymised (optional step) | Depends on the product: name/contact/photo only, or a longer list that includes nationality | Workable, Teamtailor, Greenhouse, Presidio |
| 5. A model scores or ranks | Raw-text tools pass everything. Field-based scoring passes a short list of job-related fields | sliday, hiring-agent, Greenhouse, Workday |
| 6. A recruiter looks at the result | In the region the recruiter can filter by nationality directly. Western anonymised screening hides some fields at this stage only | Bayt, GulfTalent, Naukrigulf; Workable, Teamtailor |

## 3. Evidence in detail

### 3.1 Is nationality on the CV in the first place?

- **Arab region:** CV guides for the UAE and Saudi Arabia list nationality and visa or
  Iqama status as standard fields, and tie this to visa handling and to Emiratisation and
  Saudization quotas. These are commercial CV-advice sites and recruiter blogs; no
  academic source on CV conventions in the region turned up.
- **Europe:** the Europass template has "Nationality(-ies)" with the note "remove if not
  relevant". All fields are optional.
- **US and UK:** nationality is normally left out. Most LLM hiring audits come from this
  setting, which is why they work with names.
- Our own literature review already notes four human correspondence studies that put
  nationality or birth country on the CV (`literature_review.md` §6.2).

### 3.2 Parsing: commercial parsers keep it, as a separate field

| parser | nationality in the output? | full text kept? |
|---|---|---|
| Textkernel (also sold as Sovren; used by Bullhorn, Sage and others) | Yes. `personal.nationality.code` and `.description`: "The nationality of the candidate, normalized to the ISO 3166-1 alpha-2 classification." Also birth date, birth place, gender, national ID, driving licences | Yes: `documentText` and `documentHtml` |
| RChilli | Yes. "Other Personal Information" lists Nationality next to DateOfBirth, Gender, MaritalStatus, VisaStatus and passport details. A help article says nationality mentioned in the resume is extracted, ethnicity is not | Output lists `DetailResume` and `HtmlResume`; content not confirmed |
| Affinda | Yes. Personal information: name, date of birth, birthplace, nationality, headshot, "Right to work (visa)". Older API versions list date of birth but not nationality | A `rawText` field appears in the sample |
| JSON Resume (schema used by HackerRank's hiring-agent) | No. `basics` has name, label, image, email, phone, url, summary, location, profiles | not applicable |
| OpenResume (about 8,900 GitHub stars) | No. Profile: name, email, phone, url, summary, location | not applicable |
| pyresparser (about 950 stars) | No. Name, email, phone, skills, experience, college, degree, designation, companies | not applicable |

So the answer to "does parsing drop it?" is split. In the commercial stack it is
preserved and normalised to a country code. That makes it more usable for filtering, not
less. In open-source stacks it has no place to go.

What this looks like in one open-source pipeline, read in the code of
`interviewstreet/hiring-agent`: six LLM calls each extract one section into JSON
(`basics`, `work`, `education`, `skills`, `projects`, `awards`). The scoring call does
not see the PDF text. It sees a text rebuilt from that JSON (`convert_json_resume_to_text`
in `transform.py`), beginning with `Name:`, `Email:`, `Phone:`, `Website:`, `Summary:`,
`Location:`. A nationality line survives only if the extraction model happens to copy it
into the summary. The applicant's name, by contrast, is passed to the scoring model,
although the fairness block tells the model not to use it.

### 3.3 What the scoring model receives

| tool | what goes to the model | nationality reaches it? |
|---|---|---|
| Chat model used directly | whatever the recruiter pastes or uploads | Yes |
| No-code templates (n8n and similar; listings only, workflow files not opened) | PDF text extracted and sent to GPT or Gemini with the job description | Yes, as far as the descriptions go |
| `sliday/resume-job-matcher` | the full PDF text (`resumeText`) in the gate prompt and in the scoring prompt | Yes |
| `interviewstreet/hiring-agent` | text rebuilt from extracted JSON | Normally no |
| Greenhouse Talent Matching | "skills, years of experience, job titles, start/end dates of employment, and company names". "The system does not use names or any contact information", "does not process special category data", and form answers are not included | No |
| Workday HiredScore | datasheet: "Gender/race and other demographic data is never incorporated into the scores/grading system and correlated features are also removed." Nationality is not named | Probably no; not stated |
| Ashby | the resume, with "PII" redacted; criteria can also check free-text form answers. The redacted fields are not listed publicly | Unknown |
| Textkernel Match | weighted criteria in 8 categories; examples are job title, skills, education. Fields used are not listed in what I could read | Unknown |
| Talentera (Bayt), Qureos, Elevatus | marketing pages speak of "fit ranking" and criteria set by the customer; inputs are not listed | Unknown |

### 3.4 Redaction and anonymisation

| product | what is hidden | nationality hidden? | from whom |
|---|---|---|---|
| Workable anonymized screening | name, address, phone number | No | human reviewers |
| Teamtailor anonymous stage | personal information on the candidate card; names and pictures in the attached CV | Not listed | human reviewers |
| Greenhouse resume anonymization | name, titles, suffixes, gender, photo, "race/ethnicity/nationality", marital status, address, email, phone, social links | **Yes** | human reviewers in application review |
| Eightfold candidate masking | name, gender, race; more by configuration | by configuration; list not public | human reviewers |
| Ashby | "PII" | not stated | the model |
| Microsoft Presidio (open source) | default recognisers include `NRP`, nationality / religious / political group, taken from the language model's NORP label | **Yes by default** (section 3.5) | whatever comes next |
| German pilot of anonymised applications, 2010–2012 (`krause2012anonymous`) | per a Bundestag summary: name, gender, nationality and place of birth, disability, date of birth or age, marital status, photo | **Yes** | human reviewers |

Two observations:

- Most of these features hide information from the **human** reviewer. Only Ashby's
  statement and the Greenhouse matching description are about what the **model** gets.
- "Pseudonymised: names and contact details replaced" in our main prompt describes the
  narrow version (Workable, Teamtailor). The version designed against discrimination
  (Greenhouse, the German pilot) removes nationality as well. Both exist.

`chen2026beyond` and `tan2026small` add that redaction does not close the channel even
when it is applied: models recover the group from the remaining text, most easily from
language fields. In our CVs the languages are held constant, so this route is closed by
design, and the explicit line is the only cue.

### 3.5 Tool test: a standard redactor on our own CVs

This is a test of a tool, **not an experiment result**, and it involved no LLM call. I
rendered our 20 CVs with each of the 28 stated nationalities and ran Microsoft Presidio
(default configuration, spaCy `en_core_web_lg`) over each version. The script and its
environment are in the session scratch folder, not in the repository.

Result over all 22 job countries, 12,320 CV versions (20 CVs x 28 nationalities x 22
countries):

- The nationality value was flagged as `NRP` in **11,880 of 12,320** versions (96.4%).
- 27 of the 28 demonyms were flagged in every one of their 440 versions. **"Djiboutian"
  was never flagged** (0 of 440). The job country made no difference to this.
- With the default anonymiser the line becomes `Nationality: <NRP>`.
- The country in `Location: {country}` was flagged as a location in 10,080 versions
  (81.8%), so the same step would usually remove the country of the job from the CV as
  well, but not for every country.
- There were false alarms that damage the CV: `English (C1)` became
  `English (<US_DRIVER_LICENSE>)`, and durations and dates were replaced by `<DATE_TIME>`.

What it shows: a pipeline that puts an off-the-shelf PII filter with default settings in
front of the model would remove our treatment almost entirely, but not evenly. A
nationality the tool does not know passes through. A filter restricted to names, e-mail
addresses and phone numbers, which is the common narrow set-up, would not touch the line.

### 3.6 Platforms in the Arab region

- **Bayt.com**: the employer guide says CV Search criteria include "location,
  nationality, skills, languages spoken, last employer, education". A third-party listing
  speaks of 33 filters including visa status and nationality. Bayt's help pages for
  profiles list nationality, additional nationalities and visa status among the personal
  details.
- **Talentera** (Bayt's ATS): the help centre describes a nationality filter in CV search
  ("Nationality, where relevant to the role"); a search summary says it works in include
  and exclude mode, which I could not confirm on the page. Marketing lists Saudization
  tracking and Emiratisation workflows.
- **GulfTalent**: "you can filter candidates by over 20 different criteria – including
  education, experience, industry, location, nationality, age and salary expectation".
- **Naukrigulf**: "Filter accurately on nationality, location, experience & 24 other
  criteria".
- **Qureos**: its own pages claim search and filtering by nationality tied to
  Emiratisation planning.
- **AI ranking in these tools**: the pages I read (Talentera "SANAD AI Fit ranking",
  Qureos, Elevatus) do not say which candidate fields the ranking uses. So for the region
  the documented fact is that nationality reaches the recruiter as a filter. Whether it
  reaches the ranking model is not documented either way.
- For comparison, the UK regulator's audit of AI recruitment tools (ICO, November 2024,
  read through law-firm summaries) found that some tools let recruiters filter out
  candidates by protected characteristics and that some inferred gender and ethnicity from
  names. So such filters are not limited to the Gulf.

## 4. Verdict by pipeline type

| pipeline | does the line reach the scoring model? | how sure |
|---|---|---|
| Recruiter uses a chat model directly | Yes | certain by construction |
| Raw-text screener (sliday; no-code templates) | Yes | code read for sliday; listings only for templates |
| Extract-to-schema open-source pipeline (hiring-agent) | No, unless copied into the summary | code read; not run |
| Any pipeline with a default Presidio-style filter in front | No for 27 of our 28 nationalities, yes for one | tested on our CVs, one tool, one configuration |
| Pipeline with narrow redaction (name, contact, photo) | Yes | vendor pages |
| Western enterprise AI scoring (Greenhouse; Workday) | No | vendor statements; untested |
| Ashby, Textkernel Match | Unknown | not documented publicly |
| Regional portals and ATS | Reaches the recruiter as a filter; unknown for AI ranking | vendor pages |

## 5. What this means for our design

Observations and options. Choices are the team's, and the prompts have to be fixed before
the pilot.

- **The treatment is defensible as realistic**, with a stated scope: pipelines that give
  the model the CV text as written. For a study set in the Arab world this is easier to
  defend than in a US setting, because nationality is ordinary CV content there and
  platforms treat it as a legitimate search criterion.
- **The pseudonymisation sentence can stay.** Removing names and contact details while
  leaving nationality is what narrow anonymised screening does. If asked, the honest
  addition is that redaction designed against discrimination removes nationality too.
- **A sharper way to state the limitation:** in systems that score on extracted
  job-related fields, the nationality line never reaches the model, so our estimates do
  not apply to them. In the same systems nationality still exists as a structured field
  that a recruiter can filter on, which is outside what we measure.
- **The uneven redaction is worth a sentence.** A default filter removed 27 demonyms and
  missed one. Where such a filter is the only safeguard, protection would differ by
  nationality. This is a side observation from one tool, not a finding of the study.
- **Not for the course project (parked-list candidates):** a redaction arm (same CVs
  after a standard filter) as an alternative mitigation to the ignore paragraph, and a
  parse-then-score arm.

Likely Q&A question and a short answer: "Would a real system ever see the nationality?"
Yes when the CV text is passed as it is, which is how chat models and simple screeners
are used. No in systems such as Greenhouse that score on extracted skills and job
history. In the region itself nationality is a normal CV field and a recruiter filter on
the main job portals.

## 6. Sources and how far each was checked

Levels: **raw** = file or schema read directly; **test** = run locally; **page** =
official page read through a summarising fetch tool, quotes to be re-checked; **snip** =
search result snippet only. Keys in backticks are already in `literature_matrix.csv`.

| source | level | link |
|---|---|---|
| JSON Resume schema | raw | https://github.com/jsonresume/resume-schema |
| interviewstreet/hiring-agent: `transform.py`, `pdf.py`, `evaluator.py`, templates | raw | https://github.com/interviewstreet/hiring-agent |
| sliday/resume-job-matcher: `matcher/gate.ts`, `matcher/match.ts` | raw | https://github.com/sliday/resume-job-matcher |
| OpenResume types; pyresparser README | raw | https://github.com/xitanggg/open-resume , https://github.com/OmkarPathak/pyresparser |
| Microsoft Presidio, default recognisers, on our CVs | test | https://github.com/microsoft/presidio |
| Textkernel CV parsing data model | page | https://developer.textkernel.com/Parser/master/data_model/candidate-data-model/ |
| RChilli resume parser fields | page | https://docs.rchilli.com/kc/c_RChilli_resume_parser_fields |
| RChilli help article on ethnicity and nationality | snip | https://help.rchilli.com/hc/en-us/articles/900006275563-Are-you-parsing-ethnicity-in-a-resume |
| Affinda, data extracted | page | https://docs.affinda.com/resumes/data-extracted |
| Greenhouse, Anonymize resumes | page | https://support.greenhouse.io/hc/en-us/articles/19864880540827-Anonymize-resumes |
| Greenhouse, Talent Matching data processing FAQ | page | https://support.greenhouse.io/hc/en-us/articles/41131616864283-Talent-Matching-Data-Processing-FAQ |
| Workday, Responsible AI with HiredScore datasheet | snip | https://www.workday.com/content/dam/web/en-us/documents/datasheets/responsible-ai-with-hiredscore-datasheet-enus.pdf |
| Workday admin guide, candidate personal information by country | snip | https://doc.workday.com/admin-guide/en-us/human-capital-management/recruiting/candidates/candidate-personal-information/steps--change-personal-information.html |
| Ashby, AI-assisted application review (docs) and AI page | page / snip | https://docs.ashbyhq.com/ai-assisted-application-review , https://ashbyhq.com/ai |
| Workable anonymized screening | snip | https://resources.workable.com/backstage/workable-anonymized-screening |
| Teamtailor, anonymize candidate profiles | snip | https://support.teamtailor.com/en/articles/3790111-anonymize-candidate-profiles-to-reduce-unconscious-bias |
| Eightfold masking | snip | https://eightfold.ai/blog/ai-you-can-trust |
| Textkernel Match scoring | snip | https://developer.textkernel.com/SearchMatch/master/Matching/Scoring/ |
| Bayt employer guide (page returned 403; quote from search result) | snip | https://www.bayt.com/en/blog/3537/a-complete-guide-to-using-bayt-com-for-employers/ |
| Talentera help, CV search; Talentera AI platform page | page | https://lp.talentera.com/en/help/how-to-use-bayt-remote-cv-search , https://www.talentera.com/en/ai-recruitment-platform/ |
| GulfTalent CV search | snip | https://www.gulftalent.com/recruitment-solutions/free-cv-search |
| Naukrigulf employer CV search | snip | https://www.naukrigulf.com/employer-cv-search |
| Qureos | page / snip | https://www.qureos.com/ai-recruitment-platform-in-ksa |
| Gulf CV conventions (CV-advice sites, recruiter blogs) | snip | https://visualcv.com/international/saudi-arabia-cv , https://blog.loopcv.pro/gulf-cv-format/ |
| Europass template | snip | https://www.eba.europa.eu/sites/default/files/documents/10180/15977/d796e2b5-c3cf-4684-b68c-b168f254384e/CVTemplate_en_GB.doc |
| German pilot of anonymised applications: Bundestag summary; IZA Research Report 44 (`krause2012anonymous`) | snip | https://docs.iza.org/report_pdfs/iza_report_44.pdf |
| ICO, AI tools in recruitment, audit outcomes report (Nov 2024), via law-firm summaries | snip | https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2024/11/ico-intervention-into-ai-recruitment-tools-leads-to-better-data-protection-for-job-seekers |
| Privacy International, Humanless Resources? (9 July 2026): tests of Manatal and Talenteria; no finding on nationality or redaction | page | https://privacyinternational.org/long-read/5798/humanless-resources-uncovering-ai-recruitment-software |
| `chen2026beyond` (arXiv 2609.16501) | abstract | https://arxiv.org/abs/2609.16501 |
| `tan2026small` (arXiv 2603.05189) | abstract | https://arxiv.org/abs/2603.05189 |

## 7. Not covered

- What the regional AI rankers (Talentera, Qureos, Elevatus, ZenATS) actually feed their
  models. Only a vendor could answer, or a test account.
- Ashby's field-level redaction list (said to be in its Trust Center model cards).
- Oracle, SAP SuccessFactors, iCIMS, SmartRecruiters, LinkedIn.
- Other redaction tools (AWS Comprehend, Google Sensitive Data Protection, Azure): the
  entity lists I saw were cut off, with no nationality type visible in them.
- Running any pipeline end to end with a model. That would need model calls and the
  team's approval.
- Arabic-language sources and academic work on CV conventions in the region.
