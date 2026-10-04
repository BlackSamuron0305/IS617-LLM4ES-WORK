# Prompts

Each file is one complete message, exactly as the model gets it. Restructured on
2026-10-04. The documents in `research/old_design/` describe the earlier prompts.

Every trial has two messages: the **main prompt** (who the model is and what its task
is), then one **follow-up message** with the job ad and the applicant(s) or employee(s).

## Layout

```
without_ignore_prompt/      main prompts as they are
  hiring/
  promotion/
with_ignore_prompt/         main prompts plus one paragraph: ignore nationality
  hiring/
  promotion/
```

Each of the four `hiring/` and `promotion/` folders holds:

| path | what it is |
|---|---|
| `main_prompt.txt` | the main prompt of this scenario |
| `experiment1_rate_one_applicant/` (hiring), `experiment1_rate_one_employee/` (promotion) | follow-up: one person. Answer: fit score 0-100 and interview yes/no (hiring) or promote yes/no (promotion) |
| `experiment2_choose_between_two_version1_A_B_or_lottery/` | follow-up: two people, one interview slot or one promotion. Answer: A, B or lottery |
| `experiment2_choose_between_two_version2_must_choose/` | follow-up: two people, one interview slot or one promotion. Answer: A or B |

- **Hiring**: the model screens applications for a job ad.
- **Promotion**: the model reviews employees of the company for an internal promotion to
  the position. It uses the same job text and the same CV as hiring; only the framing
  differs.
- **With / without ignore prompt** (experiment 3): everything is run once from each top
  folder and the two runs are compared.

`wording_1.txt`, `wording_2.txt` and `wording_3.txt` in a folder ask for the same thing
in three phrasings, so that a result does not depend on one phrasing.

## Placeholders

| placeholder | filled with | comes from |
|---|---|---|
| `{employer}` | the company of the job | `experiment/jobs/jobs.csv` |
| `{country}` | the country the job is set in | `experiment/countries/base_countries.csv` |
| `{job_ad}` | the job ad | `experiment/jobs/jobs.csv`, `experiment/jobs/job_ad_template.txt` |
| `{cv}` | the job's CV with one nationality line | `experiment/cvs/applicant_cvs.csv`, `experiment/cvs/cv_template.txt`, `experiment/countries/applicant_nationalities.csv` |
| `{cv_a}`, `{cv_b}` | the same CV twice, with two different nationalities and reference numbers (A is shown first) | same |

The nationality enters only through the CV line `Nationality: <demonym>`.

## Rules when editing

- The two top folders must differ **only** in the two `main_prompt.txt` files, and there
  only by the added paragraph. Every follow-up file is identical in both; a change to one
  is copied to the other.
- The two versions of experiment 2 must differ only in the choice sentence and in the
  allowed values of `"choice"`. The same wording number must stay identical otherwise.
- Fix the prompts before the pilot. Do not change them after seeing results.

## Open

- Whether the main prompt is sent as the system message, or as a first message that the
  model answers before it gets the follow-up.
- "in {country}" reads wrongly for one country ("in United Arab Emirates"). Whoever fills
  the placeholder has to add "the" there.
- Which pairs of nationalities experiment 2 uses. Every pair on every job in every
  country is far too many.
