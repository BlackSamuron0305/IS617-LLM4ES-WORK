#!/bin/bash
#SBATCH --job-name=is617
#SBATCH --partition=gpu_a100_il
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x-%j.out
#
# Start a vLLM server for one model and run ONE stage of the pipeline against it.
#
# UNTESTED. This script has never run on the cluster. Before the first approved run, check it
# against the helpers that already work there (~/is617/repo/cluster/lib.sh: vllm_start,
# vllm_wait, vllm_verify_model, vllm_stop) and fix the srun line, the container options and the
# paths if they differ. This is the only place that passes --allow-real-calls; it does so only
# when ALLOW_REAL_CALLS=yes, which is set only after the team has approved the run.
#
# Submit from the repo root, after `mkdir -p logs` (Slurm does not create the log folder):
#   sbatch --export=ALL,STAGE=answers,ALIAS=qwen3-32b,BATCH=pilot1,BLOCKS=1,MODEL_PATH=/path/to/qwen3-32b,ALLOW_REAL_CALLS=yes cluster/run_vllm.sbatch
#
# Environment variables:
#   STAGE             required: answers (pipeline.run_models) or judge (pipeline.run_judge)
#   ALIAS             required: alias in experiment/models.csv (answers) or
#                     experiment/judge/judge_models.csv (judge)
#   BATCH             required: batch name; must not start with "mock"
#   MODEL_PATH        required: folder with the model weights on the cluster
#   BLOCKS            optional, answers only: space-separated block numbers, for example "1 2"
#   WORKERS           optional: parallel calls, default 16
#   PORT              optional: port of the server, default 8000
#   VLLM_ARGS         optional: extra arguments for `vllm serve`, for example "--max-model-len 8192"
#   PYTHON            optional: Python 3.11 or newer, default python3 (the cluster's system
#                     python may be older; use the venv's python)
#   ALLOW_REAL_CALLS  must be "yes", or the script exits before doing anything else
#
# The server and this script run on the same node; the only network address used here is
# localhost. The exit code is the exit code of the stage (0 when it ran through).

set -u

# 1. Real calls need the team's approval. Nothing else happens before this check.
if [ "${ALLOW_REAL_CALLS:-}" != "yes" ]; then
    echo "refusing: set ALLOW_REAL_CALLS=yes after the team approved this run" >&2
    exit 1
fi

# 2. Required variables.
missing=""
for name in STAGE ALIAS BATCH MODEL_PATH; do
    if [ -z "${!name:-}" ]; then
        missing="$missing $name"
    fi
done
if [ -n "$missing" ]; then
    echo "error: missing required variable(s):$missing" >&2
    exit 1
fi
case "$STAGE" in
    answers) TABLE=experiment/models.csv ;;
    judge) TABLE=experiment/judge/judge_models.csv ;;
    *) echo "error: STAGE must be answers or judge, not '$STAGE'" >&2; exit 1 ;;
esac
if [ "$STAGE" = "judge" ] && [ -n "${BLOCKS:-}" ]; then
    echo "error: BLOCKS only applies to STAGE=answers" >&2
    exit 1
fi
WORKERS="${WORKERS:-16}"
PORT="${PORT:-8000}"
VLLM_ARGS="${VLLM_ARGS:-}"
PYTHON="${PYTHON:-python3}"

# Run from the folder the job was submitted from: it must be the repo root.
cd "${SLURM_SUBMIT_DIR:-.}" || exit 1
if [ ! -d pipeline ] || [ ! -f "$TABLE" ]; then
    echo "error: $PWD is not the repo root (no pipeline/ or $TABLE); submit from the repo root" >&2
    exit 1
fi

# 3. The model id from the table. A model without a pinned revision, or a repo with uncommitted
# changes, would be refused by the stage anyway; stop here, before the server is loaded.
MODEL_ID=$("$PYTHON" - "$TABLE" "$ALIAS" <<'PY'
import sys
from pipeline.client import COMMIT_HASH
from pipeline.common import dirty_files, load_models

models = load_models(sys.argv[1])
if sys.argv[2] not in models:
    sys.exit(f"error: unknown alias {sys.argv[2]!r}; {sys.argv[1]} has: {', '.join(models)}")
model = models[sys.argv[2]]
if not COMMIT_HASH.fullmatch(model["revision"]):
    sys.exit(f"refusing: {sys.argv[2]} has no pinned revision (a 40-character commit hash) in {sys.argv[1]}")
if dirty_files():
    sys.exit("refusing: git reports uncommitted changes (or fails) in experiment/ or pipeline/")
print(model["model_id"])
PY
) || { echo "error: could not look up $ALIAS in $TABLE (see the message above)" >&2; exit 1; }

# vLLM and the Hugging Face libraries must not contact the internet: the model is a local folder.
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export VLLM_NO_USAGE_STATS=1
export DO_NOT_TRACK=1

VLLM_PID=""
stop_server() {
    if [ -n "$VLLM_PID" ]; then
        kill "$VLLM_PID" 2>/dev/null
        for _ in 1 2 3 4 5 6; do
            kill -0 "$VLLM_PID" 2>/dev/null || break
            sleep 5
        done
        kill -9 "$VLLM_PID" 2>/dev/null
        wait "$VLLM_PID" 2>/dev/null
        VLLM_PID=""
    fi
}
# Stop the server however the script ends (also on scancel or the time limit).
trap stop_server EXIT
trap 'exit 143' TERM INT HUP

# 4. Start the server in the background, inside the container, and log to logs/vllm-<job>.log.
mkdir -p logs
echo "starting vLLM for $MODEL_ID ($STAGE, alias $ALIAS, batch $BATCH) on port $PORT"
# $VLLM_ARGS is split into words on purpose.
srun --ntasks=1 --container-name=pyxis_vllm_is617 --container-mounts="$MODEL_PATH:$MODEL_PATH:ro" \
    vllm serve "$MODEL_PATH" --served-model-name "$MODEL_ID" --port "$PORT" $VLLM_ARGS \
    > "logs/vllm-${SLURM_JOB_ID:-local}.log" 2>&1 &
VLLM_PID=$!

# 5. Wait until the server lists its model: every 10 s, for at most 900 s.
ready=""
waited=0
while [ "$waited" -lt 900 ]; do
    if curl -sf "http://localhost:$PORT/v1/models" > /dev/null; then
        ready=yes
        break
    fi
    if ! kill -0 "$VLLM_PID" 2>/dev/null; then
        echo "error: the vLLM server stopped before it was ready; see logs/vllm-${SLURM_JOB_ID:-local}.log" >&2
        exit 1
    fi
    sleep 10
    waited=$((waited + 10))
done
if [ -z "$ready" ]; then
    echo "error: the server was not ready after 900 s; see logs/vllm-${SLURM_JOB_ID:-local}.log" >&2
    exit 1
fi
echo "server ready after about $waited s"

# 6. Run the stage. This is the only place that passes --allow-real-calls.
if [ "$STAGE" = "answers" ]; then
    cmd=("$PYTHON" -m pipeline.run_models --batch "$BATCH" --model "$ALIAS")
    for block in ${BLOCKS:-}; do
        cmd+=(--block "$block")
    done
else
    cmd=("$PYTHON" -m pipeline.run_judge --batch "$BATCH" --judge "$ALIAS")
fi
cmd+=(--base-url "http://localhost:$PORT/v1" --allow-real-calls --workers "$WORKERS")
"${cmd[@]}"
status=$?

# 7. Stop the server and pass on the exit code of the stage.
stop_server
exit "$status"
