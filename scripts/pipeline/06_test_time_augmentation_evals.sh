#!/bin/sh
# 06_test_time_augmentation_evals.sh — one of the chains that produced the published models, kept as it ran.
# It expects the data layout in docs/METHODS.md (NONNA tiles, channels and weights in the working directory)
# and writes its outputs there. Run from anywhere: paths resolve against the repository root.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"; export OMP_NUM_THREADS=1
TE_TTA=4 TE_BW=4 V5_SIZE=small V5_CKPT=v5_small_ctlfull.pt TAG=temporal_ctlfull_tta4 python3 "$ROOT/src/eval/temporal_eval.py" corridor_blocks.txt > temporal_eval_ctlfull_tta4.log 2>&1; echo "TTA4_DONE $(date)" >> chain_tta_eval.log
TE_TTA=8 TE_BW=4 V5_SIZE=small V5_S1=1 V5_CKPT=v5_small_s1full.pt TAG=temporal_s1full_tta python3 "$ROOT/src/eval/temporal_eval.py" corridor_blocks.txt > temporal_eval_s1full_tta.log 2>&1; echo "TTA_S1_DONE $(date)" >> chain_tta_eval.log
echo "CHAIN_DONE $(date)" >> chain_tta_eval.log
