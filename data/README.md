# data

The output of our model runs is saved here. It is empty until the first real run.

- `raw/`: the model responses exactly as they came back, one folder per run. Never edited by hand.
- `processed/`: the tables built from the raw responses, one folder per run.

Output of real runs is committed to git. Output of mock or test runs (folder name
starts with `mock`) is ignored by git and must never be reported as a result.
