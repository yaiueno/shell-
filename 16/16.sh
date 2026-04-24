#!/bin/sh
i=0
j=$#
while [ $i -lt $j ]
do 
    echo -n $1
    shift 1
    i=$((i + 1))
done
echo