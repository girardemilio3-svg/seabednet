#!/bin/sh
# v6 map: two full-data models (all soundings, no temporal blanking) with the new recipe, with and without winter radar; national inference for both; 3-model ensemble.
cd ; export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
echo "START $(date)" >> chain_spark7.log
COMMON='V5_CORPUS=tiles_nat:100:3857,tiles10:10:3857 V5_SIZE=small V5_STEPS=4000 V5_BATCH=8 V5_WORKERS=6 V5_LR=2e-4 V5_CUDA_FRAC=0.45'
rm -f v5_small_ctlall.pt v5_small_s1all.pt
env $COMMON V5_AUX=0 V5_CKPT=v5_small_ctlall.pt python3 v5_train.py > v5_ctlall.log 2>&1; echo "TRAIN_ctlall $(date)" >> chain_spark7.log
env $COMMON V5_S1=1 V5_CKPT=v5_small_s1all.pt python3 v5_train.py > v5_s1all.log 2>&1; echo "TRAIN_s1all $(date)" >> chain_spark7.log
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
V5_BW=8 V5_CKPT=v5_small_ctlall.pt V5_OUT=national_ctl_out python3 national_v5.py > national_ctl.log 2>&1; echo "INFER_ctl $(date) $(ls national_ctl_out | wc -l)" >> chain_spark7.log
V5_BW=8 V5_S1=1 V5_CKPT=v5_small_s1all.pt V5_OUT=national_s1_out python3 national_v5.py > national_s1.log 2>&1; echo "INFER_s1 $(date) $(ls national_s1_out | wc -l)" >> chain_spark7.log
python3 ensemble_v6.py > ensemble_v6.log 2>&1; echo "ENSEMBLE $(date) $(tail -1 ensemble_v6.log)" >> chain_spark7.log
echo "CHAIN_DONE $(date)" >> chain_spark7.log
