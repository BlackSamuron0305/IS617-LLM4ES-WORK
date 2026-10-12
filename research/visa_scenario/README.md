# Visa scenario: research notes

Three internal notes written by Claude Code on 2026-10-10 in one working session with
Laith, when the project moved from bank customer checks to visitor visa applications.
They are research notes, not report text and not slide text. Each note has a table that
says how far every source was read. Many pages were read only through a summarising
tool; a quote or a number from such a page has to be checked on the original before it
goes into the paper.

| file | question | answer in one line |
|---|---|---|
| `ai_in_visa_processing.md` | How is AI really used in visa processing, and what can a prompt be modelled on? | Rule-based sorting into three levels, with nationality as an input in the UK (until 2020) and the Netherlands; refusals stay with a person everywhere; no language model that rates applications is documented |
| `destination_and_requirements.md` | Which country asks all 22 Arab League nationalities for the same visa, and what does the application look like? | Australia, Visitor visa (subclass 600): same form, same fee (AUD 250), same legal test. The note has the criteria, the documents and real figures by nationality |
| `motivation_and_cost_of_bias.md` | Which numbers support the motivation, and how can a gap be expressed in money? | Official figures on anti-Muslim discrimination; real refusal rates by nationality; three ways to price a gap, of which "the savings that would make up for it" fits best |

Things to know when reading them:

- The notes were written in parallel, before the design was fixed. Where they speak of
  applicants who live in Germany, of a German or an Iranian benchmark, of four placebo
  nationalities, of savings in euros or of a fee of AUD 200, the design has moved on:
  `experiment/README.md` and its folders are authoritative. The applicants now live in
  the United Arab Emirates; the sources for that are in
  `experiment/applicants/README.md` and were not part of these notes.
- The notes also discuss passport strength (Henley Passport Index) and comparisons with
  non-Arab nationalities. Laith took both out of the design: the project is about bias
  among the 22 Arab League nationalities, measured against the official rules. What was
  built for the other idea is in `parked_comparison_set/`.
- The sources that went into the design, the proposal and the slides are in
  `../references.bib` and `../literature_matrix.csv` (87 entries added on 2026-10-10).
  In the matrix, `abstract` also covers pages read through a summarising tool.
- No claim of novelty is made in any of them. The searches were limited.
- Data files and scripts used for the notes were in a temporary folder and are not in
  the repository. What the design needs from them is in
  `experiment/countries/official_rules.csv` and `experiment/costs/cost_assumptions.csv`.
- Two small tables were added later the same day for the pitch slide on why the setting
  is realistic: `gulf_residents_by_origin_2024.csv` (foreign citizens in the six Gulf
  states by Arab League country of origin, mid-2024; `undesa2024migrantstock`) and
  `citizenship_loss_rules_2020.csv` (what happens to the citizenship of each of the 22
  when a citizen takes another one, law on 1 January 2020; `vink2020macimide`). Both
  were taken from the data files themselves. The second ends in 2020.
