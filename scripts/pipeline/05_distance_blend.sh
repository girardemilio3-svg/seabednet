#!/bin/sh
# 05_distance_blend.sh — one of the chains that produced the published models, kept as it ran.
# It expects the data layout in docs/METHODS.md (NONNA tiles, channels and weights in the working directory)
# and writes its outputs there. Run from anywhere: paths resolve against the repository root.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
until grep -q CHAIN_DONE pipeline_9.log 2>/dev/null; do sleep 300; done
echo "START $(date)" >> pipeline_10.log
OMP_NUM_THREADS=4 python3 "$ROOT/src/inference/blend_map.py" national_v6_out national_v6h_out > blend_v6.log 2>&1; echo "BLEND $(date) $(tail -1 blend_v6.log | cut -c1-40)" >> pipeline_10.log
echo "CHAIN_DONE $(date)" >> pipeline_10.log
