#! /bin/sh
echo -n "-"
if test -w "$1"; then
  echo -n "w"
else
  echo -n "-"
fi
if test -r "$1"; then
  echo -n "r"
else
  echo -n "-"
fi
if test -x "$1"; then
  echo  "x"
else
  echo  "-"
fi