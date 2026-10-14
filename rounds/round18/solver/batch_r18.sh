#!/bin/bash
mkdir -p "$(dirname "$0")/work"; cd "$(dirname "$0")/work"
OUT=summary_arr.txt; : > $OUT
for k in B D; do
 for lw in 6 5; do
  for arr in 1234 1243 1324 1342 1423 1432; do
   for add in 0 111 9889; do
    j=a_${k}_lw${lw}_${arr}_${add}.job
    if [ $lw = 6 ]; then python3 -I ../mkjob2.py $k lin $j "LW 6" "LIMIT 100" "ARR $arr" "ADD $add"; else python3 -I ../mkjob2.py $k lin $j "LW 5" "ARR $arr" "ADD $add"; fi
    ../june_sa $j ${j%.job}.out 12 1200000 5 10 2>/dev/null
    echo "$k lw$lw arr$arr add$add $(head -1 ${j%.job}.out)" >> $OUT
   done
  done
 done
done
# vowel-major / mixed single table via sa2
for k in B D; do
 for cw in 17 19 20; do
  j=v_${k}_cw${cw}.job
  python3 -I ../mkjob2.py $k lin $j "NTAB 1" "MAJ -1 -1" "LW 6" "CW $cw" "LIMIT 100"
  ../june_sa2 $j ${j%.job}.out 16 1500000 5 10 2>/dev/null
  echo "$k sa2 cw$cw $(head -1 ${j%.job}.out)" >> $OUT
 done
done
echo DONE >> $OUT
