#!/bin/bash
#SBATCH --job-name=dl_pinned
#SBATCH --partition=cpu_il
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16gb
#SBATCH --time=02:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#
# Download ONE model at the exact revision pinned in experiment/models.csv (or judge_models.csv),
# into $WS/models/<dir>. Unlike ~/llm/download_one.sbatch it does not take the newest version.
#   sbatch cluster/download_model.sbatch google/gemma-4-31B-it gemma-4-31b-it <40-character-commit-hash>
# Written on 2026-11-01. Not a real model call; it only copies files. Ask the user before submitting.
source "$HOME/llm/env.sh"
module load devel/miniforge/25.3.1-python-3.12
set -u

REPO="${1:?usage: download_model.sbatch HF_REPO DEST_DIR_NAME REVISION}"
DIR="${2:?missing destination directory name}"
REV="${3:?missing revision (40-character commit hash)}"
DEST="$WS/models/$DIR"

echo "node=$(hostname) repo=$REPO revision=$REV dest=$DEST started=$(date)"
if [ -f "$DEST/config.json" ]; then
  echo "ALREADY_PRESENT $DEST"
  exit 0
fi
mkdir -p "$WS/models"
python - "$REPO" "$DEST" "$REV" <<'PY' || { echo "DOWNLOAD_FAILED $REPO"; exit 1; }
import sys
from huggingface_hub import snapshot_download
repo, dest, rev = sys.argv[1:4]
print("DOWNLOAD_DONE", snapshot_download(repo_id=repo, local_dir=dest, revision=rev, max_workers=8))
PY
du -sh "$DEST"
head -1 "$DEST/.cache/huggingface/download/config.json.metadata"
echo "DOWNLOAD_OK $REPO finished=$(date)"
