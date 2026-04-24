#!/bin/sh
echo "<html><body>" |sed 's/<\([^>]*\)>.*/\1/'
echo "int main (void)" |sed 's:(\([a-z]*\)):\1:'
echo "int main (void)" |sed 's:.*(\([a-z]*\)):\1:'
echo "/tmp/mytest.sh.tgz" |sed 's:[^.]*\(\..*\):\1:'
#↑なぜかびっくりだめ考察してください。
echo "/tmp/mytest.sh.tgz" |sed 's=[/.]=-=g'