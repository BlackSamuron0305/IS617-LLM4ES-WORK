#!/bin/bash
# Submit N shards of one run, each as a chain of D identical 30-minute jobs.
# Each job resumes where the one before stopped; once everything is done the later jobs exit at
# once without starting the server (run_vllm.sbatch checks the plan first). Written 2026-11-01.
#
#   cluster/submit_chain.sh ALIAS MODEL_PATH BATCH_BASE N_SHARDS CHAIN_DEPTH PARTITION "EXPORTS"
# EXPORTS: extra variables for run_vllm.sbatch, comma separated, for example
#   'BLOCKS=1 2 3' or 'BLOCKS=4,VARIANTS=regulation_text no_guidance'
# Real model calls: run this only with the team's approval (ALLOW_REAL_CALLS=yes is set below).
set -eu
ALIAS=$1; MODEL_PATH=$2; BASE=$3; N=$4; DEPTH=$5; PART=$6; EXTRA=${7:-}
cd "$(dirname "$0")/.."
mkdir -p logs
for ((k = 0; k < N; k++)); do
    prev=""
    for ((d = 0; d < DEPTH; d++)); do
        dep=()
        [ -n "$prev" ] && dep=(--dependency=afterany:"$prev")
        prev=$(sbatch --parsable --partition="$PART" --gres=gpu:1 --time=00:30:00 --job-name="${BASE}_s$k" \
            --exclude=uc3n088,uc3n089,uc3n107 "${dep[@]}" \
            --export="ALL,STAGE=answers,ALIAS=$ALIAS,BATCH=${BASE}_s$k,SHARD=$k/$N,MODEL_PATH=$MODEL_PATH,PYTHON_MODULE=devel/python/3.11.7-gnu-11.4,PYTHON=python3,WORKERS=64,ALLOW_REAL_CALLS=yes${EXTRA:+,$EXTRA}" \
            cluster/run_vllm.sbatch)
        echo "shard $k step $d: job $prev"
    done
done
