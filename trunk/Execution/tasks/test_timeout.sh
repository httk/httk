#!/bin/bash

PID=$$
( trap " " TERM; sleep 3336 & wait; kill -- -$PID ) &
TIMEOUTPID=$!
sleep 3
echo hi
kill $TIMEOUTPID
