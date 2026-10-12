# Costs

How a difference in the model's answers is turned into money. Written on 2026-10-10 by
Claude Code at Laith's request. **A draft for the analysis plan. The team has not
confirmed it, and it has to be fixed before the first real run.**

| file | what it is |
|---|---|
| `cost_assumptions.csv` | the prices and rates used below, each with its source and how far the source was read |

The research behind this is in
`research/visa_scenario/motivation_and_cost_of_bias.md`, section 6.

## Three measures

### 1. The savings a passport costs (main measure)

The question: how much more money in the bank does an applicant with passport X need to
get the same risk score as the same applicant with passport Y?

1. Block 3 shows every application with each of five savings amounts. From it: how many
   points the score falls when the savings are 1.5 times as high.
2. Blocks 1 and 2 give the gap in points between passport X and passport Y.
3. Gap divided by the fall per step gives the number of steps. One step is "1.5 times
   the savings". Starting from a stated amount, this is a sum in dirhams.
4. Report a range, not one number, and report it for each model on its own.

Why this one: it works on the 0 to 100 score, so it still works if a model recommends
"grant" for everybody. It needs no data from outside. It makes no statement about real
visa offices. A published audit of language models did the same with credit-score points
and then turned them into dollars (`bowen2025measuring`); studies with people express
gaps as years of work experience (`bertrand2004emily`) or as credit-score points.

Its weak points:

- If a model does not react to savings, step 1 is close to zero and the result is
  meaningless. The pilot has to show that the score reacts. If it does not, this measure
  is dropped and the report says so.
- The sum in dirhams depends on the starting amount. State it.
- It is a statement about the model: "for this model, a Yemeni passport weighs as much
  as x dirhams less in the bank". It is not what a visa costs anybody.

### 2. Fees lost per 1,000 identical applicants (an illustration)

The fee for the visa is AUD 250 since 1 July 2026 (Migration Regulations, Schedule 1,
item 1236) and is not paid back after a refusal (`cost_assumptions.csv`).

- **Direct:** the share of `refuse` recommendations for passport X minus the share for
  passport Y, times 1,000, times AUD 250. A gap of three percentage points is 30 more
  refusals and AUD 7,500.
- **If the models hardly ever recommend a refusal:** use the rating. In the UK's
  streaming tool, 3.6% of visit applications rated green were refused, 18.9% of those
  rated amber and 51.4% of those rated red (one office, two months of 2017). Applying
  these shares to the model's low, medium and high gives an expected number of
  refusals. This borrows figures from another country and another year and has to be
  labelled as an illustration every time it is shown.

No total for a whole country is planned. It would need the assumption that a model
decides real applications, and no authority is documented as doing that.

### 3. Extra checks per applicant (a burden, not a price)

The number of letters in `further_checks`: more bank statements, a call to the employer,
more proof of ties, a detailed itinerary, an interview, a police certificate. Each one
costs the applicant time and delays the decision. No price list for them was found, so
this stays a count.

## Not used

- Estimates of what visa requirements cost in trade and tourism (for example 52% to 63%
  less travel between two countries with a visa requirement). They are about a rule, not
  about single decisions, and cannot be produced from model answers. One of them can
  serve as a line of motivation.
- The fee measured in days of income. All applicants live and earn in the United Arab
  Emirates.

## Numbers for motivation, not for the analysis

- Fees paid for refused Schengen visas: EUR 157.1 million in 2025, 145.1 million in
  2024 and 130 million in 2023, according to LAGO Collective (read through a summarising
  tool). The method is refused applications times the fee: 1,632,984 visas not issued in
  2023 times the EUR 80 fee of that year is EUR 130.6 million.
- Beyond the fee: translations of every document, possibly a police certificate, health
  checks and biometrics, lost bookings, and the refusal has to be declared in later
  applications (`research/visa_scenario/destination_and_requirements.md`, section 9).
- Waiting: granted Tourist stream applications from the six Gulf states were decided in
  about one day at the median, Syrian ones in 29 days and Palestinian ones in 30 days
  (July 2024 to September 2025, `homeaffairs2025da449`).
- The same sum for consulates in the Arab League countries in 2025 is about EUR 50
  million (554,327 visas not issued times EUR 90). **Own calculation by Claude from the
  Commission's file, not a published figure.** It counts by place of application, not by
  nationality.

## Rules

- Every money figure in the report or on a slide says which measure it is.
- Never present measure 2 as a forecast.
- Fix the measures, the starting amount for measure 1 and the reference passport before
  the first real run.

## Open

- Which passport is the reference for a gap: the average of the 22 Arab League
  nationalities, or the best-rated one among them.
- The starting amount for the sum in dirhams.
- Whether block 3 is run on all four models.
