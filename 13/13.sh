#!/bin/sh
sum=0
j=0
while [ $j -lt 10 ]
do
    sum=$(( sum + j ))
    j=$(( j + 1 ))
    echo $sum
done
exit