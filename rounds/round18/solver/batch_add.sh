#!/bin/bash
# general additive key: total K = 101*off (annealed) + ADD (enumerated 0..99), mod 10000
mkdir -p "$(dirname "$0")/work"; cd "$(dirname "$0")/work"
OUT=summary_add.txt; : > $OUT
for k in B; do
 for add in $(seq 0 99); do
  j=add_${k}_${add}.job
  python3 -I ../mkjob2.py $k lin $j "LW 6" "LIMIT 100" "ADD $add"
  ../june_sa $j ${j%.job}.out 10 1000000 5 10 2>/dev/null
  echo "$k add$add $(head -1 ${j%.job}.out)" >> $OUT
 done
done
echo DONE >> $OUT
