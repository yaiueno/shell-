#! /bin/sh
if test $1 -lt 10 ; then
    i =$(($1 + 1))
    $0 $i
else
    exho $1
fi
exit1