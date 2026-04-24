#!/bin/sh
i=0
j=$#

sum=0

while [ $i -lt $j ]
do 
    sum=$(($sum + $1))
    shift 1
    i=$((i + 1))
done
echo $sum