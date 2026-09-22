#!/bin/sh
# 03_seed_ensemble.sh — one of the chains that produced the published models, kept as it ran.
# It expects the data layout in docs/METHODS.md (NONNA tiles, channels and weights in the working directory)
# and writes its outputs there. Run from anywhere: paths resolve against the repository root.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# seed ensemble: three more full-data models (seeds 1,2,3; new recipe, no radar), national inference for each, then a 6-member v6 map.
cd "$ROOT"; export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
until grep -q CHAIN_DONE pipeline_5.log 2>/dev/null; do sleep 300; done
echo "START $(date)" >> pipeline_8.log
COMMON='V5_CORPUS=tiles_nat:100:3857,tiles10:10:3857 V5_SIZE=small V5_STEPS=4000 V5_BATCH=8 V5_WORKERS=6 V5_LR=2e-4 V5_CUDA_FRAC=0.45'
for sd in 1 2 3; do
  rm -f v5_small_seed$sd.pt; env $COMMON V5_SEED=$sd V5_CKPT=v5_small_seed$sd.pt python3 "$ROOT/src/model/v5_train.py" > v5_seed$sd.log 2>&1; echo "TRAIN_seed$sd $(date)" >> pipeline_8.log
  OMP_NUM_THREADS=2 V5_BW=8 V5_TTA=4 V5_CKPT=v5_small_seed$sd.pt V5_OUT=national_seed${sd}_out python3 "$ROOT/src/inference/national_v5.py" > national_seed$sd.log 2>&1; echo "INFER_seed$sd $(date) $(ls national_seed${sd}_out | wc -l)" >> pipeline_8.log
done
echo "CHAIN_DONE $(date)" >> pipeline_8.log
