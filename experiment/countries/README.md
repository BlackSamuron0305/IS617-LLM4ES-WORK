# Countries

Rewritten on 2026-10-08 for the bank-onboarding design. The earlier tables (the 22
countries a job was set in, and a row without a nationality) are in
`research/old_design/hiring_2026-10-04/countries/`.

## `customer_nationalities.csv`

The nationalities a customer can have. 28 rows.

| column | meaning |
|---|---|
| `country` | country name; links to `country_covariates.csv` |
| `demonym` | the word in the file, e.g. `Nationality: Jordanian` |
| `group` | `arab`, `benchmark` or `placebo` |
| `arab_identity_contested` | `true` for Comoros, Djibouti and Somalia. A flag only; these countries stay in every comparison |
| `identity_document` | the line in the file: `<demonym> passport`, and `German identity card` for the German customer |
| `residence_status` | the line in the file: an unlimited settlement permit, and `German citizen` for the German customer |
| `eu_high_risk_list` | `yes` if the country is on the European Commission's list of high-risk third countries |
| `eu_list_since` | the date the country's entry took effect |
| `note` | remarks |

| group | rows | which |
|---|---|---|
| `arab` | 22 | all Arab League member states (a political-institutional criterion, not an ethnic one) |
| `benchmark` | 2 | Germany (the citizen), Türkiye (non-Arab Middle East, Muslim-majority, the usual comparison group in German studies) |
| `placebo` | 4 | Uruguay, Malawi, Maldives, Cambodia |

There is no row without a nationality. The field is mandatory in a bank's file.

**The EU high-risk list.** Read on the Commission's website on 2026-10-08: 26 countries,
last changed with effect from 29 January 2026. Four Arab League members are on it:
Algeria and Lebanon (since 5 August 2025), Syria and Yemen (since 23 September 2016). The
other eighteen, Türkiye and the four placebo countries are not. Germany is an EU member
and cannot be on a list of third countries. The same list is printed in the policy
(`../policy/bank_policy.txt`); if one is updated, update the other.

The lists of other bodies differ and change several times a year (FATF, Basel AML
Index). They are not in the table. If one is added for the analysis, fix the source and
the date before the first real run.

**What the placebo nationalities are for.** Any set of nationality labels will make a
model's ratings spread a little. The placebo rows show how large that spread is for
countries unrelated to the Arab world, so the spread among the 22 Arab League
nationalities can be compared with it. None of the four is on the EU list. The four cover
four World Bank regions and the four income groups, and include one Muslim-majority
country (chosen on 2026-10-04, before any data).

## Notes on single nationalities

These labels carry associations that change over time, and a model may have learned them
differently depending on when its training data ends.

- **Palestine**: Arab League member; statehood is not recognised everywhere. Kept
  because "Palestinian" is a common self-description. Whether a "Palestinian passport"
  line reads naturally to a model is untested.
- **Syria**: Arab League membership suspended 2011-2023, restored May 2023; treated as a
  member. The Assad government fell in December 2024. On the EU list since 2016.
- **Sudan**: war since April 2023. Not on the EU list; South Sudan is, and is a different
  country.
- **Yemen**: no World Bank GDP value 2015-2022.
- Outputs refer to "Arab League member-state nationalities", not "Arab customers".

## `country_covariates.csv`

World Bank data for the 28 countries: income per person, income group and region, with
source and retrieval date on every row. It is downloaded data, not typed by hand. Not
shown to the model; for analysis only. Unchanged since 2026-09-30.
