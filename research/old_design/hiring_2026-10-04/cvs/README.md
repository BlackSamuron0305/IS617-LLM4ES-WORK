# CVs

Rewritten on 2026-10-04: 20 CVs, **one per job**. The documents in `research/old_design/` describe the earlier set (48 CVs: 8 per job in three
qualification levels, each set in one of 8 countries with cities and named schools).

| file | what it is |
|---|---|
| `applicant_cvs.csv` | one row per CV. No nationality and no country: both are filled in when the prompt is built |
| `cv_template.txt` | the layout that turns one row into the CV text the model reads |

## How a CV reaches the model

1. Take the row of `applicant_cvs.csv` whose `occupation` matches the job.
2. Fill it into `cv_template.txt`.
3. Replace `{country}` with the country the job is set in
   (`experiment/countries/base_countries.csv`).
4. Insert the line `Nationality: <demonym>` with one row of
   `experiment/countries/applicant_nationalities.csv` (no line for `(not stated)`).

Every version of a CV is therefore identical except for the country and that one line.

**Choosing between two.** Both candidates get the **same CV**: same education, same
experience, same skills and certificates. They differ only in the nationality line and
in the reference number (`applicant_reference` for one, `applicant_reference_b` for the
other).

## Columns of `applicant_cvs.csv`

| columns | content |
|---|---|
| `occupation` | which job in `experiment/jobs/jobs.csv` the CV applies to |
| `applicant_reference`, `applicant_reference_b` | shown instead of a name; the second one is for candidate B |
| `location`, `work_authorization`, `driving_licence`, `availability`, `languages` | the personal-details block. `location` is `{country}` |
| `profile`, `achievement1`, `achievement2` | summary and key achievements |
| `exp1_*`, `exp2_*` | the two jobs held: title, employer, start, end, bullets |
| `edu1_*`, `edu2_*` | education: degree, institution, start, end |
| `skills`, `cert1_*`, `cert2_*` | skills and certificates |

Rendered lines: `start - end | title | employer` followed by one bullet per item;
`start - end | degree | institution`; skills joined by commas; `None listed` when there
is no certificate.

## How the CVs are written

- **Middle level.** Each CV meets its job's requirements but is not outstanding, so
  scores have room to move up or down. Experience is somewhat above the minimum the ad
  asks for.
- **No names of places, schools or companies.** Employers are described, not named
  (`Food distribution company`). Schools are `University ({country})` or
  `College ({country})`. This keeps the CV the same in every country, and it lets the same
  CV serve as an applicant's CV (hiring) and as an employee profile (promotion).
- **Dates** run up to 06/2024; the current job ends with `present`.
- The first 6 CVs are the first middle-level CV of each job in the earlier design, with
  cities, school names and invented company names replaced as above. The other 14 were
  written on 2026-10-04.
