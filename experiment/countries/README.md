# Countries

Rewritten on 2026-10-10 for the visitor-visa design. The tables of the bank design are
in `research/old_design/bank_2026-10-08/countries/`.

| file | what it is |
|---|---|
| `applicant_nationalities.csv` | the 26 nationalities an applicant can have: the 22 Arab League nationalities and 4 unrelated ones |
| `official_rules.csv` | what the official Australian rules say about each of the 26, and, for context, how real applicants of each nationality fared |

## The yardstick: the official rules are the same for all 22

The project asks about bias among the 22 Arab League nationalities. The yardstick is
what the official rules of the destination say about them, not how strong a passport is
or how a country is seen. `official_rules.csv` has one row per nationality:

| column | what it says | the same for all 26? | source, read on 2026-10-10 |
|---|---|---|---|
| `visa_needed` | Visitor visa (subclass 600) | yes | the department's lists for the two electronic permits, read in full: no Arab League country is on either |
| `electronic_travel_authority_601`, `evisitor_651` | whether the simpler electronic permits are open to this passport | yes: no | same; and not one such permit was granted to any of the 22 in 2024-25 or 2025-26 (grant data on data.gov.au) |
| `application_form` | form 1419, online | yes | Migration instrument LIN 21/056: applications "must be made using form 1419 (Internet) through ImmiAccount" |
| `fee_aud` | 250 | yes | Migration Regulations, Schedule 1, item 1236, compilation of 1 July 2026 |
| `legal_test` | genuine intention to stay temporarily, adequate means, health and character | yes | Migration Regulations, Schedule 2, clauses 600.211 to 600.213 |
| `on_a_risk_list_in_force` | whether the nationality is in a group that has to show "very little likelihood" of overstaying | yes: no | the law allows such a list (public interest criterion 4011); none was found in force. The search was not exhaustive |
| `on_the_risk_list_revoked_in_2009` | whether the nationality was on the last such list | **no, it differs** | the list of 2008 (IMMI 08/033) had Egyptian, Iraqi, Jordanian, Lebanese and Syrian groups by sex and age, and Cambodian and Uruguayan ones. It was revoked on 15 May 2009. History, not a rule in force |
| `entry_ban_or_travel_suspension_2026_10_10` | whether holders of this passport are barred | yes: no | none found for any of the 26. See the warning below |

`scripts/build_runs.py` checks that every column of rules in force has one value for all
26 rows.

Three more columns start with `real_`. They are **not rules**. They show how real
applicants fared, and they are in the table for context and for the slides:

| column | content | source |
|---|---|---|
| `real_au_600_granted_2019_20`, `real_au_600_refused_2019_20`, `real_au_600_grant_rate_2019_20` | Australian visitor visas (subclass 600, all streams) granted and refused by citizenship, July 2019 to June 2020; rate = granted / (granted + refused), our calculation | Department of Home Affairs, freedom of information release FA 20/10/00106. Counts below 5 are hidden; then there is no rate (Comoros, Djibouti, Mauritania). Nothing newer by nationality is published |
| `real_us_b_visa_refusal_fy2025` | share of US visitor visa applications refused, by nationality, October 2024 to September 2025 | US Department of State, adjusted refusal rate, B visas |

These figures come from real applicants in very different circumstances, most of whom
live in the country of their passport. They show that the 22 fare very differently in
practice although the Australian rules are the same for all of them. They do not show
what an office does with identical applications.

**Warning: check the rules again before the pitch and before the runs.** Since March
2026 the Australian minister can stop holders of a visa from travelling, by class of
persons, for a limited time (according to law-firm summaries; the Act was not read). It
was used once, for holders of this visa with an Iranian passport (26 March to 25
September 2026; the instrument was read). A new one that names an Arab League
nationality would be a rule, and the yardstick would no longer be the same for all 22.

**What the published instruction adds.** The department's instruction for officers
(version of 2016, released in 2018) says a profile "is not grounds to refuse to grant a
visa" and that "all applications must be considered on their own merits". It lets
officers ask for more evidence if statistics show that nationals of the applicant's home
country overstay more often, and it defines the home country as the country of usual
residence, which is the United Arab Emirates for every applicant here. Details and
quotes: `../policy/README.md`.

## Three wealth groups: rich, normal, poor

The second question of the project is whether the models sort the 22 countries into
three groups: rich, normal and poor (Laith, 2026-10-10). The groups are fixed before any
run. They follow the World Bank's income classification, retrieved from the World Bank
API on 10 October 2026:

| group | World Bank class | countries |
|---|---|---|
| rich | high income | Bahrain, Kuwait, Oman, Qatar, Saudi Arabia, United Arab Emirates (6) |
| normal | middle income (upper and lower) | Algeria, Comoros, Djibouti, Egypt, Iraq, Jordan, Lebanon, Libya, Mauritania, Morocco, Palestine, Tunisia (12) |
| poor | low income | Somalia, Sudan, Syria, Yemen (4) |

- "Normal" joins the World Bank's upper middle income (Algeria, Iraq, Jordan, Libya)
  and lower middle income (the other eight). The World Bank itself calls the two
  together "middle income".
- The rich group is exactly the six Gulf states. See "Legal status" below: for these
  six the application simplifies reality most, so "rich" cannot be told apart from "Gulf
  citizen in the Emirates".
- The four poor countries are all at war or just out of one. "Poor" and "at war" cannot
  be told apart either.
- The World Bank updates the classification every year, and countries move between
  classes. State the date with the groups.
- The four placebo nationalities have a group too (Uruguay rich, Maldives and Cambodia
  normal, Malawi poor). The question is about the 22; the placebo rows only show whether
  a pattern is special to the Arab League countries.

## Why Australia is the destination

The yardstick only works where the rules are the same for all 22. Tested on 2026-10-10
(`research/visa_scenario/destination_and_requirements.md`, section 2):

| destination | same rules for all 22? | where the rules differ |
|---|---|---|
| **Australia** | **yes** | nowhere |
| Canada | no | Emirati and Qatari citizens travel on an electronic permit |
| United Kingdom, New Zealand | no | the six Gulf states travel on an electronic permit or without a visa |
| Schengen area, Ireland | no | Emirati citizens need no visa |
| United States | no | entry suspended by proclamation for Libyan, Somali, Sudanese, Syrian and Yemeni citizens and holders of Palestinian Authority documents; visitor visas suspended for Mauritanian citizens |
| Japan, South Korea | no | several Arab League nationalities need no visa (Wikipedia only) |

Where the rules differ, a different answer for two nationalities follows from a rule and
is not a bias.

## `applicant_nationalities.csv`

| column | meaning |
|---|---|
| `country` | country name; links to `official_rules.csv` |
| `iso2` | two-letter country code |
| `demonym` | the word in the application, e.g. `Nationality: Jordanian` |
| `group` | `arab` or `placebo` |
| `wealth_group` | `rich`, `normal` or `poor` (see above) |
| `wb_income_group` | the World Bank class the wealth group is taken from |
| `arab_identity_contested` | `true` for Comoros, Djibouti and Somalia. A flag only; these countries stay in every comparison |
| `travel_document` | the line in the application: `<demonym> passport` |
| `note` | remarks |

| group | rows | which |
|---|---|---|
| `arab` | 22 | all Arab League member states (a political-institutional criterion, not an ethnic one) |
| `placebo` | 4 | Uruguay, Malawi, Maldives, Cambodia |

There is no row without a nationality.

**What the four placebo nationalities are for.** Any set of nationality labels makes a
model's answers move a little. The four show how much, so that the differences among the
22 can be told from noise. They are a check, not a research question: the project is
about the differences among the 22. They are the four of the earlier designs, chosen on
2026-10-04 before any data, from four World Bank regions and the four income groups, one
of them Muslim-majority. All four need the same Australian visa under the same rules.
They can be dropped by deleting their rows in both tables.

**Legal status in the United Arab Emirates.** The applicants live there
(`../applicants/README.md`), and every application states the same legal status,
whatever the nationality. In reality the Emirati applicant would be a citizen, and
citizens of the other five Gulf Cooperation Council states "may commence work
immediately in the UAE, without the need to obtain a residence visa, unlike citizens of
other nationalities" (government portal u.ae, page updated 12 August 2026, read through
a summarising tool). The application does not say this, but a model may know it. The
`note` column marks these six rows; as a check, the comparisons can be repeated without
them.

## Notes on single nationalities

These labels carry associations that change over time, and a model may have learned them
differently depending on when its training data ends.

- **Palestine**: Arab League member; statehood is not recognised everywhere. Kept
  because "Palestinian" is a common self-description. Whether a "Palestinian passport"
  line reads naturally to a model is untested.
- **Syria**: Arab League membership suspended 2011-2023, restored May 2023; treated as a
  member. The Assad government fell in December 2024.
- **Sudan**: war since April 2023.
- **United Arab Emirates**: the country the applicants live in.
- **Realism**: not every one of the 26 nationalities has a sizeable community in the
  United Arab Emirates. The applications treat every nationality the same way; say so as
  a limitation.
- Outputs refer to "Arab League member-state nationalities", not "Arab applicants".

## Not part of the design

An earlier draft of 2026-10-10 compared the 22 with 22 non-Arab passports of similar
strength and with five non-Arab Muslim-majority passports. Laith removed this: the
project is about bias among Arabs, and it does not look at passport strength. The
material is in `research/visa_scenario/parked_comparison_set/`.
