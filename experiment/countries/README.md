# Countries

Rewritten on 2026-11-01 for the Estonian design. The tables of the Australian design
(with the real grant and refusal rates of Australia and the United States) are in git
history (commit af0e409); the tables of the bank design are in
`research/old_design/bank_2026-10-08/countries/`.

| file | what it is |
|---|---|
| `applicant_nationalities.csv` | the 26 nationalities an applicant can have: the 22 Arab League nationalities and 4 unrelated ones, with the column `visa_required` |
| `official_rules.csv` | what the official rules for a Schengen visa to Estonia say about each of the 26 |

## The yardstick: the grounds for refusal are the same for everyone

The project asks about bias among the 22 Arab League nationalities. The yardstick is
what the official rules say, not how strong a passport is or how a country is seen. For
a Schengen visa the rule that matters is Article 32(1) of the Visa Code (Regulation (EC)
No 810/2009): it lists the grounds on which a visa shall be refused, and nationality is
not one of them (text read from the screenshot Laith supplied; the grounds are quoted in
`../policy/regulation_text.txt`). Estonia applies the same Visa Code to every applicant.

`official_rules.csv` has one row per nationality:

| column | what it says | the same for all 24 that need a visa? | source |
|---|---|---|---|
| `visa_needed` | Schengen visa, type C (short stay); or none for the two visa-exempt nationalities | yes | see "Two nationalities need no visa" |
| `application_form` | online form (eelviisataotlus.vm.ee), printed, signed, lodged in person | yes | Estonian Ministry of Foreign Affairs, page on the Schengen visa: "The form must be filled in online, printed and signed"; "All visa applications must be submitted in person." |
| `fee_eur` | 90 | yes | same page: "Schengen visa 90 Euros". Reduced fees (35 euros) exist for eleven other nationalities, none of them in this experiment |
| `legal_test` | the grounds of Article 32(1) | yes | Visa Code, Article 32(1), read from the screenshot |
| `nationality_is_a_ground_in_art_32` | no | yes | same: the list names no nationality |
| `means_per_day_eur`, `insurance_min_eur` | 70, 30000 | yes | same page of the ministry |
| `entry_ban_or_visa_measure_2026_11_01` | none known; **not checked** | yes (as far as known) | see the warning below |

`pipeline/build_runs.py` checks that every column of this table has one value across the
nationalities that need a visa, that the exempt ones say so, and that the amounts in the
guidance are the amounts in this table.

## Two nationalities need no visa

`applicant_nationalities.csv` has `visa_required = no` for two of the 26:

- **United Arab Emirates (Emirati).** Citizens need no visa for short stays in the
  Schengen area. This is the case that the Australian design avoided, and it is the
  price of the Estonia setting. Source: Annex II of Regulation (EU) 2018/1806 and the
  earlier project note (`research/visa_scenario/destination_and_requirements.md`); not
  read again in full text, check before the first run.
- **Uruguay (Uruguayan), a placebo.** Visa-exempt for short stays. Same source, same
  caveat.

They stay in the experiment on purpose (the application states the same legal status for
everyone, Laith's rule of 2026-10-10, and the rows cost almost nothing), but they are
**reported apart** from the 24 nationalities that need a visa. Their row says what a
model does when it is given a visa application that, in reality, nobody from that country
would hand in. For the Emirati row there is a second reason to read it apart: in reality
an Emirati born in the Emirates is a citizen, and the application says "lawful long-term
resident". The main comparison among the Arab nationalities is therefore among **21**
(the 22 without the Emirates). A check that also leaves out the five other Gulf states is
listed among the comparisons.

**Warning: check the rules again before the runs.** Not checked: (1) Council measures
under Article 25a of the Visa Code that make the processing of visas for a country's
nationals harder or easier; (2) the list of nationalities whose applications are sent to
other Member States for consultation (Article 22), which lengthens the processing and
does not change the grounds; (3) whether a travel ban or special rule exists for an Arab
League nationality at the time of the runs. A rule that names one of the 21 would mean
the yardstick is no longer flat.

## What practice adds

Real consulates refuse and grant different nationalities at different rates, although
the grounds are the same. European Commission statistics give the share of Schengen visas
not issued by country; they were **not** read for this design, and comparing the model's
order of the 22 with the real rates stays on the parked list. If the figures are added
later they are context, not a yardstick: they come from real applicants in different
circumstances.

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

## Why Estonia is the destination

Laith's decision of 2026-11-01. Reasons given: the Visa Code requires that a refusal has a
valid reason (Article 32, which Laith supplied as a screenshot), so a score and a stated
reason can be checked against a written list of grounds; and Laith reports that Estonia is
adding AI to many public services, including support for visa decisions. **That last claim
was not confirmed.** A search on 2026-11-01 found the national AI programme Eesti.ai
(launched January 2026) and a plan for digital identities for AI agents, and nothing
about visa decisions; the ministry's website search returned no result for "artificial
intelligence". Do not state it in the report until a source is found
(`research/visa_scenario/estonia_scenario.md`).

The cost of the choice is the one the Australian design avoided: the rules are not flat
for all 22, because one of them (Emirati) needs no visa. See "Two nationalities need no
visa".

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
| `visa_required` | `yes`, or `no` for the Emirati and the Uruguayan nationality (see above) |
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
of them Muslim-majority. Three of the four need the same Schengen visa under the same rules; Uruguay needs none.
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
