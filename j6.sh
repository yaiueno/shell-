#!/bin/sh
i=1
sum=0

while [ "$i" -le "$1" ]
do
    sum=$((sum + i))
    i=$((i + 2))
done

echo "$sum"
exit 0
