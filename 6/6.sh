#!/bin/sh

i=0
max=$(($1 / 2))
sum=0

while [ $i -lt $max ]
do
    sum=$((sum + $(($((i * 2)) + 1))))
    i=$((i + 1))
done
echo $sum