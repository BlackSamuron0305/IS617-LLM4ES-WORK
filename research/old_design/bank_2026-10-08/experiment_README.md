# Experiment

What is in this folder and how the experiment is run. Decided on 2026-10-08, when the
project moved from hiring to bank customer checks. The hiring design of 2026-10-04 is in
`research/old_design/hiring_2026-10-04/`. Why this scenario was chosen is written up in
`research/scenario_reviews/bank_onboarding_scenario.md`.

## The idea in four sentences

A bank in Germany has to check every new customer for money-laundering risk and has to
record the customer's nationality. The model is given the bank's written policy and one
customer file, and returns a risk rating and a recommendation. The file is identical for
every customer except for the nationality and the passport that goes with it. Everyone
lives and earns in Germany and has no payments to other countries, so by the policy the
passport gives no reason for a different rating.

## Folders

| folder | content |
|---|---|
| `policy/` | the bank's policy, and the paragraph on nationality that is added in the second version |
| `customers/` | 20 customer files, one row each, and the layout of a file |
| `countries/` | the 28 nationalities a customer can have, with the EU high-risk list status, and World Bank data |
| `prompts/` | the main prompt and the three wordings of the task |
| `models.csv` | the four planned models: name, exact model id, version to pin, notes |

Each folder has its own README. `scripts/build_runs.py` puts the prompts together and
checks them; it never calls a model.

**Table conventions.** Tables are UTF-8 CSV files with one thing per row. An empty cell
means not applicable. Text that is filled in from a table is written `{{NAME}}`; text
that is filled in for each run is written `{name}`.

## What one run is

One run is one call to one model with two messages:

1. the **main prompt**: who the model is, and the bank's policy in one of two versions;
2. the **task**: one customer file and the request for the rating, in one of three
   wordings.

The answer is one JSON object: `risk_score` (0 to 100), `risk_rating` (low, medium,
high), `enhanced_checks` (yes, no), `recommendation` (open, escalate, decline) and a
short `reason`.

## What varies

| | values | number |
|---|---|---|
| customer file | 20 customers with different occupations and incomes; 10 plain files and 10 with one mild risk indicator (`customers/`) | 20 |
| nationality | 22 Arab League nationalities, German and Turkish as benchmarks, 4 placebo nationalities (`countries/`) | 28 |
| policy version | without and with the paragraph that says nationality is not a risk factor (`policy/`) | 2 |
| wording of the task | three phrasings of the same request (`prompts/`) | 3 |

Nothing else changes between runs. There is no version without a nationality: the field
is mandatory in a bank's file.

## Run plan

`python scripts/build_runs.py` prints these counts from the files.

| block | what | prompts | runs per model with 5 repetitions |
|---|---|---|---|
| 1 | policy without the nationality rule | 20 x 28 x 3 = 1,680 | 8,400 |
| 2 | policy with the nationality rule | 1,680 | 8,400 |
| | **total** | **3,360** | **16,800** |

With four models: 67,200 runs. A prompt has about 720 to 810 words. Block 1 on all models
is enough for the preliminary results of the midterm.

Five repetitions per prompt are a proposal. Whether repetitions make sense depends on the
decoding settings, which are not decided (see "Open").

Run in small batches (one model and one block at a time, or smaller), so that a failed
batch can be repeated on its own.

## What will be compared (draft, not an analysis plan)

- The spread of the risk score and of the ratings across the 22 Arab League
  nationalities, against the spread across the 4 placebo nationalities.
- The four Arab League countries on the EU high-risk list (Algeria, Lebanon, Syria,
  Yemen) against the eighteen that are not on it. By the policy the list applies to where
  a customer lives and where payments go, not to the passport.
- The unlisted Arab League nationalities against the placebo nationalities and against
  the German and Turkish benchmarks.
- The same with the nationality rule in the policy.
- Plain files against files with one risk indicator.
- The four models against each other.
- How often an answer cannot be read or the model refuses, by nationality.

The risk score is a rating given by a model. It is not a probability of anything.

## Open

- **Hypotheses and an analysis plan.** They have to be written before the first real run,
  not after seeing results. Nothing above is a hypothesis.
- **A pilot** that shows whether the answers vary at all. All 20 customers are ordinary
  low-risk customers, so a model may answer "low" for everybody. A pilot is a real model
  call and needs the team's explicit approval.
- **Decoding settings and repetitions**: temperature, seeds, and how many repetitions.
- **How the answer format is enforced**: by the instruction only, or by a JSON schema at
  decoding time.
- **Whether the main prompt is sent as the system message.** The products in this field
  give the model the institution's procedures as standing instructions, which speaks for
  the system message. Gemma has no separate system role (`models.csv`).
- **Whether the list of high-risk countries stays in the policy** (`policy/README.md`).
- Pinning the model versions, and a timing test of a few hundred runs.
- The code that sends the runs and reads the answers does not exist. It must refuse real
  calls unless the team has approved them explicitly.
- No real model calls without the team's explicit approval.
