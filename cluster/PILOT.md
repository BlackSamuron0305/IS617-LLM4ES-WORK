# The pilot: how to run it

Written on 2026-11-01. **Nothing here has been run. A real run needs the team's explicit
approval** (CLAUDE.md, "Compute and models"). The go / no-go rules are in
`experiment/analysis_plan.md`, section 5.

**What:** `qwen3-32b` (already downloaded on the cluster), base variant, blocks 1 and 3,
wording 1, one repetition. 520 + 2,080 = 2,600 calls, each about 700 words in and under 100
tokens out. One H100 for about an hour including the start of the server.

**Why this one:** it needs no download and it is one of the three audited models. If the
instrument fails here, nothing else is worth running.

## Before the submission (on the PC)

1. The team has read the prompts (`experiment/prompts/README.md`) and agreed to freeze them.
2. The model is pinned (done on 2026-11-01: the commit hash from the download metadata is in
   `experiment/models.csv`).
3. Run the tests and a mock walk-through:
   `python -m unittest discover -s tests -t .` and
   `python -m pipeline.run_models --batch mock_check --model qwen3-32b --mock --block 1 --block 3 --wording 1 --max-repetitions 1`
   then `python -m pipeline.parse_answers --batch mock_check` and
   `python -m pipeline.pilot_report --batch mock_check`.
4. Commit and push (`experiment/` and `pipeline/` must have no uncommitted change), then
   `git tag prereg-pilot && git push --tags`.

## On the cluster (checked on 2026-11-01)

- `qwen3-32b` in the workspace `llm` is a symlink to `/pfs/work9/workspace/scratch/ma_lsandouk-is617/models/qwen3-32b`
  (the workspace `is617`, expires about 2026-11-17). Its commit hash,
  `9216db5781bf21249d130ec9da846c4624c16137`, is in `experiment/models.csv`.
- The container `pyxis_vllm` (vLLM 0.29) exists. `cluster/run_vllm.sbatch` now starts the server
  the way `~/llm/vllm_serve.sbatch` does.
- The login Python is 3.9: load `devel/python/3.11.7-gnu-11.4` (`PYTHON_MODULE`).
- Queues on 2026-11-01 (`sbatch --test-only`): `dev_gpu_h100` (30 minutes) in about 20 minutes,
  `gpu_h100_short` (30 minutes) in about 30, `gpu_h100` (hours) in a week. A100 nodes in the short
  queue have 40 GB, too small for Qwen3-32B in bf16 on one GPU. So the pilot uses a 30-minute H100
  slot. The runner skips finished calls, so a job that hits the limit is submitted again with the
  same command and continues.

```
source ~/llm/env.sh
mkdir -p $WS/is617_work && cd $WS/is617_work
git clone https://github.com/BlackSamuron0305/IS617-LLM4ES-WORK.git repo && cd repo
git checkout prereg-pilot && mkdir -p logs
sbatch --partition=dev_gpu_h100 --gres=gpu:1 --time=00:30:00   --export=ALL,STAGE=answers,ALIAS=qwen3-32b,BATCH=pilot1,BLOCKS="1 3",WORDINGS=1,MAX_REPETITIONS=1,MODEL_PATH=$WS/models/qwen3-32b,PYTHON_MODULE=devel/python/3.11.7-gnu-11.4,PYTHON=python3,WORKERS=48,ALLOW_REAL_CALLS=yes cluster/run_vllm.sbatch
```

Exclude the nodes that failed before (`uc3n088`, `uc3n089`, `uc3n107`) with `--exclude`.

## After the job

```
python -m pipeline.parse_answers --batch pilot1
python -m pipeline.pilot_report --batch pilot1
```

Copy `data/raw/pilot1/` and `data/processed/pilot1/` to the PC (never keep the only copy on
the cluster; workspaces expire) and look at the report. The four checks decide what changes
before the full run. Look at 20 reasons by hand, in particular those of the AED 2,000
applications and those of the Syrian, Sudanese and Emirati rows.

**Optional second step: the judge on the pilot reasons.** `python -m pipeline.judge_build
--batch pilot1`, then the stage `judge` with `ALIAS=gpt-oss-120b` (already on the cluster;
needs its own pinned revision and `--limit 300` first). The aim is to see whether the six codes
come out sensibly and to draw the sample the team codes by hand
(`python -m pipeline.judge_validate sample --batch pilot1`).

The raw files of the pilot are labelled as a pilot. They are not a result and are not part of
the confirmatory analysis.
