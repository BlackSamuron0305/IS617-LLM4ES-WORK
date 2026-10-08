# Jobs

Rewritten on 2026-10-04: 20 jobs, one row per job. The documents in `research/old_design/` describe the earlier 6 jobs.

| file | what it is |
|---|---|
| `jobs.csv` | one row per job |
| `job_ad_template.txt` | the layout that turns one row into the job ad text the model reads |

## Columns of `jobs.csv`

| column | content |
|---|---|
| `occupation` | the job's id; the same id marks its CV in `experiment/cvs/applicant_cvs.csv` |
| `title`, `employer` | job title and the hiring company. Company names are invented and were not checked against real company registers |
| `location` | `{country}`: filled with one of the 22 countries in `experiment/countries/base_countries.csv` |
| `about` | one or two sentences about the company |
| `tasks`, `requirements`, `offer` | lists, items separated by ` \| `; each item becomes one bullet |
| `required_years` | years of experience the ad asks for |
| `skill_level` | `low`, `mid`, `mid-high` or `high`; for analysis only, not shown to the model |

No job ad names a city or a country. Every job is run once in each of the 22 base
countries by filling `{country}`.

## The 20 jobs

| skill level | jobs |
|---|---|
| low | sales associate, warehouse associate, customer service agent, hotel front desk agent, delivery driver, security guard, line cook |
| mid | administrative assistant, HR officer, electrician, IT support technician, procurement officer, graphic designer |
| mid-high | financial accountant, marketing specialist |
| high | software developer, management consultant, registered nurse, civil engineer, data analyst |

The first 6 (software developer, sales associate, warehouse associate, financial
accountant, management consultant, administrative assistant) are from the earlier
design; their texts are unchanged except that city mentions were removed. The other 14
were written on 2026-10-04.

Every ad requires English only (`Fluent English (C1 or higher)`).
