# Prompts

Written on 2026-10-08. Each file is a message with placeholders. The earlier hiring and
promotion prompts are in `research/old_design/hiring_2026-10-04/prompts/`.

Every run has two messages: the **main prompt** (who the model is, and the bank's
policy), then the **task** (one customer file and the request for the rating).

| file | what it is |
|---|---|
| `main_prompt.txt` | the main prompt. `{policy}` is filled with one of the two versions of the policy |
| `task_wording_1.txt`, `task_wording_2.txt`, `task_wording_3.txt` | the task in three phrasings, so that a result does not depend on one phrasing. `{customer_file}` is filled with one customer file |

## Placeholders

| placeholder | filled with | comes from |
|---|---|---|
| `{policy}` | the policy without or with the paragraph on nationality | `experiment/policy/` |
| `{customer_file}` | one customer with one nationality | `experiment/customers/`, `experiment/countries/customer_nationalities.csv` |

The nationality enters only through the customer file: the lines `Nationality:`,
`Identity document:` and, for the German customer, `Residence status:`.

## The answer

All three wordings ask for the same JSON object:

| key | values |
|---|---|
| `risk_score` | integer from 0 (lowest risk) to 100 (highest risk) |
| `risk_rating` | `low`, `medium` or `high` |
| `enhanced_checks` | `yes` or `no` |
| `recommendation` | `open`, `escalate` or `decline` |
| `reason` | one or two sentences |

Never call the risk score a probability.

## Rules when editing

- The three wordings must ask for the same thing and must have the same answer format.
  `scripts/build_runs.py` checks the format.
- The main prompt says that a compliance analyst takes the final decision. Keep that: it
  is how the products in this field describe themselves, and EU law requires human
  involvement in such decisions from July 2027.
- Fix the prompts before the pilot. Do not change them after seeing results.

## Open

- Whether the main prompt is sent as the system message (see `experiment/README.md`).
- The prompts are in English although the bank is in Germany.
