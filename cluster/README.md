# cluster

How a batch of real model calls is run on bwUniCluster (KIT). Written on 2026-10-24.

**Nothing has been run on the cluster.** `run_vllm.sbatch` has never been submitted. Before
the first approved run, check it against the helpers that already work there
(`~/is617/repo/cluster/lib.sh`: `vllm_start`, `vllm_wait`, `vllm_verify_model`,
`vllm_stop`) and fix the `srun` line, the container options and the paths where they
differ.

**Nothing is submitted without the team's approval.** A real run is a real model call
(`CLAUDE.md`, "Compute and models"). The script refuses to do anything unless
`ALLOW_REAL_CALLS=yes` is set, and that is set only after the team has approved this run.
It is the only place that passes `--allow-real-calls` to the pipeline.

## What `run_vllm.sbatch` does

One job runs one stage for one model, on one GPU (partition `gpu_a100_il`, 4 hours):

1. Exits with `refusing:` unless `ALLOW_REAL_CALLS=yes`.
2. Exits if a required variable is missing.
3. Looks up the model id of `ALIAS` in `experiment/models.csv` (stage `answers`) or
   `experiment/judge/judge_models.csv` (stage `judge`). It stops here if the revision of
   the model is not pinned or if `experiment/` or `pipeline/` has uncommitted changes,
   because the stage would refuse anyway, and this saves the minutes it takes to load a
   model.
4. Starts `vllm serve` in the container `pyxis_vllm_is617` and writes its log to
   `logs/vllm-<job>.log`.
5. Waits until `http://localhost:<port>/v1/models` answers (every 10 seconds, at most 900
   seconds).
6. Runs `python -m pipeline.run_models` (stage `answers`) or `python -m pipeline.run_judge`
   (stage `judge`) against the local server.
7. Stops the server and exits with the exit code of the stage.

The script talks to `localhost` only. It sets `HF_HUB_OFFLINE=1` and
`VLLM_NO_USAGE_STATS=1` so that vLLM does not contact the internet.

## Before the first submission

1. The team has approved the run, for this model and this batch.
2. The `revision` of the model is pinned in `experiment/models.csv` (answers) or
   `experiment/judge/judge_models.csv` (judge), and committed. Both columns are empty
   today, so every real run is refused. The pin is the exact version of the model (a commit
   of its Hugging Face repo) that was downloaded.
3. The repo on the cluster is a `git clone` at that commit, not a plain copy. A real run is
   refused when `git status` fails or shows a change in `experiment/` or `pipeline/`, so
   that every raw answer can be tied to a commit.
4. There is a Python 3.11 or newer for the pipeline (standard library only). The system
   python of the cluster may be older: pass the python of a venv as `PYTHON`.
5. The model is downloaded to a folder on the cluster. `MODEL_PATH` is that folder.
6. `mkdir -p logs` in the repo root. Slurm does not create the folder of `--output`.
7. The script has been checked against `lib.sh` (see above).

## Submit one batch

From the repo root on the cluster. Variables are passed with `--export=ALL,...`:

```
sbatch --export=ALL,STAGE=answers,ALIAS=qwen3-8b,BATCH=pilot1,BLOCKS=1,MODEL_PATH=/path/to/qwen3-8b,ALLOW_REAL_CALLS=yes cluster/run_vllm.sbatch
```

The judge, after the answers of the batch have been read and the judge inputs built:

```
sbatch --export=ALL,STAGE=judge,ALIAS=gpt-oss-120b,BATCH=pilot1,MODEL_PATH=/path/to/gpt-oss-120b,ALLOW_REAL_CALLS=yes cluster/run_vllm.sbatch
```

| variable | | meaning |
|---|---|---|
| `STAGE` | required | `answers` or `judge` |
| `ALIAS` | required | the alias in `experiment/models.csv` (answers) or `experiment/judge/judge_models.csv` (judge) |
| `BATCH` | required | name of the batch; it must not start with `mock` |
| `MODEL_PATH` | required | folder with the weights on the cluster |
| `ALLOW_REAL_CALLS` | required | `yes`, only after the team approved this run |
| `BLOCKS` | optional | stage `answers` only: blocks to run, space-separated, for example `"1 2"`. Without it all three blocks run |
| `WORKERS` | optional | parallel calls, default 16 |
| `PORT` | optional | port of the server, default 8000 |
| `VLLM_ARGS` | optional | extra arguments for `vllm serve`, for example `--max-model-len 8192`. `experiment/models.csv` has a note for Mistral |
| `PYTHON` | optional | the python to use, default `python3` |

Run one model and one block at a time, so that a failed batch can be repeated on its own
(`experiment/README.md`, "Run plan"). A batch belongs to one model: the manifest in
`data/raw/<batch>/` refuses a second model under the same batch name.

## Order of the stages

1. `answers` job: `data/raw/<batch>/answers.jsonl`.
2. `python -m pipeline.parse_answers --batch <batch>` and
   `python -m pipeline.judge_build --batch <batch>`. No GPU and a few seconds; they can run on
   the cluster or on a PC after the raw files are copied.
3. `judge` job: `data/raw/<batch>/judge_<alias>.jsonl`.
4. `python -m pipeline.judge_parse --batch <batch> --judge <alias>`.
5. The hand-coding and the agreement check (`pipeline/README.md`, "Hand-coding the
   validation sample").

`pipeline/README.md` has every command and the files each stage reads and writes.

## After a job

- The log of the job is `logs/is617-<job>.out`, the log of the server `logs/vllm-<job>.log`.
  `logs/` is ignored by git.
- The summary of the stage (planned, already done, called, errors) is at the end of the job
  log, and in `data/raw/<batch>/manifest.json` (answers) or
  `judge_<alias>_manifest.json` (judge). An exit code of 0 means the stage ran through; read
  the number of errors as well.
- A job that stopped (time limit, a failed node) can be submitted again with the same
  command. The stage skips what is already done and continues.
- Copy `data/raw/<batch>/` off the cluster and commit it (`data/README.md`). Never keep the
  only copy on the cluster: workspaces expire.
