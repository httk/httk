#!/bin/bash
#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2014 Rickard Armiento
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
#############################################################################
#
# This is a simplified version of the full httk taskmanager
#
# This version of the taskmanager assumes no other taskmanagers are running in parallel.
# It takes the current working directory as a httk task and runs it. If subtasks are created,
# they will be exectued one at a time in priority order (using recursion, starting a new
# single_job_taskmanager). When all subtasks are finished, the main task is called again,
# just as with the normal taskmanager.
#
# Recommended uses of this simplified taskmanager:
#
#  - You are in the process of developing a run script and "just want to run through this
#    task" to debug it, with all output in the console.
#
#  - You don't care for the parallelism, resource handling, and restart/continuation capability
#    of the full httk taskmanager, and just want something to put in your cluster submit
#    script that will run one task to completion with a minimum of hassle.
#
if [ "$1" == "--rename" ]; then
    RENAME=1
    export HT_TASK_STEP="$2"
else
    RENAME=0
    export HT_TASK_STEP="$1"
fi

export IDCODE="single-job-taskmgr"

if [ -z $HT_TASK_STEP ]; then
    HT_TASK_STEP=start
fi

function split {
  local SEP="$1"
  local GET="$2"
  local STR="$3"
  awk "{split(\$0,a,\"$SEP\"); print a[$GET]}" <<< "$STR"
}

SOURCE="$0"
SOURCE_DIRNAME=$(dirname "$SOURCE")
ABSOLUTE_DIR=$(cd "$SOURCE_DIRNAME"; pwd -P)
SELF="$ABSOLUTE_DIR/$(basename "$SOURCE")"

export HT_TASK_TOP_DIR=$(pwd -P)
rm -f ht.nextstep

RESULT=2
DATE="$(date +"%Y-%m-%d_%H.%M.%S")"

if [ "$RENAME" == 1 ]; then
    echo "Trying to rename source directory"
    DIRNAME=(dirname "$HT_TASK_TOP_DIR")
    BASENAME=(basename "$HT_TASK_TOP_DIR" .waitstart)
    mv "$DIRNAME/$BASENAME.waitstart" "$DIRNAME/$BASENAME.singlejob"
fi

while [ "$RESULT" -gt 1 -a "$RESULT" -lt 4 ]; do

  if [ -e "$HT_TASK_TOP_DIR/ht_steps" ]; then
      echo "==== Trying to execute ht_steps: $HT_TASK_TOP_DIR/ht_steps $HT_TASK_STEP"
      (
      mkdir -p "ht.run.$DATE"
      export HT_TASK_RUN_NAME="ht.run.$DATE"
      cd "ht.run.$DATE"
      export HT_TASK_CURRENT_DIR="$(pwd -P)"

      "$HT_TASK_TOP_DIR/ht_steps" "$HT_TASK_STEP"

      RESULT=$?
      echo "==== Job return code: $RESULT"
      exit "$RESULT"
      )
      RESULT="$?"
      if [ -e "$HT_TASK_TOP_DIR/ht.run.$DATE/ht.nextstep" ]; then
	  HT_TASK_STEP=$(cat "$HT_TASK_TOP_DIR/ht.run.$DATE/ht.nextstep")
      else
	  HT_TASK_STEP="unknown"
      fi

  elif [ -e "$HT_TASK_TOP_DIR/ht_run" ]; then
      echo "==== Trying to execute ht_run: $HT_TASK_TOP_DIR/ht_run $HT_TASK_STEP"
      (
      export HT_TASK_RUN_NAME="./"
      export HT_TASK_CURRENT_DIR="$(pwd -P)"
      "$HT_TASK_TOP_DIR/ht_run" "$HT_TASK_STEP"

      RESULT=$?
      echo "==== Job return code: $RESULT"

      exit "$RESULT"
      )
      RESULT="$?"
      if [ -e "$HT_TASK_TOP_DIR/ht.nextstep" ]; then
	  HT_TASK_STEP=$(cat "$HT_TASK_TOP_DIR/ht.nextstep")
      else
	  HT_TASK_STEP="unknown"
      fi
  fi

  if [ "$RESULT" -eq 3 ]; then
      for PRIORITY in 1 2 3 4 5; do
	  echo "==== subtasks, checking priority $PRIORITY"
	  # We only need to look for waitstart directories here, since we just spawn
	  # a new single_job_taskmanager recursively and that one WILL run the
	  # subtask into completion and rename it to *.finished. There is never going to
	  # be tasks in an ongoing status mode here.
          find "$HT_TASK_TOP_DIR" -depth -name "ht.task.*.${PRIORITY}.waitstart" | (
	      while read TASK; do
		  echo "==== Task: $TASK"
		  DIR=$(dirname "$TASK")
		  FULLNAME=$(basename "$TASK")

		  TASKSET=$(split . 3 "$FULLNAME")
		  TASKID=$(split . 4 "$FULLNAME")
		  STEP=$(split . 5 "$FULLNAME")
		  RESTARTS=$(split . 6 "$FULLNAME")
		  OWNER=$(split . 7 "$FULLNAME")
		  PRIO=$(split . 8 "$FULLNAME")
		  STATUS=$(split . 9 "$FULLNAME")

		  #TASKTYPE=$(split . 3 "$FULLNAME")
		  #TASKNAME=$(split . 4 "$FULLNAME")
		  #STEP=$(split . 5 "$FULLNAME")
		  #PRIO=$(split . 6 "$FULLNAME")
		  #RUNTYPE=$(split . 7 "$FULLNAME")

		  #mv "$TASK" "$DIR/ht.task.${TASKNAME}.${TASKTYPE}.${STEP}.${IDCODE}.${PRIO}.running"
		  mv "$TASK" "$DIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.${IDCODE}.${PRIO}.running"
		  (


		      cd "$DIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.${IDCODE}.${PRIO}.running"
		      "$SELF" "$STEP"
		  )
		  mv "$DIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.${IDCODE}.${PRIO}.running" "$DIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.none.${PRIO}.finished"
	      done
	  )
      done
  fi
done

if [ "$RENAME" == 1 ]; then
    echo "Trying to rename source directory"
    DIRNAME=(dirname "$HT_TASK_TOP_DIR")
    BASENAME=(basename "$HT_TASK_TOP_DIR" .waitstart)
    if [ "$RESULT" == "10" ];then
	mv "$DIRNAME/$BASENAME.singlejob" "$DIRNAME/$BASENAME.finished"
    else
	mv "$DIRNAME/$BASENAME.singlejob" "$DIRNAME/$BASENAME.broken"
    fi
fi

echo "==== Single job taskmanager quitting."
