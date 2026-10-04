# Experiment

What is in this folder and how the experiment is run. Decided on 2026-10-04. The documents in `research/old_design/` describe the earlier design.

## Folders

| folder | content |
|---|---|
| `prompts/` | the messages the model gets: main prompts and follow-up messages, for hiring and promotion, with and without the ignore-nationality paragraph |
| `jobs/` | 20 jobs, one row each |
| `cvs/` | 20 CVs, one per job |
| `countries/` | the 22 countries a job is set in, and the 29 nationalities an applicant can have |
| `models.csv` | the four planned models: name, exact model id, version to pin, notes |

Each folder has its own README.

**Table conventions.** Tables are UTF-8 CSV files with one thing per row. Several values
in one cell are separated by ` | ` (space, pipe, space). An empty cell means not
applicable. Text that is filled in later is written `{name}`, for example `{country}`.

## What one run is

One run is one call to one model: a main prompt, then a follow-up message. It is built
from one job with its CV, one country, one nationality (rate one) or two nationalities
(choose between two), and one wording.

## Run plan

**Models:** Qwen3 8B, Llama 3.1 8B, Gemma 3 12B, Mistral Small 24B (`models.csv`).
The exact versions still have to be pinned. A fifth model is optional.

**Rules**

- Every job is run in every country: 20 x 22 = 440 job-country combinations.
- **Rate one:** each combination with each of the 29 nationality rows.
- **Choose between two:** in each combination the 22 Arab nationalities are randomly
  paired into 11 pairs, and each pair is shown in both orders (22 runs). Both candidates
  have the same CV. Every nationality appears equally often; a specific pair comes up
  about 21 times. The pairs are drawn once with a fixed seed, before any results exist.
- **Wordings rotate:** each run uses one of the three wordings in turn. They are not
  multiplied.
- One run per combination, no repeats.

**Blocks, most important first.** Each block is a complete result on its own.

| block | what | runs per model |
|---|---|---|
| 1 | hiring, rate one applicant | 12,760 |
| 2 | hiring, choose between two (both versions) | 19,360 |
| 3 | blocks 1 and 2 again with the ignore prompt | 32,120 |
| 4 | promotion, everything | 64,240 |
| | **total** | **128,480** |

With four models: 513,920 runs. Block 1 on all models is enough for the preliminary
results of the midterm.

Run in small batches (one model and one block at a time, or smaller), so that a failed
batch can be repeated on its own.

## Open

- Hypotheses and an analysis plan for this design. They have to be written before the
  first real run, not after seeing results. The draft preregistration in
  `research/old_design/` belongs to the earlier design.
- Whether the main prompt is sent as the system message, or as a first message that the
  model answers before it gets the follow-up.
- Pinning the model versions.
- A timing test of a few hundred runs.
- The code that builds and sends the runs was removed on 2026-10-04 (git history, commit
  670f827) and has to be rewritten for this design.
- No real model calls without the team's explicit approval.
