#!/bin/bash
#SBATCH --job-name=is617
#SBATCH --partition=gpu_h100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=120gb
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x-%j.out
#
# Start a vLLM server for one model and run ONE stage of the pipeline against it.
#
# Adapted on 2026-11-01 to the launch method that already works on the cluster
# (~/llm/vllm_serve.sbatch and ~/llm/run_stage.sbatch): `enroot start --rw --rc rc_exec.sh` on the
# unpacked container pyxis_vllm, with the workspace mounted. This is the only place that passes
# --allow-real-calls; it does so only when ALLOW_REAL_CALLS=yes, which is set only after the team
# has approved the run.
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
#   VARIANTS          optional, answers only: space-separated prompt variants, default base
#   WORDINGS          optional, answers only: space-separated task wordings, for example "1"
#   MAX_REPETITIONS   optional, answers only: at most this many repetitions per prompt
#   SHARD             optional, answers only: K/N, only every N-th call starting at K (use one BATCH per shard)
#   LIMIT             optional, answers only: only the first N calls (a smoke test)
#   CONTAINER_NAME    optional: name of the unpacked Enroot container with vLLM, default pyxis_vllm
#   ENV_FILE          optional: file that sets WS and the Enroot paths, default ~/llm/env.sh
#   PYTHON_MODULE     optional: a module to load for Python 3.11 or newer, for example devel/python/3.11.7-gnu-11.4
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
if [ "$STAGE" = "judge" ] && [ -n "${BLOCKS:-}${VARIANTS:-}${WORDINGS:-}${MAX_REPETITIONS:-}${SHARD:-}${LIMIT:-}" ]; then
    echo "error: BLOCKS, VARIANTS, WORDINGS, MAX_REPETITIONS, SHARD and LIMIT only apply to STAGE=answers" >&2
    exit 1
fi
# The environment of the working cluster setup (WS, ENROOT_DATA_PATH, VLLM_IMAGE, HF_HOME).
source "${ENV_FILE:-$HOME/llm/env.sh}" || exit 1
# Enroot keeps its runtime files in $XDG_RUNTIME_DIR/enroot; the login node's /run/user/<id> does not exist
# on a compute node (the first pilot job died with "failed to open .../enroot/fstab"). Use the node-local disk.
export ENROOT_RUNTIME_PATH="${TMPDIR:-/tmp}/enroot-runtime-${SLURM_JOB_ID:-$$}"
mkdir -p "$ENROOT_RUNTIME_PATH"
if [ -n "${PYTHON_MODULE:-}" ]; then
    module load "$PYTHON_MODULE" || exit 1
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

# The plan options of the answers stage, used by the check below and by the run itself.
PLAN=()
if [ "$STAGE" = "answers" ]; then
    for block in ${BLOCKS:-}; do PLAN+=(--block "$block"); done
    for variant in ${VARIANTS:-}; do PLAN+=(--variant "$variant"); done
    for wording in ${WORDINGS:-}; do PLAN+=(--wording "$wording"); done
    if [ -n "${MAX_REPETITIONS:-}" ]; then PLAN+=(--max-repetitions "$MAX_REPETITIONS"); fi
    if [ -n "${SHARD:-}" ]; then PLAN+=(--shard "$SHARD"); fi
    # Nothing left to do: leave before the server is started (it takes minutes to load a model).
    # This is what makes a chain of identical jobs cheap: the later ones end here.
    LEFT=$("$PYTHON" -m pipeline.run_models --batch "$BATCH" --model "$ALIAS" "${PLAN[@]}" --remaining) || exit 1
    echo "plan: $LEFT"
    case "$LEFT" in *'"remaining": 0'*) echo "nothing left to do for $BATCH"; exit 0 ;; esac
    if [ -n "${LIMIT:-}" ]; then PLAN+=(--limit "$LIMIT"); fi
fi

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
# The model folder may be a symlink into another workspace: serve and mount the real path.
MODEL_REAL=$(readlink -f "$MODEL_PATH")
CONTAINER="${CONTAINER_NAME:-pyxis_vllm}"
enroot list | grep -qx "$CONTAINER" || enroot create -n "$CONTAINER" "$VLLM_IMAGE"
# $VLLM_ARGS is split into words on purpose. --rc makes the container run the command it is given
# (the image's own rc would append it to `vllm serve`).
enroot start --rw --rc "$HOME/llm/rc_exec.sh" \
    -m "$WS:$WS" -m "$HOME:$HOME" -m "$(dirname "$MODEL_REAL"):$(dirname "$MODEL_REAL")" -m "${TMPDIR:-/tmp}:/tmp" \
    -e HF_HOME="${HF_HOME:-$WS/hf-cache}" -e HF_HUB_OFFLINE=1 \
    "$CONTAINER" \
    vllm serve "$MODEL_REAL" --served-model-name "$MODEL_ID" --host 127.0.0.1 --port "$PORT" \
    --max-model-len 8192 --gpu-memory-utilization 0.90 --max-num-seqs 64 $VLLM_ARGS \
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
    cmd=("$PYTHON" -m pipeline.run_models --batch "$BATCH" --model "$ALIAS" "${PLAN[@]}")
else
    cmd=("$PYTHON" -m pipeline.run_judge --batch "$BATCH" --judge "$ALIAS")
fi
cmd+=(--base-url "http://localhost:$PORT/v1" --allow-real-calls --workers "$WORKERS")
"${cmd[@]}"
status=$?

# 7. Stop the server and pass on the exit code of the stage.
stop_server
exit "$status"
