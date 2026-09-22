#!/bin/sh
cd "$(dirname "$0")/../.."
until grep -q CHAIN_DONE chain_spark9.log 2>/dev/null; do sleep 300; done
echo "START $(date)" >> chain_spark10.log
OMP_NUM_THREADS=4 python3 blend_map.py national_v6_out national_v6h_out > blend_v6.log 2>&1; echo "BLEND $(date) $(tail -1 blend_v6.log | cut -c1-40)" >> chain_spark10.log
echo "CHAIN_DONE $(date)" >> chain_spark10.log
