#!/bin/bash

for DIR in ht.*; do
    COUNT=$(find "$DIR" -name "ht.task.*" | wc -l)
    echo "$DIR : $COUNT"
done
