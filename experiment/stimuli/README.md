# Stimuli

Two tables and one template are the complete CV material. Every prompt
combines **one CV row with one nationality row** when the prompt is built, so the
nationality clones of a CV are identical by construction: the only thing that
changes is the `Nationality:` line. The job ads and the base countries are two
more small tables; the building blocks were used once to build `applicant_cvs.csv`.

| file | contents |
|---|---|
| `applicant_cvs.csv` | one row per base CV (48 rows); no nationality column |
| `applicant_nationalities.csv` | one row per nationality condition (34 rows) |
| `cv_template.txt` | the single plain-text CV template |
| `jobs.csv` | one row per occupation and its job ad (6 rows) |
| `base_countries.csv` | one row per base country a CV and its job ad are set in (8 rows) |
| `building_blocks/` | the curated CV components (11 tables) that `scripts/build_cv_table.py` composed into `applicant_cvs.csv`; `institutions.csv` is also the validator's whitelist |

All tables are UTF-8 CSV (conventions: `../DATA_FORMAT.md`) and open in Excel or
any IDE. After editing any of them, run `python -m hiringaudit validate-stimuli`;
it must pass before any run. A run records the SHA-256 of `applicant_cvs.csv`,
`applicant_nationalities.csv`, the template, `jobs.csv` and the prompt tables, and refuses
to resume if any of them changed. How the job ad and a CV enter a prompt:
`../prompts/README.md`.

## Setting: every CV is set in one Arab League country

User request 2026-10-01: each CV is set entirely in ONE base country
(`base_country`, ISO3; `base_city`): its `Location:` line, every employer city
and its educational institution are in that country, and the job ad it is shown
with is located in its base city (`jobs.csv`: `location` = `{city}, {country}`;
the ads of one occupation are otherwise identical). Nothing in a CV,
job ad or prompt is German (no German cities, institutions, credentials, legal
forms, HGB or euro; the validator scans for them). Employers are invented,
country-neutral English names without a legal suffix; institutions are real
universities and colleges of the base country (`building_blocks/institutions.csv`;
with `base_countries.csv` both the builder input and the validator whitelist).

| base country (base city) | other employer cities |
|---|---|
| ARE United Arab Emirates (Dubai) | Abu Dhabi, Sharjah |
| SAU Saudi Arabia (Riyadh) | Jeddah, Dammam |
| QAT Qatar (Doha) | Al Rayyan, Al Wakrah |
| KWT Kuwait (Kuwait City) | Hawalli, Al Ahmadi |
| OMN Oman (Muscat) | Sohar, Nizwa |
| BHR Bahrain (Manama) | Muharraq, Riffa |
| JOR Jordan (Amman) | Irbid, Zarqa |
| EGY Egypt (Cairo) | Giza, Alexandria |

The most recent job is always in the base city. The three lines that depend on
the base country are derived in `src/hiringaudit/stimuli/setting.py` and are
constant across the nationality clones of a CV:

    Location: <base city>, <country>
    Work authorization: Authorized to work in <the country>; no visa sponsorship required
    Driving licence: Valid driving licence issued in <the country>

**Allocation.** Base countries are assigned per forced-choice pair: positions
(01, 04) strong, (02, 05) adequate, (03, 06) borderline, (07, 08) adequate of each
occupation share one base country (`fc_pair` and `base_country` in
`building_blocks/cv_slots.csv`). 24 pairs over 8 countries = 3 pairs (6 CVs) per country,
each in a different occupation. Pilot pairs (pilot occupations, positions 01-06)
are marked *; the pilot covers every country once and ARE twice.

| base country | strong | adequate | borderline |
|---|---|---|---|
| ARE | software_developer* | financial_accountant | warehouse_associate* |
| SAU | financial_accountant | software_developer* | management_consultant |
| QAT | - | retail_sales_associate, management_consultant | software_developer* |
| KWT | warehouse_associate* | financial_accountant | administrative_assistant |
| OMN | retail_sales_associate* | software_developer, administrative_assistant | - |
| BHR | administrative_assistant | retail_sales_associate*, warehouse_associate | - |
| JOR | management_consultant | administrative_assistant | retail_sales_associate* |
| EGY | - | warehouse_associate*, management_consultant | financial_accountant |

Counts per country x tier (pairs): ARE, SAU, KWT, JOR 1/1/1; OMN, BHR 1/2/0;
QAT, EGY 0/2/1 (strong/adequate/borderline).

**Forced choice** pairs two CVs of the same occupation, the same tier AND the same
base country (the job ad is located there); in the main set the adequate cell of
an occupation therefore has 2 CV pairs (02/05 and 07/08), the other cells 1.

**host_national** = (nationality code == the CV's base country). It is written
to every raw record (`base_country`, `host_national` aligned with
`nationalities`) and to the processed tables (evaluations: `base_country`,
`host_national`; forced choice: `base_country`, `host_national_a`,
`host_national_b`). Benchmark (DEU, POL, TUR), placebo and NONE codes are never
host nationals, because every base country is an Arab League member state.

## How a clone is rendered

prompt = job ad (localized to the CV's base city) + render(CV row, nationality
row, clone type), with `cv_template.txt`:

- **counterfactual**: `Nationality: <demonym>` at a fixed position (between
  `Location:` and `Work authorization:`);
- **NONE** (control): the whole `Nationality:` line is omitted, nothing else
  changes;
- **positive control**: the NONE clone with the rendered lines of the education
  entries named in `positive_control_education` removed: EVERY qualification that
  satisfies the job ad's designated must-have (for a master's, both the master's
  and the preceding bachelor's), so
  only the school-leaving line remains in EDUCATION. The validator checks that
  no qualification cue is left anywhere in the positive control (no
  degree-formatted line, no diploma / degree / bachelor / master / MBA / graduate
  / qualified / university / college ... wording). Stimulus id
  `<cv_id>__NONE__pc`.

Stimulus ids are `<cv_id>__<code>`. Every rendered prompt is stored once in
`data/raw/<run_id>/prompts.jsonl` (keyed by its SHA-256), and every record names
its `stimulus_ids`.

## `applicant_cvs.csv`

| column(s) | meaning |
|---|---|
| `cv_id`, `occupation`, `qualification_tier`, `pilot` | identity; tiers strong / adequate / borderline; `pilot` = in the pilot subset |
| `applicant_reference` | `APP-dddd`; replaces the name, never encodes a nationality |
| `reference_date` | the month that "present" means (2024-06); nothing is dated later |
| `relevant_experience_months`, `total_experience_months` | must equal what the job dates imply (checked) |
| `positive_control_education` | the education entries whose rendered lines the positive control removes, e.g. `edu1 \| edu2` (every entry with an institution, in table order) |
| `base_country`, `base_city` | the country (ISO3, an Arab League row of `applicant_nationalities.csv`) and city the CV is set in; the job ad is located there |
| `location`, `work_authorization`, `driving_licence` | derived from the base country (checked against `experiment/stimuli/setting.py`); constant across the clones of a CV |
| `availability`, `languages` | design constants: identical in every row (checked); `languages` is English only |
| `profile` | the profile (2-3 sentences; the first states the relevant experience) |
| `achievement<i>` | key achievements (strong 3, adequate 2, borderline 2), from the occupation's pool for the tier |
| `exp<i>_title`, `_employer`, `_city`, `_start`, `_end`, `_relevant`, `_bullets` | jobs, most recent first (`exp1`); dates `MM/YYYY` or `present`; `_relevant` = counts as relevant experience (not rendered); bullets separated by ` \| ` |
| `edu<i>_degree`, `_institution`, `_start`, `_end` | education, most recent first, without gaps: the qualification (`edu1`; for a master's, `edu2` is the preceding bachelor's, 4 years, same base country), then the "Secondary school certificate" (no institution, no start). Strong software developers, accountants and consultants hold a master's; strong retail, warehouse and administrative CVs an advanced diploma that starts straight after school |
| `skills` | skills separated by ` \| ` (strong 12, adequate 10, borderline 8, incl. tools/software) |
| `cert<i>_name`, `cert<i>_year` | certificates (at most 3) |

Empty cells mean "no such entry". Jobs: strong CVs have four roles (junior, two
mid-level, senior; 3/3/4/5 bullets, oldest first), adequate CVs two (3/4),
borderline CVs an unrelated earlier role (3 bullets) and a junior role (3). CV
length is fixed within a tier. Rules the validator enforces:

- the base country is a row of `base_countries.csv`, `base_city` is
  its base city, and the Location, work-authorization and driving-licence lines
  are the derived ones;
- every employer city and every institution is on the base country's whitelist;
- every CV has exactly one same-occupation, same-tier partner with the same base
  country (its forced-choice pair), with the same pilot status;
- English is the only language;
- no demonym, no other country or city name, no citizenship, religious,
  foreign-language or German term appears anywhere in a CV (only the CV's own
  base country and its cities may appear);
- tiers are ordered by relevant experience within each occupation, and a
  borderline CV has less total experience than every adequate one;
- each job's bullets and employer come from the building blocks for its title,
  and the key achievements from those for the CV's tier (`building_blocks/`).

**How the table was built.** `python scripts/build_cv_table.py --force`
(2026-10-01) composed the 48 CVs from `building_blocks/`, `jobs.csv` and
`base_countries.csv` with a fixed seed. The table is the source of truth from
then on: edit it directly (the builder refuses to overwrite it without
`--force`). The experiment runtime never reads the building blocks. The builder
reproduces `applicant_cvs.csv` byte for byte (a test checks this); on 2026-10-01 the
column `positive_control_lines` (rendered lines joined by ` || `) was replaced by
`positive_control_education` (entry names joined by ` | `), with identical
rendered clones.

## `jobs.csv`

One row per occupation (factor J; contract v0.2, A12/A7). Columns: `occupation`
(the id used in `applicant_cvs.csv` and `config/runs.csv`), `pilot` (in the pilot subset),
`title`, `employer`, `location` (always `{city}, {country}`: filled with the
CV's base city), `about`, `tasks`, `requirements`, `offer` (lists),
`positive_control_requirement`, `required_years`, and the descriptive moderator
codes `skill_level`, `customer_contact`, `trust_role`, `fit_emphasis` (with six
occupations these are descriptive only). The rendered ad lists Position,
Employer, Location, "About us", "Your tasks", "Your profile" (requirements) and
"What we offer".

- All employers are invented, country-neutral English names without a legal
  suffix (neither Arabic- nor German-sounding, implausible as real firms). Check
  each name against company registers before publication.
- The only language requirement is "Fluent English (C1 or higher)"; every CV
  lists English (C1), so any language concern a model raises is unsupported by
  the record. No diversity statements, no demographic language, no mention of
  nationality, visas or relocation (deliberately no "(m/f/d)" either).
- `required_years` is the experience minimum the tiers were built against (at
  least 2 so that a borderline CV can be 12-18 months short without zero relevant
  experience); it must match the "At least N years" requirement (checked).
- `positive_control_requirement` (A7) names the ONE must-have whose lines the
  positive control removes (every qualification line that satisfies it); it
  names degrees or diplomas only, so no certificate or course left in the CV
  satisfies it. It must be one of the `requirements` (checked).

## `base_countries.csv`

One row per base country: `code` (ISO3; an Arab League row of
`applicant_nationalities.csv`), `name` (must equal its country name there), `article`
(`the` for "the United Arab Emirates", else empty), `aliases` (other forms that
may appear, e.g. `UAE` in "UAE University"), `base_city` (the Location line and
the job ad), `cities` (every city an employer may be in, including the base
city). Their institutions are in `building_blocks/institutions.csv`
(`base_country`, `institution_kind` = computing / business / engineering /
college, `institution`): real universities and colleges, listed only where a CV
of that country needs that kind of programme; none contains a demonym or other
origin cue (the leak scan enforces this). Verify programme offerings before
publication.

## `building_blocks/`

The input of `scripts/build_cv_table.py` (one entity per row; row order matters,
because the builder draws from every list in table order with a fixed seed):

| file | one row per |
|---|---|
| `build_settings.csv` | build setting: seed, reference date, the design constants `availability` and `languages`, the school-leaving line |
| `cv_slots.csv` | base CV: `cv_id`, `occupation`, `position`, `qualification_tier`, `pilot`, `fc_pair` (the same-tier pair that shares a base country), `base_country` |
| `roles.csv` | job title: `kind` = junior / mid / senior (titles of the occupation) or unrelated (with `profile_phrase` and its own `employers`) |
| `bullets.csv` | bullet: `bullet_set` = core (every title of the occupation), senior (senior titles in addition) or the title of an unrelated role |
| `employers.csv` | employer of the occupation's own titles |
| `achievements.csv`, `profiles.csv` | key achievement / profile template (`{experience}`, `{unrelated}`) per tier |
| `skills.csv` | skill: `kind` = required (every CV), nice (preferred: strong 4-5, adequate 1-2), tools (neutral fillers) |
| `qualifications.csv` | degree: `level` = advanced (strong CVs) or relevant, `years`, `institution_kind`, `preceding_bachelor` (a master's) |
| `certifications.csv` | certificate: `kind` = required / optional, `since` (not dated before) |
| `institutions.csv` | institution of a base country (see above) |

Rubric (relative to the job ad's minimum, "req"): **strong** = all must-haves
clearly met, relevant experience >= req + 36 months, four roles (junior, two
mid-level, senior), all required plus 4-5 preferred skills, advanced
qualification, 3 certificates, 3 achievements; **adequate** = all must-haves met,
req + 1..20 months, no unrelated job, two roles, 1-2 preferred skills, relevant
qualification, 1 optional certificate, 2 achievements; **borderline** = clearly
misses ONE must-have: 12-18 months BELOW req (never zero), a junior final role
after one genuinely unrelated role short enough that total experience stays below
req (hence below every adequate CV), no preferred skill, no optional
certificate, 2 achievements. Length is fixed within a tier (bullets per role
strong 3/3/4/5, adequate 3/4, borderline 3 + 3; skills 12 / 10 / 8). EDUCATION
lists the qualification and then the school-leaving line without gaps; a
master's is preceded by its bachelor's in the same base country. No other part of
a CV may name a qualification (checked on the positive control).

## `applicant_nationalities.csv`

Columns: `code`, `country`, `demonym`, `group` (arab / benchmark / placebo /
control), `subregion`, `arab_league_joined`, `arab_identity_contested`, `note`.
**DEU (German) is the reference condition.** The NONE row has no country and no
demonym.

Notes moved here from the former `config/nationalities.yaml`:

- **Inclusion rule for the primary set:** the 22 Arab League member states (same
  membership as the World Bank "Arab World" aggregate). Membership is a
  political-institutional criterion, not an ethnic one. Three members whose Arab
  identity is contested (COM, DJI, SOM) are flagged `arab_identity_contested` for a
  pre-registered sensitivity analysis (see `research/design_decisions.md`).
- **Sub-regions** are fixed before data collection and are used only for
  hierarchical modelling, never to choose contrasts after seeing results.
- **Benchmarks:** DEU (reference), POL (EU foreign, non-MENA), TUR (non-Arab MENA,
  Muslim-majority). **Control:** NONE, the line is omitted.
- **Placebo nationality signals** (adversarial review H5; secondary). Purpose: a
  reference for how much ANY comparably diverse set of nationality labels spreads
  a model's scores, so that within-Arab spread (sigma_A) can be compared with
  generic label spread (sigma_placebo). Baseline independent evaluation only; never
  in forced choice; never in confirmatory Arab tests. Pre-specified selection rule
  (2026-09-30, before any real data): 8 nationalities outside the Arab League,
  MENA, Europe and the benchmark set; 2 from each of 4 World Bank regions (Latin
  America & Caribbean, Sub-Saharan Africa, South Asia, East Asia & Pacific); income
  spread chosen to approximate the Arab set's (Arab: 6 H / 4 UM / 8 LM / 4 L;
  placebo: 2 H / 2 UM / 3 LM / 1 L); includes rare demonyms (Seychellois,
  Maldivian, Malawian) and two Muslim-majority states (MDV, MYS) so that neither
  token rarity nor religion is unique to the Arab set. Income groups and regions
  were verified against the World Bank country API on 2026-09-30.
- **Syria's** membership was suspended 2011-2023 and restored in May 2023; it is
  treated as a member. Arab League accession years are for documentation only and
  must be verified before they appear in the paper.
- **Interpretation notes** (CR-20; no design change). These signals carry
  distinctive, time-varying associations that a model's training data may encode
  differently depending on its data cutoff:
  - PSE: Palestine is an Arab League member, but its statehood is not recognised
    everywhere. (In the former German setting this mattered because Germany does not
    recognise Palestine as a state and German records often list Palestinians as
    "ungeklärt"/stateless [VERIFY]; the note in `applicant_nationalities.csv` still says so.) In
    the Arab-world setting the label may evoke base-country-specific statuses, e.g.
    Palestinian refugees, or Jordanians of Palestinian origin in a CV set in Amman
    [VERIFY]. "Palestinian" is kept because it is a common self-description on real CVs.
  - SYR: the Assad government fell in December 2024; models trained before and
    after may associate "Syrian" with different contexts (civil war, refugee
    arrivals 2015-16, post-2024 transition).
  - SDN: war since April 2023.
  - YEM: no World Bank GDP value 2015-2022, so it is excluded from the
    income-gradient hypothesis H1d (see `config/country_covariates.csv`).
- Outputs refer to "Arab League member-state nationalities", not "Arab
  applicants" (CR-19).
