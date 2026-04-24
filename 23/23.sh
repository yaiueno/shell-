#!/bin/sh
for x in ./bar*
do
    sed 's=bgein=begin=g' "$x" > tmp.tex
    mv tmp.tex "$x"
done
echo "finish"
   