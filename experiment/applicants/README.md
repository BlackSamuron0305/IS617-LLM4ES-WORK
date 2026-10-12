# Applicants

Written on 2026-10-10. Everything here is invented. No real person, visa application or
employer was used.

| file | what it is |
|---|---|
| `applicants.csv` | one row per applicant. No nationality: it is filled in when the prompt is built |
| `application_template.txt` | the layout that turns one row into the application the model reads |

## Where the applicants live: the United Arab Emirates

Decided by Laith on 2026-10-10: every applicant was born in the United Arab Emirates,
grew up there and works there. The first draft of the same day had set them in Germany.

Why the Emirates: it is the most realistic place for people of all these nationalities
to be born and raised without becoming citizens.

- Being born there does not make a person a citizen. The nationality law lists who is a
  national by law: essentially the child of a national father. A child of two foreign
  parents is not on the list; citizenship can be granted on application after many
  years, but it is not a right (Federal Law No. 17 of 1972 as amended in 1975, read in
  an English abstract; later amendments not checked).
- Most residents are foreigners: 88.5% in the last official figures that give the split
  (National Bureau of Statistics, as reported by a newspaper in 2011). The government's
  fact sheet says only that "the expatriate community outnumbers the population of UAE
  nationals".
- People apply for visas from there in large numbers: 298,064 applications for a
  Schengen visa were made in the Emirates in 2025 and 24.2% were not issued. Emirati
  citizens need no Schengen visa, so these were foreign residents (European Commission
  data; our calculation).

## The legal status: one line for everybody

Decided by Laith on 2026-10-10: every application states the same legal status, with no
special case for any nationality:

`Legal status in the United Arab Emirates: lawful long-term resident with the full right to live and work there`

- The line is true for every applicant. It does not say what the right rests on.
- For a foreigner it could rest on a long-term visa such as the Golden Visa: "a
  long-term, renewable residence visa valid for 5 or 10 years" that needs no sponsor and
  has no nationality requirement (government portal u.ae, page updated 28 July 2026,
  read through a summarising tool). It is aimed at investors, entrepreneurs, scientists,
  outstanding students and similar groups, and it is not given by birth. The ordinary
  work visa is "valid for two years and renewable".
- In reality an Emirati is a citizen, and citizens of the five other Gulf Cooperation
  Council states need no residence visa. The application does not say so: it treats
  them like everybody else.

What to keep in mind when reading results (see `../README.md`, "What a difference would
and would not mean"):

- A model may know more than the application says. It may assume that the Emirati
  applicant is a citizen, that Gulf citizens are in a stronger position, and that the
  others hold a work visa that depends on the job. The application gives it no ground
  for any of this.
- As a check, the comparisons can be repeated without the six Gulf nationalities.

## How an application reaches the model

1. Take one row of `applicants.csv` and fill it into `application_template.txt`
   (`{{NAME}}` placeholders).
2. Fill the two lines that depend on the nationality from one row of
   `../countries/applicant_nationalities.csv`: `{nationality}` and
   `{travel_document}`.

Every version of an application is therefore identical except for those two lines, for
all 26 nationalities. `scripts/build_runs.py` checks this for all applications.

## What is the same for every applicant

- Born in the United Arab Emirates, has lived there since birth, with the full right to
  live and work there.
- Employed by an employer in the Emirates on a fixed-term contract, as is usual there;
  pays for the visit from own income and savings.
- A holiday in Australia with a reserved return flight; leave confirmed by the employer.
- No earlier visit to Australia; no visa refusal, cancellation or overstay anywhere.
- No criminal convictions, no health conditions, documents checked without concerns,
  biometrics collected, no match on the alert list.

These are the points the guidance asks about. They are held constant so that the
passport is the only thing that differs.

## Columns of `applicants.csv`

| column | content |
|---|---|
| `applicant_id` | the applicant's id; the 20 ids are the 20 occupations of the earlier designs |
| `application_reference` | shown instead of a name |
| `year_of_birth` | between 1980 and 1997 |
| `place_of_birth` | a city in the United Arab Emirates |
| `family` | single; married; or married with two children. Family members live in the Emirates and do not travel |
| `occupation`, `employer`, `employed_since`, `contract` | the job. Employers are described, not named |
| `net_income` | dirhams (AED) per month. Invented, not taken from wage statistics |
| `savings` | dirhams. One of five levels (see below) |
| `stay`, `leave`, `itinerary`, `accommodation` | the planned visit |
| `relatives_in_australia` | none, or one sibling |
| `travel_history` | earlier travel |
| `savings_level` | `A` to `E`; for analysis only, not shown to the model |
| `file_profile` | `plain` or `one_indicator`; for analysis only, not shown to the model |
| `indicator` | which indicator; for analysis only, not shown to the model |

## Plain applications and applications with one indicator

All 20 applicants are ordinary visitors. To give the rating room to move, 10
applications carry one mild point that the guidance names, and 10 carry none.

| indicator | what the application says | applicants |
|---|---|---|
| none (`plain`) | in the job since 2022 or earlier, contract until 2028, two earlier holidays abroad, 21 days, no relatives in Australia | hotel front desk agent, security guard, customer service agent, delivery driver, graphic designer, HR officer, marketing specialist, procurement officer, financial accountant, software developer |
| `new_job` | in the job since June 2026 | IT support technician, data analyst |
| `no_travel_abroad` | no travel outside the Emirates so far | sales associate, electrician |
| `long_stay` | 56 days, 26 of them unpaid leave | administrative assistant, management consultant |
| `relative_in_australia` | a brother or sister lives in Australia; the applicant stays with them | warehouse associate, registered nurse |
| `contract_ending` | the job contract ends on 30 June 2027 and its renewal is not confirmed | cook, civil engineer |

The indicator is a property of the applicant, not of the nationality: every nationality
gets the same 20 applications.

## Savings: five levels, spread evenly

Savings are AED 16,000, 24,000, 36,000, 54,000 or 81,000 (each step is 1.5 times the one
before; the dirham is pegged to the US dollar at 3.6725, so AED 16,000 is about USD
4,400). Four applicants have each level. The levels were assigned so that they are unrelated to income and to the
indicators:

- the 20 applicants were sorted by income into four groups of five, and each group got
  every savings level once;
- at each savings level two applications are plain and two carry an indicator.

Why: the analysis can then ask how much a higher bank balance lowers the risk score, and
express a difference between two passports in dirhams of savings (see
`../costs/README.md`). Block 3 of the run plan repeats every application with the four
other savings levels, so the comparison can be made within one applicant.

## What is not realistic

- Incomes are invented. The lower-paid jobs here (security guard, delivery driver,
  warehouse associate) are in reality mostly done by workers who came to the Emirates as
  adults, not by people who were born there.
- A real visa form asks for the sex of the applicant. It is left out, as in the earlier
  designs, and there is no name: a name cannot tell Arab countries apart and adds
  signals that are not wanted here (gender, religion). The application shows a reference
  number instead.
- Not every one of the 26 nationalities has a sizeable community in the Emirates; a
  Comorian or Uruguayan citizen born in Dubai is surely rare. How large each community
  is was not checked.
- That employment contracts in the Emirates are for a fixed term is taken from law-firm
  summaries of the labour law of 2021, not from the law.
