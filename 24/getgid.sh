#!/bin/sh
awk -F : '{print $1"="$3}' /etc/group | sort -r  -t =  -n -k 2