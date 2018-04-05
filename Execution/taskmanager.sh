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
#  TODO: How to enforce an overall priority order?
#
#  Usage: taskmanager.sh [type of taskmanager] [resource file]
#
#   Optional category directories (taskmanager uses them if a run resides in them)
#
#   ht.source : A source directory from which tasks can be created
#   ht.running : A directory for ongoing tasks
#   ht.finshed : A directory collecting finished tasks
#   ht.broken : A directory collecting broken tasks
#
#   Statues of waiting, ongoing, etc, tasks:
#
#   ht.waiting : Task that wants to be (re)executed. 
#   ht.finished: Finished task, not to be further touched
#   ht.running: Task that is currently running - or possibly stale, 
#                     (if ctime has not been updated in too long)
# 
#   Full breakdown:
#   ht.task.type.id.step.1.running
#     ht.task = obligatory prefix
#     type = type of job, allows for differentiation where only some taskmanagers deal with some jobs
#     id = task unique id 
#     step = the step the task is at right now
#     1 = priority number, 1-5, 1 is highest
#
#     running = task status
#
#   Statuses of rejected tasks:
#
#   ht.task.*.timeout : a run that was killed by the set timeout, needs investigation, 
#                       or maybe just longer runtime.
#   ht.task.*.dead    : task has been declared dead, not to be run again
#   ht.task.*.overrun : task has been restarted too many times
#   ht.task.*.underrun: task finished too quickly
#   ht.task.*.unknown : task in unknwon status, needs manual supervision
#   ht.task.*.broken  : task is in a broken state, usually because of user error
#
#   if you need to have subdirectories in your task directories that you do not want
#   the taskmanager to mess with at all, name them ht.ignore.(something)
#

# Check if the present process runs in its own process group,
# if not, restart the job so that it does.

################### OPTIONS ####################################

# Parameters that can be set both by environment or as arguments
export HT_TASKMGR_TIMEOUT="$HT_TASKMGR_TIMEOUT"
export HT_TASKMGR_WRAP="$HT_TASKMGR_WRAP"
export HT_TASKMGR_SET="$HT_TASKMGR_SET"
export HT_TASKMGR_ROOTDIR="$HT_TASKMGR_ROOTDIR"
BZIPLOG=1

# Command line argument handling
while [ -n "$1" ]; do
    case $1 in
	-r|--norestart)
	    NORESTART=1
	    shift 1
	    ;;
        -w|--wrap)
            HT_TASKMGR_WRAP=$2
	    # Never shift > 1, as that shifts 0 if there is no arg...
	    shift 1
	    shift 1
            ;;
        -s|--set)
            HT_TASKMGR_SET=$2
	    shift 1
	    shift 1
            ;;
        -b|--no-bzip2log)
            BZIPLOG=0
	    shift 1
            ;;
        -d|--rootdir)
            HT_TASKMGR_ROOTDIR=$2
	    shift 1
	    shift 1
            ;;
        -t|--timeout)
            HT_TASKMGR_TIMEOUT=$2
	    shift 1
	    shift 1
            ;;
        *)
	    echo "Usage:"
	    echo "  $0/taskmanager.sh -h : this help"
	    echo "  $0/taskmanager.sh [-w wrap_program] [-s set]"
	    echo ""
	    exit 0
            ;;
    esac
done

if [ -z "$HT_TASKMGR_SET" ]; then
    HT_TASKMGR_SET="any"
fi

if [ -z "$HT_TASKMGR_TIMEOUT" ]; then
    # 6h ought to be enough for anybody
    HT_TASKMGR_TIMEOUT="21600"
fi

if [ -n "$HT_TASKMGR_ROOTDIR" ]; then
    cd "$HT_TASKMGR_ROOTDIR"
fi
HT_TASKMGR_ROOTDIR="$(pwd -P)"


#############################################################
# Make sure taskmanager runs in its own process group

kill -0 -$$ >/dev/null 2>&1
if [ "$?" != "0" ]; then
    if [ "$NORESTART" == 1 ];then
	echo "taskmanager.sh: option given to not restart, but not running in a process group. Cannot continue." >&2
	exit 1
    else
	echo "taskmanager.sh: not running in own process group. Restarting to fix this." >&2
	# Let this process stay around as the parent of the real taskmanager to handle
	# a rather specific corner case: if this process was started under the pretense
	# that if the real process group gets killed, then this process (and the child process =
	# the real taskmanager) should also get killed. This does not work if 
	# we had done 'exec setsid', since then the new taskmanager process would be 
	# detached from the original process group.
	KILLPID=""
	trap "if [ -n \"\$KILLPID\" ]; then kill \"\$KILLPID\"; fi" EXIT
	setsid "$0" --norestart "$@" &
	KILLPID="$!"
	wait
	RESULT="$?"
	trap - EXIT
	exit "$RESULT"
    fi
else
    echo "Vasp_run_controlled: running in process group -$$" >&2
fi

export TASKMGRPID=$$
#######################################################################
# TODO: Make taskmanager.sh aware of actual nodes and job requirements.

shopt -s extglob

TOTAL_NODES=1
FREE_NODES=1

function split {
  local SEP=$1
  local GET=$2
  local STR=$3
  awk "{split(\$0,a,\"$SEP\"); print a[$GET]}" <<< "$STR"
}

function FILE_MATCH {
    local GLOB=$(basename "$1")
    local DIR=$(dirname "$1")
    test -n "$(cd "$DIR"; find . -mindepth 1 -maxdepth 1 -name "$GLOB" -print -quit)"
    return "$?"
}

function PATH_PREFIX {
    local FROM="$1"
    local PREFIX="$2"
    local COUNT=0
    while [ -e "${PREFIX}${COUNT}" ]; do
	COUNT=$((COUNT+1))
    done
    if [ "$FROM" == "-d" ]; then
	mkdir "${PREFIX}${COUNT}" 
    elif [ "$FROM" == "-f" ]; then
	touch "${PREFIX}${COUNT}" 
    else
	mv "$FROM" "${PREFIX}${COUNT}"
    fi
    if [ "$?" == 0 ]; then
	echo "${PREFIX}${COUNT}" 
    else
	return "$?"
    fi
}

function ATOMIC_START {
    local TMPDIR=$(PATH_PREFIX -d ht.tmp.atomic.)
    cd "$TMPDIR"
}

function ATOMIC_MV {
    local FROM="$1"
    local TO="$2"
    echo "$2" > ht.atommv."$1"
}

function ATOMIC_END {
    local ATOMDIR=$(basename "$(pwd -P)")
    cd ..
    # This is the atomic step, before this, all gets ignored, after this, we are at the next step.
    local OUTDIR=$(PATH_PREFIX "$ATOMDIR" ht.atomic.)
    #
}

function ATOMIC_EXEC {
    if FILE_MATCH "ht.tmp.atomic.*"; then
	rm -rf ht.tmp.atomic.*
    fi

    if FILE_MATCH "ht.atomic.*"; then
	for ATOMDIR in ht.atomic.*; do
	    (cd "$ATOMDIR"; find . -maxdepth 1 -name "ht.atommv.*") | sed -e 's/^.\/ht.atommv.//' | xargs -i sh -c "mv {} \$(cat \"$ATOMDIR/ht.atommv.{}\"); rm -f \"$ATOMDIR/ht.atommv.{}\""
	    if FILE_MATCH "$ATOMDIR/*"; then
		mv "$ATOMDIR"/* .
	    fi
	    rmdir "$ATOMDIR"
	done
    fi

    if FILE_MATCH "ht.tmp.atomic.*"; then
	rm -rf ht.tmp.atomic.*
    fi
}

function TASKMGR_HEARTBEAT {
    mkdir -p "$HT_TASKMGR_ROOTDIR"/ht.taskmgrstats
    touch ht.taskmgrstats/"alive.$IDCODE"
}

trap "echo \"TASKMANAGER exiting, making sure everything is shut down\"; kill -- -$TASKMGRPID; exit 100;" EXIT
#trap "trap - TERM; echo \"TASKMANAGER got SIGTERM signal, shutting down\"; kill -- -$TASKMGRPID; exit 100;" TERM
#trap "trap - INT; echo \"TASKMANAGER got SIGINT signal, shutting down\"; kill -- -$TASKMGRPID; exit 100;" INT

IDCODE="tskmgr-$(date +"%Y-%m-%d_%H_%M_%S_$RANDOM")"

## Script begins

# Write a log message on stderr
function logmsg {
    local LEVEL=$1
    local MSG=$2

    if [ "$LEVEL" -lt 20 ]; then
	echo "[$IDCODE|$(date +"%Y-%m-%d %H:%M:%S")] $2" >&2
    fi
}

# Write out an error msg 
function errmsg {
    local MSG=$1
    echo "[$IDCODE|$(date +"%Y-%m-%d %H:%M:%S")] ERROR!: $1" >&2
}

function check_requirements {
    # 2 = requirements check out
    # 0 = requirements does not check out, don't try to run this
    local DIR=$1
    return 2
}

function check_max_requirements {
    # 2 = requirements check out
    # 0 = requirements does not check out, don't try to run this
    local DIR=$1
    return 2
}

function check_restartable {
    # 2 = restartable
    # 0 = non-restartable
    local DIR=$1
    if [ -e "$DIR/ht.state.running" -a -e "$DIR/ht_restart.sh" ]; then
	return 2
    fi
    return 0
}

function find_last_versionnbr {
    local DIR=$1
    local TASKNAME=$2
    local LAST=""
    local LASTNBR=""
    local FILES=""

    FILES=( $DIR/run.${TASKNAME}.*.old )
    if [ -e "${FILES[0]}" ]; then
	NEXT=$(printf "%s\n" "${FILES[@]}" | awk -F. '{AR[$(NF-2)]=1} END {N=asorti(AR,ARSORT); print ARSORT[N];}')
    else
	NEXT=0
    fi
    echo "${NEXT}"
    return 0
}

function compress {
    local DIR=$1
    find "$DIR" -type f -not -name \*.bz2 -exec bzip2 \{\} \;
}

function copy_state {
    local FROM=$1
    local TO=$2
    #local DIR="$(dirname "$TASK")"
    #local NAME="$(basename "$TASK")"
    #local SAFENAME="${NAME#ht\.task\.}"

    ## Copy everything from one dir to another, but ignore any ht.* files
    #for $FILE in $TASK/*; do
#	if [[ $FILE == ht.state.* ]]; then
#	    continue
#	fi
#
#	rm -rf "$DIR/run.task.$SAFENAME/$FILE"
#
 #   done
#
    #find "$FROM" -mindepth 1 -maxdepth 1 -type f -not -name ht.\* -print0 -exec cp -rp \{\} "$TO" \;

    find "$FROM" -not -name ht.\* -print0 | cpio -pmd0 "$TO"
}

function adopt {
    local SRC=$1
    logmsg 1 "Adopt run: attempting to adopt run: $SRC"

    local DIR=$(dirname "$SRC")
    #local PARENTDIR=$(dirname "$DIR")
    #local DIRNAME=$(basename "$DIR")

    local FULLNAME=$(basename "$SRC")

    local TASKSET=$(split . 3 "$FULLNAME")
    local TASKID=$(split . 4 "$FULLNAME")
    local STEP=$(split . 5 "$FULLNAME")
    local RESTARTS=$(split . 6 "$FULLNAME")
    local OWNER=$(split . 7 "$FULLNAME")
    local PRIO=$(split . 8 "$FULLNAME")
    local STATUS=$(split . 9 "$FULLNAME")
    
    local OUTDIR="$DIR"

    if [ "${DIR:0:15}" = "ht.waitstart/1/" -o "${DIR:0:15}" = "ht.waitstart/2/" -o \
	 "${DIR:0:15}" = "ht.waitstart/3/" -o "${DIR:0:15}" = "ht.waitstart/4/" -o \
	 "${DIR:0:15}" = "ht.waitstart/5/" ]; then
	OUTDIR="ht.waitstart/${DIR:15}"
    fi

    # Handle a ht.waiting / ht.running dir in the path and set outdir accordingly

    local PREPREDIR="${OUTDIR%ht\.task.*}"
    if [ "$PREPREDIR" == "$OUTDIR" ]; then
	PREPREDIR=""
    fi
    local RESTDIR="${OUTDIR#$PREPREDIR}"

    local PREDIR="${RESTDIR%+(ht\.waiting|ht\.running|ht\.waitstart)*}"
    local POSTDIR=""
    if [ "$PREDIR" != "$RESTDIR" ]; then 
	POSTDIR="${RESTDIR#$PREDIR+(ht\.waiting|ht\.running|ht\.waitstart)}"
	OUTDIR="${PREPREDIR}${PREDIR}ht.running${POSTDIR}"
    fi

    logmsg 1 "NEW CHECK ::: :$DIR : $PREPREDIR : $RESTDIR : $PREDIR : $POSTDIR : $OUTDIR :"

    if [ "$STATUS" == "running" ]; then
	RESTARTS="$((RESTARTS+1))"
    fi

    # ht.task.<taskset>.<taskid>.<step>.<restarts>.<owner>.<prio>.<status>
    if [ -e "$OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.${IDCODE}.${PRIO}.running" ]; then
	errmsg "Adopt run: My running directory already exist! This should never happen, skipping to next job. Offending directory was: $OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.${IDCODE}.${PRIO}.running"
	return 1
    fi

    # Must have this here, since some filesystem does not update even the ctime on mv
    touch -c "$DIR/$FULLNAME" > /dev/null 2>&1

    mkdir -p "$OUTDIR"	
    mv "$DIR/$FULLNAME" "$OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.${IDCODE}.${PRIO}.running" > /dev/null 2>&1
    if [ "$?" != "0" ]; then
	logmsg 1 "Adopt run: $SRC lost to other process in race condition. Finding another ht.task."
	return 2
    fi

    # Overly safe racing condition protection in possibly lossy non-locking networked file system
    sleep 1

    logmsg 1 "Adopt run: Double-checking that rollback directory was not lost to race condition: $SRC."
    if [ ! -d "$OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.${IDCODE}.${PRIO}.running" ]; then
	logmsg 1 "Adopt run: $SRC lost to other process in race condition. Finding another ht.task."
	return 2
    fi

    if [ "$RESTARTS" -gt "10" ]; then
	logmsg 1 "Too many restarts, putting this job in a broken state."
	echo "Too many restarts!" >> "$OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.${IDCODE}.${PRIO}.running/ht.reason"
	mv "$OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.${IDCODE}.${PRIO}.running" "$OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.${IDCODE}.${PRIO}.stopped" 
	return 2
    fi

    echo "$OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.${IDCODE}.${PRIO}.running"
    return 0
}

function start_run {
    local TASK="$1"

    local DIR=$(dirname "$TASK")
    local DIRNAME=$(basename "$DIR")
    local PARENTDIR=$(dirname "$DIR")

    local FULLNAME=$(basename "$TASK")	    
    local TASKSET=$(split . 3 "$FULLNAME")
    local TASKID=$(split . 4 "$FULLNAME")
    local STEP=$(split . 5 "$FULLNAME")
    local RESTARTS=$(split . 6 "$FULLNAME")
    local OWNER=$(split . 7 "$FULLNAME")
    local PRIO=$(split . 8 "$FULLNAME")
    local STATUS=$(split . 9 "$FULLNAME")

    # Handle a ht.waiting / ht.running dir in the path and set outdir accordingly
    local PREPREDIR="${DIR%ht\.task.*}"
    if [ "$PREPREDIR" == "$DIR" ]; then
	PREPREDIR=""
    fi
    local RESTDIR="${DIR#$PREPREDIR}"

    local PREDIR="${RESTDIR%+(ht\.waiting|ht\.running)*}"
    local POSTDIR=""
    local MOVEDIR=0
    if [ "$PREDIR" != "$RESTDIR" ]; then 
	POSTDIR="${RESTDIR#$PREDIR+(ht\.waiting|ht\.running)}"
	MOVEDIR=1
    fi
    EXOUTDIR="${PREPREDIR}${PREDIR}ht.example${POSTDIR}"
    #logmsg 1 "TEST2:$DIR : $PREPREDIR : $RESTDIR : $PREDIR : $POSTDIR : $EXOUTDIR :"

    export HT_TASK_TOP_DIR="$(cd "$TASK"; pwd -P)"
    export HT_TASK_STEP="$STEP"
    cd "$HT_TASK_TOP_DIR"

    if [ -e "$HT_TASK_TOP_DIR/ht_steps" ]; then
	logmsg 1 "Trying to execute ht_steps: $HT_TASK_TOP_DIR/ht_steps $HT_TASK_STEP"
	PROGRAM="../ht_steps"
	mkdir -p "ht.run.current"
	cd "ht.run.current"
	export HT_TASK_RUN_NAME="ht.run.current"
	export HT_TASK_CURRENT_DIR="$(pwd -P)"
    else
	logmsg 1 "Trying to execute ht_run: $HT_TASK_TOP_DIR/ht_run $HT_TASK_STEP"	
	PROGRAM="ht_run"
	export HT_TASK_RUN_NAME="."
	export HT_TASK_CURRENT_DIR="$(pwd -P)"
    fi

    if [ -e ht.nextstep ]; then
	HT_TASK_STEP=$(cat ht.nextstep)
    fi
    
    if [ "$HT_TASK_STEP" != "ht_finished" -a "$HT_TASK_STEP" != "ht_broken" ]; then

	# Allow run to run safely in a setsid, but make sure it gets killed if we get a signal
	(
	    KILLPID=""
	    trap "if [ -n \"\$KILLPID\" ]; then kill -TERM -- -\"\$KILLPID\"; (sleep 10; kill -KILL -- -\"\$KILLPID\") & fi" EXIT
	    trap " " TERM
	    # WARNING: setsid can behave extremely wierd if invoked as a process group leader. That should
	    # not be an issue here, however. 
	    if [ -n "$HT_TASKMGR_WRAP" ]; then
		setsid "$HT_TASKMGR_WRAP" "$PROGRAM" "$HT_TASK_STEP" >> "$HT_TASK_TOP_DIR/ht.taskmgr.stdout" 2>&1 &
	    else
		setsid "$PROGRAM" "$HT_TASK_STEP" >> "$HT_TASK_TOP_DIR/ht.taskmgr.stdout" 2>&1 &
	    fi
	    KILLPID="$!"
	    wait "$KILLPID"
	    RETURNCODE="$?"
	    logmsg 1 "Run returncode: $RETURNCODE"
	    if [ "$RETURNCODE" -le 127 ]; then
		trap - EXIT
		exit "$RETURNCODE"
	    fi
	    kill -TERM -- -"$KILLPID"
	    (sleep 10; kill -KILL -- -"$KILLPID") &
	    trap - EXIT
	    wait "$KILLPID"
	    exit 43
	) &
	RUNPID=$!    
	
	WATCHDOGPID=$( 
	    (
		trap " " TERM
		sleep "$HT_TASKMGR_TIMEOUT" &
		SP=$!
		wait
		RETCODE=$?
		logmsg 1 "Watchdog wakes up, with return code=$RETCODE"
		if [ "$RETCODE" -gt "127" ]; then
	    	    kill -TERM "$SP" >/dev/null 2>&1; 
		fi
		kill -TERM "${RUNPID}"
		#/bin/kill -TERM -- "-${RUNPID}"
		#sleep 60
		#if kill -0 -"$RUNPID" >/dev/null 2>&1; then
		#    /bin/kill -KILL -- "-${RUNPID}"
		#fi
		#logmsg 1 "Watchdog has killed job: $NEXTTASK"
		exit 42
	    ) >/dev/null 2>&1 & echo $!)
	
	CHECKPOINTPID=$(
	    (
		COUNT=0
		while [ 0 == 0 ]; do
		    sleep 150
		    touch -c "$HT_TASK_TOP_DIR"
		done
	    ) >/dev/null 2>&1 & echo $!)
	
	#while [ 0 == 0 ]; do
	logmsg 1 "Waiting for run to finish"
	wait "$RUNPID"
	RESULT="$?"
	logmsg 1 "Woken up from run wait, return code $RESULT"
	if [ "$RESULT" -ge 128 ]; then
	    logmsg 1 "Waiting for run process to actually finish."
	    wait "$RUNPID"
	    RESULT="$?"
	    logmsg 1 "Return code: $RESULT"
	fi
	    
	kill "$CHECKPOINTPID"
	
	if kill "$WATCHDOGPID" >/dev/null 2>&1; then
	    logmsg 1 "Job $NEXTTASK finished ok, watchdog killed."
	else
	    logmsg 1 "Job $NEXTTASK was killed by the watchdog."
	    RESULT=99
	fi
	
	logmsg 1 "Job completed, return code: $RESULT"
    else
	# Below is to handle a corner case where a run is broken after having commited an
	# atomic transaction specifying either ht_finished or ht_broken, in that case
	# we avoid re-running the job, but rather just act on those statues.
	if [ "$HT_TASK_STEP" != "ht_finished"]; then
	    RESULT=10
	fi
	if [ "$HT_TASK_STEP" != "ht_broken" ]; then	
	    RESULT=4
	fi
    fi

    # We should already be in the right directory, but we cd there
    # anyway to handle a corner case where a wrapper script replaces
    # the run directory (e.g., because it needs to copy it somewhere
    # else and run it there, and then copy it back.)
    cd "$HT_TASK_CURRENT_DIR"

    if [ -e "ht.nextstep" ]; then
	NEXTSTEP=$(cat ht.nextstep)
    else
	NEXTSTEP="unknown"
    fi

    cd "$HT_TASKMGR_ROOTDIR"	

    if [ "$RESULT" == "10" -o \( "$PROGRAM" == "ht_run" -a "$RESULT" == "0" \) ]; then
	logmsg 1 "Return code 10 (or 0 for ht_run) means the run completed successfully."
	# Task finished
	(
	    rm -f "$TASK"/ht.run.current/ht.taskmgr.stdout.bz2
	    cp "$TASK"/ht.taskmgr.stdout "$TASK"/ht.run.current/ht.taskmgr.stdout
	    if [ "$BZIPLOG" == "1" ]; then
		bzip2 "$TASK"/ht.run.current/ht.taskmgr.stdout
	    fi

	    DATE="$(date +"%Y-%m-%d_%H.%M.%S")"
	    cd "$TASK"
	    ATOMIC_START
	    ATOMIC_MV ht.run.current "ht.run.$DATE"
	    # Make sure the old stdout log gets removed
	    ATOMIC_MV ht.taskmgr.stdout ht.tmp.atomic.taskmgr.stdout
	    ATOMIC_END
	    ATOMIC_EXEC
	)
	if [ "$MOVEDIR" == 1 ]; then
	    OUTDIR="${PREPREDIR}${PREDIR}ht.finished${POSTDIR}"
	    mkdir -p "$OUTDIR"
	else
	    OUTDIR="$DIR"
	fi
	mv "$TASK" "$OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.unclaimed.${PRIO}.finished"
    elif [ "$RESULT" == "2" ]; then
	# Next step
	logmsg 1 "Return code 2 means the run is ready for the next step: $NEXTSTEP"
	mv "$TASK" "$DIR/ht.task.${TASKSET}.${TASKID}.${NEXTSTEP}.${RESTARTS}.unclaimed.${PRIO}.waitstep"
    elif [ "$RESULT" == "3" ]; then
	# Subtasks
	logmsg 1 "Return code 3 means the run want to wait for subtasks before next step: $NEXTSTEP"
	mv "$TASK" "$DIR/ht.task.${TASKSET}.${TASKID}.${NEXTSTEP}.${RESTARTS}.unclaimed.${PRIO}.waitsubtasks"
    elif [ "$RESULT" == "4" ]; then
	# Broken
	logmsg 1 "Return code 4 means the run announces itself to be in a broken state."
	echo "Task gave 'broken' as return code." >> "$TASK/ht.reason"
	if [ "$MOVEDIR" == 1 ]; then
	    OUTDIR="${PREPREDIR}${PREDIR}ht.broken${POSTDIR}"
	    mkdir -p "$OUTDIR"
	else
	    OUTDIR="$DIR"
	fi
	mv "$TASK" "$OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.unclaimed.${PRIO}.broken"
    elif [ "$RESULT" == "99" ]; then
	# Timeout
	logmsg 1 "The run timed out, so, mark it as such."
	echo "Task timed out." >> "$TASK/ht.reason"
	if [ "$MOVEDIR" == 1 ]; then
	    OUTDIR="${PREPREDIR}${PREDIR}ht.timeout${POSTDIR}"
	    mkdir -p "$OUTDIR"
	else
	    OUTDIR="$DIR"
	fi
	mv "$TASK" "$OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.unclaimed.${PRIO}.timeout"
    else
	# Stopped
	logmsg 1 "The run returned a non-defined error code ($RESULT), this usually means something unexpected has happened in the runscript. We set the job in a stopped state."
	echo "Task returned non-defined error code ($RESULT). This usually means something unexpected have returned an error." >> "$TASK/ht.reason"
	if [ "$MOVEDIR" == 1 ]; then
	    OUTDIR="${PREPREDIR}${PREDIR}ht.stopped${POSTDIR}"
	    mkdir -p "$OUTDIR"
	else
	    OUTDIR="$DIR"
	fi
	mv "$TASK" "$OUTDIR/ht.task.${TASKSET}.${TASKID}.${STEP}.${RESTARTS}.unclaimed.${PRIO}.stopped"
    fi
}

function find_next_task {
    # Return codes:
    #   0: All is well, job has been printed out on stdout
    #   2: Could not find a task now, but we should re-try later
    #   3: Could not find any task to do, I'm finished

    PRIORITY=$1

    logmsg 1 "Find next task: search for a task (priority=$PRIORITY)"	

    RETURN=3

    #ALL=$(find . -depth \( -cmin +10 -name "ht.task.*.$PRIORITY.running" \) -o \( -name "ht.task.*.$PRIORITY.subruns" \) -o -name "ht.task.*.$PRIORITY.waiting")

    #find . -depth \( -cmin +10 -name "ht.task.*.$PRIORITY.running" \) -o \( -name "ht.task.*.$PRIORITY.subruns" \) -o -name "ht.task.*.$PRIORITY.waiting" | (
    # cmin or mmin?

    #( find . -depth \( -mmin +15 -name "ht.task.*.$PRIORITY.running" \) -o \( -name "ht.task.*.$PRIORITY.subruns" \) -o \( -name "ht.task.*.unclaimed.$PRIORITY.waitstep" \)  -o \( -name "ht.tmp.unpack.*" \); find . -depth \( -name "ht.task.*.unclaimed.$PRIORITY.waitstart" \) ) | (

    #( find . \( -name "ht.tmp.*" -prune \) -a \( \( -mmin +15 -name "ht.task.*.$PRIORITY.running" -prune \) -o \( -name "ht.task.*.$PRIORITY.subruns" \) -o \( -name "ht.task.*.unclaimed.$PRIORITY.waitstep" -prune \) \); find . \( -name "ht.task.*" -prune \) -a \( -name "ht.task.*.unclaimed.$PRIORITY.subruns" \) | xargs find "{}" \( -name "ht.task.*" -prune \) -a \( -name "ht.task.*.unclaimed.$PRIORITY.waitstart" \); find . \( -name "ht.task.*" -prune \) -a \( -name "ht.task.*.unclaimed.$PRIORITY.waitstart" \) ) | (

    ( 
	find . "ht.waitstart/$PRIORITY" \( \( -name "ht.tmp.*" -o -name "ht.task.*.finished" -o -name "ht.task.*.broken" -o -name "ht.task.*.stopped" -o -name "ht.task.*.running" -o -name "ht.task.*.waitstep" -o -name "ht.task.*waitstart" -o -name "ht.waitstart" \) -prune -o -true \) -a \( \( -mmin +15 -name "ht.task.*.running" \) -o \( -name "ht.task.*.waitsubtasks" \) -o \( -name "ht.task.*.waitstep" \) -o \( -name "ht.task.*.waitstart" \) \) -print 
    ) | (
       RETURN=3; 
       while read TASK; do

	    if [ ! -d "$TASK" ]; then
		continue
	    fi

	    logmsg 1 "Find next task: investigating $TASK"
	
            # TASK is now a directory on form /some/path/ht.task.id.1.2.3.code.running
	    DIR=$(dirname "$TASK")
	    FULLNAME=$(basename "$TASK")	    
	    TASKSET=$(split . 3 "$FULLNAME")
	    TASKID=$(split . 4 "$FULLNAME")
	    STEP=$(split . 5 "$FULLNAME")
	    RESTARTS=$(split . 6 "$FULLNAME")
	    OWNER=$(split . 7 "$FULLNAME")
	    PRIO=$(split . 8 "$FULLNAME")
	    STATUS=$(split . 9 "$FULLNAME")
	    
	    if [ "$HT_TASKMGR_SET" != "any" -a "$HT_TASKMGR_SET" != "$TASKSET" ]; then
		logmsg 1 ":: Job skipped, since task type $TASKSET should not be run by this jobmanager ($HT_TASKMGR_SET)"
		continue
	    fi

	    logmsg 1 "Find next task: Considering $TASK, taskid='$TASKID', owner='$OWNER', status='$STATUS', can I run this?"  	   
	#   if [ "${FULLNAME:0:14}" == "ht.tmp.unpack." ]; then
	#       logmsg 1 "This is a unpack library, checking if it is ready to unpack."
	#       if [ -e "$TASK/ht.unpack.ready" ]; then
	#           logmsg 1 "Library ready to unpack."
	#	    # Other taskmanagers may be trying to unpack this at the same time.
	#	    # This shouldn't really be a problem, just suppress error messages...
	#	    find "$TASK" -maxdepth 1 -mindepth 1 ! -name "ht.unpack.ready" -print0 | xargs -0 -i mv "{}" "$DIR" >/dev/null 2>&1
	#	    rm -f "$TASK/ht.unpack.ready" >/dev/null 2>&1
	#	    rmdir "$TASK" /dev/null 2>&1
	#	    RETURN=2
	#	fi
	#	continue
	#    fi

	    DISABLED=$(echo "$TASK" | awk '/\/ht.tmp/{print "DISABLED"}')
	    if [ -n "$DISABLED" ]; then
		logmsg 1 "The task is in a subdirectory to a ht.tmp.* directory, will not touch this."
		continue
	    fi

	    if check_requirements "$TASK"; then
		if check_max_requirements "$TASK"; then
		    logmsg 1 "Next task: I will never be capable to run this, continuing."
		else
		    logmsg 1 "Next task: not currently capable to run this, continuing (should retry later)."
		    # Should this be 2? Well, in that case we will have taskmanagers
		    # in non-daemon-mode hanging around waiting for resources
		    # to become available, I'm not sure that is a good idea.
		    RETURN=3
		fi
		continue
	    fi

	    if [ "$STATUS" == "waitsubtasks" ]; then
		logmsg 1 "Find next task: is a subtasks-type task, checking if it is finished"

		ANY=$(find "$TASK" -name "ht.task.*.running" -o -name "ht.task.*.waitstart" -o -name "ht.task.*.waitstep" -o -name "ht.task.*.waitsubtasks" | wc -l)
		if [ "$ANY" -gt 0 ]; then
		    logmsg 1 "Find next task: subruns task not finished, waiting for all subtasks to complete."
		    continue
		fi
		RUNTYPE="waiting"
	    fi

	    if [ "$STATUS" == "running" ]; then
		MTIME=$(stat -c %y "$TASK")
	        logmsg 1 "Task $TASK is a stale running task with MTIME: $MTIME"
	    fi

	    logmsg 1 "Found a task we could run and which is available: $TASK, trying to adopt."
	    	   
	    NEWRUN=$(adopt "$TASK")
	    RETURNCODE=$?
	    
	    if [ "$RETURNCODE" == "2" ]; then
		RETURN=2
		continue
	    fi

	    if [ "$RETURNCODE" == "1" ]; then
		logmsg 1 "Find next task: adopt reports unknwon error state, continuing."
		continue
	    fi

	    logmsg 1 "Handling any pending atomic transactions."
	    (
		cd "$NEWRUN"
		ATOMIC_EXEC 
	    )
	    if [ -e "$NEWRUN/ht.run.current" ]; then
		(
		    cd "$NEWRUN/ht.run.current"
		    ATOMIC_EXEC 
		)
	    fi

	    if [ "$STATUS" == "waitstep" -o "$STATUS" == "waitstart" ]; then
		logmsg 1 "Find next task: ht_run job in waitstep or waitstart state, good to go."
	    fi

	    if [ "$RUNTYPE" == "running" ]; then
		logmsg 1 "Find next task: old broken run."
		# TODO: Handle restart=false in ht.parameters
	    fi
	    
	    echo "$NEWRUN"
	    return 0
        done

	return $RETURN )

    RETURNCODE=$?	

    case $RETURNCODE in
	0 ) # All is OK, a run has been printed out on stdout, we are finished
	    return 0 
	    ;;
	2 ) # Could not adopt run, continue onwards, but make sure to retry if nothing is found
	    return 2
	    ;;
	3 ) # Didn't find anything to do, moving on
	    return 3
	    ;;
	* )
	    errmsg "Find next task: Unexpected return code from looking for Running.ht dirs: $RETURNCODE"
    esac
}

logmsg 1 "Taskmanager starting up with rootdir: $HT_TASKMGR_ROOTDIR"	    

HEARTBEATPID=$( (
    COUNT=0
    while [ 0 == 0 ]; do
	TASKMGR_HEARTBEAT
	sleep 321
    done
) >/dev/null 2>&1 & echo $!)

while [ 0 == 0 ]; do
    PRIORITY=1
    RETRY=0
    while [ 0 == 0 ]; do
	#sleep 5
	logmsg 1 "Taskmanager looking for something to do on priority level $PRIORITY."	    
	NEXTTASK=$(find_next_task "$PRIORITY")
	RETURNCODE=$?

	if [ $RETURNCODE -eq 0 ]; then
	    RETRY=0
	    logmsg 1 "##### STARTING RUN: $NEXTTASK"	    
	    start_run "$NEXTTASK" &
	    # TODO: Properly count nodes
	    FREE_NODES=$((FREE_NODES-1))
	    if [ $FREE_NODES -le 0 ]; then
		break;
	    fi
	else
	    if [ $RETURNCODE -eq 3 ]; then
		RETRY=0
		logmsg 1 "No task to do found."	    
		PRIORITY=$((PRIORITY+1))
		if [ "$PRIORITY" -gt "5" ]; then
		    logmsg 1 "Did not find anything to do, already at lowest priority."	    
		    break
		fi
		logmsg 1 "Decreased priority to $PRIORITY."	    
		continue
	    else
		logmsg 1 "Did not find anything to do (but this is temporary, we should not quit)."
		RETRY=1
		PRIORITY=$((PRIORITY+1))
		if [ "$PRIORITY" -gt "5" ]; then
		    logmsg 1 "Did not find anything to do, already at lowest priority."	    
		    break
		fi
		logmsg 1 "Decreased priority to $PRIORITY."	    
		continue
	    fi
	fi
    done
    # TODO: This works with only one node, but needs to be rethought
    # to handle multiple nodes and resource management.
    RUNNING=$(jobs -p | wc -l)
    if [ $RUNNING -gt 0 ]; then
	logmsg 1 "Waiting for any of the running tasks to finish. Number of tasks: $RUNNING"
	# Possible race condition here?, what happens if a job completes
	# just after checking, above?
	while [ 0 == 0 ]; do
	    wait 
	    RETCODE=$?
	    logmsg 1 "Woke up by returncode: $RETCODE"
	    if [ "$RETCODE" -le 127 ]; then
		break;
	    fi
	done
    elif [ "$DAEMONMODE" == "true" -o "$RETRY" == "1" ]; then
	logmsg 1 "Nothing left to do for now, idling a short while."	
	sleep 30
    else
	logmsg 1 "Nothing left to do, not running in daemon mode: quitting."	
	break
    fi
    RUNNING=$(jobs -p | wc -l)
    FREE_NODES=$((TOTAL_NODES-RUNNING))
    logmsg 1 "Free nodes available: ${FREE_NODES} of ${TOTAL_NODES}"
    # Test if we are in daemon mode
done

echo "Waiting for any running processes to finish."
wait
