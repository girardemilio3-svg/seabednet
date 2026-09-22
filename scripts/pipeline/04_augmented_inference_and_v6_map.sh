#!/bin/sh
# After chain8: 4-fold test-time-augmented national inference for the three existing full-data members, then the six-member v6 map.
cd ; export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
until grep -q CHAIN_DONE chain_spark8.log 2>/dev/null; do sleep 300; done
echo "START $(date)" >> chain_spark9.log
V5_BW=8 V5_TTA=4 V5_CKPT=v5_small.pt V5_OUT=national_base_tta_out python3 national_v5.py > national_base_tta.log 2>&1; echo "INFER_base_tta $(date) $(ls national_base_tta_out | wc -l)" >> chain_spark9.log
V5_BW=8 V5_TTA=4 V5_CKPT=v5_small_ctlall.pt V5_OUT=national_ctl_tta_out python3 national_v5.py > national_ctl_tta.log 2>&1; echo "INFER_ctl_tta $(date) $(ls national_ctl_tta_out | wc -l)" >> chain_spark9.log
V5_BW=8 V5_TTA=4 V5_S1=1 V5_CKPT=v5_small_s1all.pt V5_OUT=national_s1_tta_out python3 national_v5.py > national_s1_tta.log 2>&1; echo "INFER_s1_tta $(date) $(ls national_s1_tta_out | wc -l)" >> chain_spark9.log
V6_MEMBERS=national_base_tta_out,national_ctl_tta_out,national_s1_tta_out,national_seed1_out,national_seed2_out,national_seed3_out V6_OUT=national_v6_out python3 ensemble_v6.py > ensemble_v6_tta.log 2>&1; echo "ENSEMBLE6 $(date) $(tail -1 ensemble_v6_tta.log)" >> chain_spark9.log
echo "CHAIN_DONE $(date)" >> chain_spark9.log
