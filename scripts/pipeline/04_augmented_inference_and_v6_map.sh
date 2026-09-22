#!/bin/sh
# 04_augmented_inference_and_v6_map.sh — one of the chains that produced the published models, kept as it ran.
# It expects the data layout in docs/METHODS.md (NONNA tiles, channels and weights in the working directory)
# and writes its outputs there. Run from anywhere: paths resolve against the repository root.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# After chain8: 4-fold test-time-augmented national inference for the three existing full-data members, then the six-member v6 map.
cd "$ROOT"; export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
until grep -q CHAIN_DONE pipeline_8.log 2>/dev/null; do sleep 300; done
echo "START $(date)" >> pipeline_9.log
V5_BW=8 V5_TTA=4 V5_CKPT=v5_small.pt V5_OUT=national_base_tta_out python3 "$ROOT/src/inference/national_v5.py" > national_base_tta.log 2>&1; echo "INFER_base_tta $(date) $(ls national_base_tta_out | wc -l)" >> pipeline_9.log
V5_BW=8 V5_TTA=4 V5_CKPT=v5_small_ctlall.pt V5_OUT=national_ctl_tta_out python3 "$ROOT/src/inference/national_v5.py" > national_ctl_tta.log 2>&1; echo "INFER_ctl_tta $(date) $(ls national_ctl_tta_out | wc -l)" >> pipeline_9.log
V5_BW=8 V5_TTA=4 V5_S1=1 V5_CKPT=v5_small_s1all.pt V5_OUT=national_s1_tta_out python3 "$ROOT/src/inference/national_v5.py" > national_s1_tta.log 2>&1; echo "INFER_s1_tta $(date) $(ls national_s1_tta_out | wc -l)" >> pipeline_9.log
V6_MEMBERS=national_base_tta_out,national_ctl_tta_out,national_s1_tta_out,national_seed1_out,national_seed2_out,national_seed3_out V6_OUT=national_v6_out python3 "$ROOT/src/inference/ensemble_v6.py" > ensemble_v6_tta.log 2>&1; echo "ENSEMBLE6 $(date) $(tail -1 ensemble_v6_tta.log)" >> pipeline_9.log
echo "CHAIN_DONE $(date)" >> pipeline_9.log
