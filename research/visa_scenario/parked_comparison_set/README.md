# Parked: comparison passports picked by passport strength

Not part of the experiment. An earlier draft of 2026-10-10 (by Claude) compared the 22
Arab League nationalities with 22 non-Arab passports of similar strength and with five
non-Arab Muslim-majority passports. Laith removed this the same day: the project is
about bias among Arabs, measured against the official rules, and it does not look at
how strong a passport is.

| file | what it is |
|---|---|
| `world_reference.csv` | 199 countries: Australian visa route, passport strength (Henley Passport Index, 10 October 2026), Australian grant rates 2019-20, US refusal rates 2025, Muslim share (Pew, 2020), World Bank income data |
| `select_comparison_countries.py` | the rule that picked the comparison countries. It expects the two tables in `experiment/countries/` and no longer runs from here |

Kept only in case the question "Arab League passports against others" is taken up
later. The figures for the 26 nationalities of the experiment are in
`experiment/countries/official_rules.csv`.
