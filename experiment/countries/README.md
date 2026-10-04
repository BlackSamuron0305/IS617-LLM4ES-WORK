# Countries

Slimmed on 2026-10-04. The documents in `research/old_design/` describe
the earlier tables (country codes, sub-regions, 8 base countries with cities, 11
comparison nationalities).

## `base_countries.csv`

The countries a job can be set in. One column, `country`. 22 rows: all Arab League
member states. Every job is run once in each of them: the country fills the `{country}`
placeholder in the main prompt, the job ad and the CV.

## `applicant_nationalities.csv`

The nationalities an applicant can have. 29 rows.

| column | meaning |
|---|---|
| `country` | country name; links to `base_countries.csv` |
| `demonym` | the word in the CV line, e.g. `Nationality: Jordanian` |
| `group` | `arab`, `benchmark`, `placebo` or `control` |
| `arab_identity_contested` | `true` for Comoros, Djibouti and Somalia. A flag only; these countries stay in every comparison |
| `note` | remarks |

| group | rows | which |
|---|---|---|
| `arab` | 22 | all Arab League member states (a political-institutional criterion, not an ethnic one) |
| `benchmark` | 2 | Germany (Western European), Türkiye (non-Arab Middle East, Muslim-majority) |
| `placebo` | 4 | Uruguay, Malawi, Maldives, Cambodia |
| `control` | 1 | `(not stated)`: the Nationality line is left out of the CV |

**What the placebo nationalities are for.** Any set of nationality labels will make a
model's scores spread a little. The placebo rows show how large that spread is for
countries unrelated to the Arab world, so the spread among the 22 Arab nationalities can
be compared with it.

**How the comparison set was reduced (2026-10-04, before any real data).** The earlier
set had 3 benchmarks and 8 placebo nationalities.

- Poland was dropped. It stood for "EU foreigner", which only made sense when the jobs
  were in Germany.
- Of the 8 placebo nationalities, which were 2 from each of 4 World Bank regions, one
  per region was kept, so that the 4 kept cover the 4 income groups and include one
  Muslim-majority country:

| kept | World Bank region | income group | dropped from the same region |
|---|---|---|---|
| Uruguay | Latin America & Caribbean | high | Bolivia |
| Malawi | Sub-Saharan Africa | low | Seychelles |
| Maldives (Muslim-majority) | South Asia | upper middle | Nepal |
| Cambodia | East Asia & Pacific | lower middle | Malaysia |

Regions and income groups are those in `country_covariates.csv` (World Bank,
retrieved 2026-09-30). With 4 instead of 8 placebo nationalities, the estimate of the
generic label spread is rougher.

## Notes on single nationalities

These labels carry associations that change over time, and a model may have learned
them differently depending on when its training data ends.

- **Palestine**: Arab League member; statehood is not recognised everywhere. Kept
  because "Palestinian" is a common self-description on real CVs.
- **Syria**: Arab League membership suspended 2011-2023, restored May 2023; treated as a
  member. The Assad government fell in December 2024.
- **Sudan**: war since April 2023.
- **Yemen**: no World Bank GDP value 2015-2022.
- Outputs refer to "Arab League member-state nationalities", not "Arab applicants".

## `country_covariates.csv`

World Bank data for the 28 countries in `applicant_nationalities.csv`: income per
person, income group and region, with source and retrieval date on every row. It is
downloaded data, not typed by hand. Not shown to the model; for analysis only. Yemen
has no income value for 2015-2022.
