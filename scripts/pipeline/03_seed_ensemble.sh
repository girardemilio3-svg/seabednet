#!/bin/sh
# seed ensemble: three more full-data models (seeds 1,2,3; new recipe, no radar), national inference for each, then a 6-member v6 map.
cd ; export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
until grep -q CHAIN_DONE chain_spark5.log 2>/dev/null; do sleep 300; done
echo "START $(date)" >> chain_spark8.log
COMMON='V5_CORPUS=tiles_nat:100:3857,tiles10:10:3857 V5_SIZE=small V5_STEPS=4000 V5_BATCH=8 V5_WORKERS=6 V5_LR=2e-4 V5_CUDA_FRAC=0.45'
for sd in 1 2 3; do
  rm -f v5_small_seed$sd.pt; env $COMMON V5_SEED=$sd V5_CKPT=v5_small_seed$sd.pt python3 v5_train.py > v5_seed$sd.log 2>&1; echo "TRAIN_seed$sd $(date)" >> chain_spark8.log
  OMP_NUM_THREADS=2 V5_BW=8 V5_TTA=4 V5_CKPT=v5_small_seed$sd.pt V5_OUT=national_seed${sd}_out python3 national_v5.py > national_seed$sd.log 2>&1; echo "INFER_seed$sd $(date) $(ls national_seed${sd}_out | wc -l)" >> chain_spark8.log
done
echo "CHAIN_DONE $(date)" >> chain_spark8.log
