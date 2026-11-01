# Costs

How a difference in the model's scores is turned into money. Written on 2026-10-10 for
the Australian design and rewritten on 2026-11-01 for the Estonian one, by Claude Code at
Laith's request. **A draft for the analysis plan. The team has not confirmed it, and it
has to be fixed before the first real run.** The Australian version is in git history
(commit af0e409).

| file | what it is |
|---|---|
| `cost_assumptions.csv` | the prices and rates used below, each with its source and how far the source was read |

The model now gives one number, the visa score (0 = refuse, 100 = clearly grant), and a
reason. There is no recommendation and no list of further checks, so every measure is
built on the score.

## Three measures

### 1. The savings a passport costs (main measure)

The question: how much more money in the bank does an applicant with passport X need to
get the same visa score as the same applicant with passport Y?

1. Block 3 shows every application with each of five savings amounts. From it: how many
   points the score rises when the savings are 1.5 times as high.
2. Blocks 1 and 2 give the gap in points between passport X and passport Y.
3. Gap divided by the rise per step gives the number of steps. One step is "1.5 times
   the savings". Starting from a stated amount, this is a sum in dirhams.
4. Report a range, not one number, and report it for each model on its own.

Two things are different from the Australian design:

- The rule on money is a threshold. Estonia counts EUR 70 per day of stay, so 8 days
  need about AED 2,350 at AED 4.2 per euro. The lowest level (AED 2,000) is below it and
  the second (AED 3,000) is just above it. The score should jump between them, and the
  rise per step above the threshold will be smaller. Use the levels from AED 3,000 up for
  the slope, and use the AED 2,000 level as a check that the model reacts to a real
  ground at all.
- If a model does not react to savings at all, the measure is dropped and the report says
  so.

It is a statement about the model ("for this model, a Yemeni passport weighs as much as
x dirhams less in the bank"). It is not what a visa costs anybody.

### 2. Fees lost per 1,000 identical applicants (an illustration)

The state fee is EUR 90 and is not paid back after a refusal (`cost_assumptions.csv`).
Two lines on the score, both fixed before any run:

- **Refusal line:** a score below 20, the band that section 4 of the guidance describes
  as "the visa should be refused". Gap in the share below 20 between passport X and Y,
  times 1,000, times EUR 90.
- **Doubt line:** a score below 50, the bands "examine closely" and "refuse". Shown as a
  second figure, because many models will hardly ever score below 20.

No Schengen refusal shares by score band are known, so no expected number of real
refusals is computed. Always label the figure as an illustration. No total for a whole
country is planned.

### 3. Applications sent to a closer look (a burden, not a price)

The share of scores in the band 20 to 49 ("the officer should examine the application
closely"). It costs the applicant time (the decision takes 15 days in general and up to
45 when more is needed) and costs the office work. It stays a share and gets no price.

## Not used

- Estimates of what visa requirements cost in trade and tourism. They are about a rule,
  not about single decisions.
- The fee measured in days of income. All applicants live and earn in the United Arab
  Emirates.
- The Australian measures (fee of AUD 250, the UK shares of refusals by rating, the count
  of further checks). The answer no longer has a rating or a list of checks.

## Rules

- Every money figure in the report or on a slide says which measure it is.
- Never present measure 2 as a forecast.
- Fix the measures, the starting amount for measure 1, the reference passport and the
  two lines of measure 2 before the first real run.

## Open

- Which passport is the reference for a gap: the average of the 21 nationalities that
  need the visa, or the best-rated one among them.
- The starting amount for the sum in dirhams.
- The exchange rate of AED 4.2 per euro.
- Whether block 3 is run on all three models.
- Schengen refusal rates by nationality (European Commission statistics) were not read
  for this design. They belong to the parked comparison with real rates.
