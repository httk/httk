#!/bin/bash

# This is the API with which you interact with the httk task system and taskmanager

#### A few minor utility routines 

# Floating point arithemtic in BASH that can be very helpful
# HT_FCALC: Make a floating point calculation, 
function HT_FCALC {
    local VARS="$@"
    VARS="$VARS"
    awk "function abs(_value) {return sqrt(_value^2)} 
         function max(_a,_b) {if(_a>_b) {return _a} else {return _b} }
         function min(_a,_b) {if(_a>_b) {return _b} else {return _a} }
         BEGIN {printf(\"%.6g\n\",($VARS))}"
}

function HT_ECALC {
    local VARS="$@"
    VARS="$VARS"
    awk "function abs(_value) {return sqrt(_value^2)} 
         function max(_a,_b) {if(_a>_b) {return _a} else {return _b} }
         function min(_a,_b) {if(_a>_b) {return _b} else {return _a} }
         BEGIN {printf(\"%.14e\n\",($VARS))}"
}

function HT_FTEST {
    local VARS="$@"
    VARS="$VARS"
    awk "function abs(_value) {return sqrt(_value^2)} 
         function max(_a,_b) {if(_a>_b) {return _a} else {return _b} }
         function min(_a,_b) {if(_a>_b) {return _b} else {return _a} }
         BEGIN {if($1) { exit 0 } else { exit 1 } }"
}

function HT_FILE_MATCH {
    GLOB=$(basename "$1")
    DIR=$(dirname "$1")
    test -n "$(cd "$DIR"; find . -mindepth 1 -maxdepth 1 -name "$GLOB" -print -quit)"
    return "$?"
}

function HT_PATH_PREFIX {
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

function HT_SPLIT_FIELDS {
  local SEP=$1
  local GET=$2
  local STR=$3
  awk "{split(\$0,a,\"$SEP\"); print a[$GET]}" <<< "$STR"
}

#### CENTRAL HT ROUTINES
# HT_TASK_INIT 
# Put
#   HT_TASK_INIT "$@" 
# at the top of your runscript (right after sourcing ht_tasks_api.sh). It sets the variable
# STEP to be the next step to execute.
function HT_TASK_INIT {
    # Take care of atomic segments, see HT_TASK_ATOMIC_SECTION_START and HT_TASK_ATOMIC_SECTION_END
    STEP="$1"
    HT_TASK_ATOMIC_EXEC
    if [ -e ht.nextstep ]; then
        STEP=$(cat ht.nextstep)
    fi
    if [ "$STEP" == "ht_finished" ]; then
	HT_TASK_FINISHED
    fi
    if [ "$STEP" == "ht_broken" ]; then
	HT_TASK_BROKEN
    fi
    if [ -e "ht.vars" ]; then
	. ht.vars
    fi
    if [ -z "$HT_NBR_NODES" ]; then
	export HT_NBR_NODES=$(HT_FIND_NBR_NODES)
    fi
}

# Create subtasks to your task
# Usage:
#   HT_TASK_CREATE callback location step taskset prio 
# Reads task parameters as lines on stdin. First column should always be the subtask id.
# For each line, calls callback with this line as paramter, with the 
# current working directory set to a new apropriate subtask directory.
# 
# Other parameters:
#   location: path to where to place the subtasks
#   step: the starting step for the subtasks
#   tasket: the taskset used for all subtasks
#   prio: the prio number 1-5 set for all subtasks

function HT_TASK_CREATE {
    CALLBACK="$1"
    LOCATION="$2"
    if [ -z "$LOCATION" ]; then
	LOCATION="./"
    fi
    STEP="$3"
    if [ -z "$STEP" ]; then
	STEP=start
    fi
    TASKSET="$4"
    if [ -z "$TASKSET" ]; then
	TASKSET=any
    fi
    PRIO="$5"
    if [ -z "$PRIO" ]; then
	PRIO=3
    fi
    while read LINE; do
	TASKID="$(echo "$LINE" | awk '{print $1}')"
	if [ -e "$LOCATION/ht.task.${TASKSET}.${TASKID}".* ]; then
	    # If the subtask already exis, we assume it is already ok, and the
	    # owning job has been restarted, in which case we shouldn't touch
            # this one in case it is already running. All should be well, just 
            # continue onwards with trying to create the other subtask jobs
	    continue
	fi
	if [ -e "$LOCATION/ht.tmp.task.${TASKSET}.${TASKID}.${STEP}.0.none.${PRIO}.waitstart" ]; then
	    rm -rf "$LOCATION/ht.tmp.task.${TASKSET}.${TASKID}.${STEP}.0.none.${PRIO}.waitstart"
	fi
	mkdir "$LOCATION/ht.tmp.task.${TASKSET}.${TASKID}.${STEP}.0.none.${PRIO}.waitstart"
	if [ "$?" != "0" ]; then
	    echo "Could not create directory: $LOCATION/ht.tmp.task.any.$ID.$STEP.$PRIO.waitstart"
	    exit 1
	fi
	#ln -s "$HT_TASK_REL_TOP_DIR/ht_run" "$LOCATION/ht.tmp.task.any.$ID.$STEP.$PRIO.waitstart/ht_run" 
	(
	    cd "$LOCATION/ht.tmp.task.${TASKSET}.${TASKID}.${STEP}.0.none.${PRIO}.waitstart"
	    if [ -n "$CALLBACK" ]; then
		eval "$CALLBACK $LINE"
	    else
		echo "$LINE" > task_data
	    fi
	)
	mv "$LOCATION/ht.tmp.task.${TASKSET}.${TASKID}.${STEP}.0.none.${PRIO}.waitstart" "$LOCATION/ht.task.${TASKSET}.${TASKID}.${STEP}.0.none.${PRIO}.waitstart"
	if [ "$?" != "0" ]; then
	    echo "Error: could not move directory?: $LOCATION/ht.tmp.task.${TASKSET}.${TASKID}.${STEP}.0.none.${PRIO}.waitstart"
	    exit 1
	fi
    done
}

function HT_TEMPLATE {
    TEMPLATE=$1
    OUTPUT=$2

    if [ ! -e "$TEMPLATE" ]; then
	echo "HT_TEMPLATE: Template file missing."
	exit 1
    fi

    eval "cat - <<EOF
$(cat "$TEMPLATE")
EOF" > "$OUTPUT"
}


function HT_TASK_NEXT {
    echo "$1" > "ht.nextstep"
    exit 2
}

function HT_TASK_SUBTASKS {
    echo "$1" > "ht.nextstep"
    exit 3
}

function HT_TASK_FINISHED {
    echo "ht_finished" > "ht.nextstep"
    exit 10
}

function HT_TASK_BROKEN {
    echo "ht_broken" > "ht.nextstep"
    exit 4
}

function HT_TASK_LOG {
    echo "$1" >> ht.log
}

# These functions are here to help handling tricky sections of runscripts that
# need to do several things 'atomicly', i.e., if the task suddenly is stopped,
# these things need to have either ALL have happened, or NONE of them.
# (what is known as a transaction)
# Call HT_TASK_ATOMIC_SECTION_START. After this the current directory is a 
# subdirectory of the run directory. Create files here (accessing files in the run
# directory via ..). Once finished, call one of 
#   HT_TASK_ATOMIC_SECTION_END_NEXT <next step>
#   HT_TASK_ATOMIC_SECTION_END_NEXT_SUBTASKS <next step>
#   HT_TASK_ATOMIC_SECTION_END_NEXT_FINISHED
# which completes the atomic step and returns. 
function HT_TASK_ATOMIC_SECTION_START {
    local TMPDIR=$(HT_PATH_PREFIX -d ht.tmp.atomic.)
    cd "$TMPDIR"
}

# In runscripts this should not be called directly, USE ONE OF THE HT_TASK_ATOMIC_SECTION_END_* INSTEAD.
# YOU SHOULD ALWAYS END THE SCRIPT DIRECTLY AFTER THE CRITICAL SECTION
function HT_TASK_ATOMIC_SECTION_END {
    ATOMDIR=$(basename "$(pwd -P)")
    cd ..
    # This is the atomic step, before this, all gets ignored, after this, we are at the next step.
    OUTDIR=$(HT_PATH_PREFIX "$ATOMDIR" ht.atomic.)
    #
}

function HT_TASK_ATOMIC_SECTION_END_NEXT {
    NEXTSTATE="$1"
    echo "$NEXTSTATE" > ht.nextstep
    HT_TASK_ATOMIC_SECTION_END 
    HT_TASK_ATOMIC_EXEC
    HT_TASK_NEXT "$NEXTSTATE"
}
function HT_TASK_ATOMIC_SECTION_END_SUBTASKS {
    NEXTSTATE="$1"
    echo "$NEXTSTATE" > ht.nextstep
    HT_TASK_ATOMIC_SECTION_END 
    HT_TASK_ATOMIC_EXEC
    HT_TASK_SUBTASKS "$NEXTSTATE"
}
function HT_TASK_ATOMIC_SECTION_END_FINISHED {
    echo "ht_finished" > ht.nextstep
    HT_TASK_ATOMIC_SECTION_END 
    HT_TASK_ATOMIC_EXEC
    HT_TASK_FINISHED
}

# One may think this isn't really needed, but it is really convinient to be 
# able to find out inside an atomic section that things have gone wrong and
# we must end in a broken state.
function HT_TASK_ATOMIC_SECTION_END_BROKEN {
    echo "ht_broken" > ht.nextstep
    HT_TASK_ATOMIC_SECTION_END 
    HT_TASK_ATOMIC_EXEC
    HT_TASK_BROKEN
}

function HT_TASK_ATOMIC_MV {
    FROM="$1"
    TO="$2"
    echo "$2" > ht.atommv."$1"
}

function HT_TASK_ATOMIC_EXEC {
    if HT_FILE_MATCH "ht.tmp.atomic.*"; then
	rm -rf ht.tmp.atomic.*
    fi

    if HT_FILE_MATCH "ht.atomic.*"; then
	for ATOMDIR in ht.atomic.*; do
	    (cd "$ATOMDIR"; find . -maxdepth 1 -name "ht.atommv.*") | sed -e 's/^.\/ht.atommv.//' | xargs -i sh -c "mv {} \$(cat \"$ATOMDIR/ht.atommv.{}\"); rm -f \"$ATOMDIR/ht.atommv.{}\""
	    if HT_FILE_MATCH "$ATOMDIR/*"; then
		mv "$ATOMDIR"/* .
	    fi
	    rmdir "$ATOMDIR"
	done
    fi

    # Yes, repeat this again, in case evaluating the ht.atomic have created ht.tmp.atomic files,
    # a trick that can be used to remove files is thus moving them to ht.tmp.atomic.<name>
    if HT_FILE_MATCH "ht.tmp.atomic.*"; then
	rm -rf ht.tmp.atomic.*
    fi
}

# This routine allows running a program supervised by a timeout and several 'checkers' that
# check that the program is running as it should, and if not, kills it.
#
# The stdout checker checks specifically the stdout + stderr of the program, the other
# checkers can do what they want (but presumably they open files and check that they
# behave as they should)
#
# A checker should return with exit status 2 if they want the program to be killed.
# Checkers are started with one argument, the name of an output file to write any
# messages to (i.e., an error code, why the run was stopped).
#
# When the run has ended, all messages are aggregated into ht.runmsgs
#
# Usage:
# HT_TASK_RUN_CONTROLLED <timeout> [stdout checker [other checkers]] -- command args ...
#
function HT_TASK_RUN_CONTROLLED {
    TIMEOUT="$1"
    shift 1
    STDOUTCHECKER="$1"
    if [ "$STDOUTCHECKER" == '--' ]; then
	STDOUTCHECKER=""
    else
	shift 1
    fi

    # Everything runs in a subshell so that 'wait' works as we expect and
    # traps can be defined only for this subshell
    (
	STOPPED=0
	TIMEDOUT=0
	RETURNCODE=0

	if [ -z "$BASHPID" ]; then
	    BASHPID=$(sh -c 'echo $PPID')
	fi
	export HT_SIGNAL_PID="$BASHPID"

	echo "HT_TASK_RUN_CONTROLLED: Starting with PID $BASHPID and timeout $TIMEOUT" >&2

	# Timeout watchdog subshell
	(   
	    SIGNAL=0
	    trap "echo HT_TASK_RUN_CONTROLLED: TIMEOUT watchdog process got term signal.; SIGNAL=1" TERM
	    trap "echo HT_TASK_RUN_CONTROLLED: TIMEOUT watchdog process got int signal.; SIGNAL=1" INT
	    #trap " " TERM
	    sleep "$TIMEOUT" & 
	    SP=$! 
	    wait
	    RETCODE=$?
	    echo "HT_TASK_RUN_CONTROLLED: TIMEOUT watchdog wait stopped with code: $RETCODE"; 
	    if [ "$RETCODE" -gt "127" ]; then
	    	kill -TERM "$SP" >/dev/null 2>&1; 
	    fi
	    if [ "$SIGNAL" == 0 ]; then
		kill -USR2 "$HT_SIGNAL_PID"
	    fi
	) &
	export TIMEOUTPID="$!"
	echo "HT_TASK_RUN_CONTROLLED: Timeout watchdog started with pid: $TIMEOUTPID"

	trap "echo HT_TASK_RUN_CONTROLLED: got USR1 signal, stopping; STOPPED=1; RETURNCODE=2" USR1
	trap "echo HT_TASK_RUN_CONTROLLED: got USR2 signal, stopping; STOPPED=1; TIMEDOUT=1; RETURNCODE=99" USR2
	trap "echo HT_TASK_RUN_CONTROLLED: got SIGTERM signal, shutting down; trap - TERM; STOPPED=1; RETURNCODE=3" TERM
	trap "echo HT_TASK_RUN_CONTROLLED: got SIGINT signal, shutting down; trap - INT; STOPPED=1; RETURNCODE=100" INT
	trap "kill $TIMEOUTPID" EXIT

	i=0
	EXCLUDEPIDS="^$TIMEOUTPID\$"
	while [ 0 == 0 ]; do
	    CHECKER="$1"
	    shift 1
	    if [ "$?" == "1" ]; then
		echo "HT_TASK_RUN_CONTROLLED need one argument named '--' to separate CHECKERS and command to run."
		exit 1
	    fi
	    if [ "$CHECKER" == "--" ]; then
		break
	    fi
	    i=$((i+1))
	    # This hides the external program from job control
	    HIDDEN_FROM_JOB_CONTROL=$(rm -f "ht.tmp.msgs.$i")
	    ( "$CHECKER" "ht.tmp.msgs.$i" "$TIMEOUTPID"; if [ "$?" == "2" ]; then echo "HT_TASK_RUN_CONTROLLED - CHECKER '$CHECKER' EXITED WITH ERROR, STOPPING RUN."; kill -USR1 "$HT_SIGNAL_PID"; fi ) &
	    EXCLUDEPIDS="$EXCLUDEPIDS\|^$!\$"
	done

	if [ -n "$STDOUTCHECKER" ]; then
	    #setsid "$@" 2>&1 | ("$STDOUTCHECKER" "ht.tmp.msgs.stdout" "$HT_SIGNAL_PID";) | tee stdout.out &
	    setsid "$@" 2>&1 | ("$STDOUTCHECKER" "ht.tmp.msgs.stdout" "$TIMEOUTPID"; if [ "$?" == "2" ]; then echo "HT_TASK_RUN_CONTROLLED - STDOUTCHECKER EXITED WITH ERROR, STOPPING RUN."; kill -USR1 "$HT_SIGNAL_PID"; fi; cat -) | tee stdout.out &
	else
	    setsid "$@" 2>&1 | tee stdout.out &
	fi
	PROCESS="$(jobs -p | grep -v "$EXCLUDEPIDS")"
	echo "HT_TASK_RUN_CONTROLLED: Started main process with pid: $PROCESS" 
	
	# Saftey protection ensuring we don't leave spawned processes if this script breaks
	trap "echo got EXIT; kill $TIMEOUTPID; kill -9 -$PROCESS;" EXIT

	# Either the process finishing, or a singal, wakes up this wait
	wait "$PROCESS"
	PROCEXITCODE="$?"

	if [ "$STOPPED" == "1" ]; then
	    echo "HT_TASK_RUN_CONTROLLED: Run was STOPPED."
	else
	    echo "HT_TASK_RUN_CONTROLLED: Run finished (or timed out.)"
	fi

	if [ "$TIMEDOUT" == "1" ]; then
	    echo "HT_TASK_RUN_CONTROLLED: Run timed out."
	    echo "TIMEOUT" > ht.tmp.msgs.timeout
	else
	    echo "HT_TASK_RUN_CONTROLLED: Run did not time out."
	fi

	# Allow a short delay to let timeout process run to completion
	sleep 1

	if kill -TERM "$TIMEOUTPID" >/dev/null 2>&1; then
	    echo "HT_TASK_RUN_CONTROLLED: Timeout process pid $TIMEOUTPID was still alive (killed now)"   
	else
	    echo "HT_TASK_RUN_CONTROLLED: Timeout process NOT alive."
	fi

	# If the process group pertaining to the first job is still alive, we need to cleanup
	if kill -0 "-$PROCESS" >/dev/null 2>&1; then
	    # Make sure process tree gets cleaned up, but allow graceful shutdown
	    # This hides the external program from job control
	    echo "HT_TASK_RUN_CONTROLLED: Run process still alive, sent SIGTERM, sheduled definite SIGKILL in 10 secs."
	    HIDDEN_FROM_JOB_CONTROL=$( ( kill -TERM "-$PROCESS"; sleep 10; kill -9 "-$PROCESS") >/dev/null 2>&1 &)
	else
	    echo "HT_TASK_RUN_CONTROLLED: Run process no longer alive."
	    if [ "$STOPPED" != "1" -a "$TIMEDOUT" != "1" ]; then
		RETURNCODE="$PROCEXITCODE"
	    fi
	fi

	echo "HT_TASK_RUN_CONTROLLED: Waiting for all checker processes to catch up and finish."
	wait 

	trap - EXIT

	find . -maxdepth 1 -name "ht.tmp.msgs.*" -print0 | xargs -0 cat > ht.controlled.msgs
	rm -f ht.tmp.msgs.*

	echo "HT_TASK_RUN_CONTROLLED: ends" >&2

	return "$RETURNCODE"
    )
}

function HT_TASK_FOLLOW_FILE {
    # This appears to be the most portable way of doing this, while still staying reasonably 
    # efficient (i.e., seeking to the end), sigh...
    perl -e '
      use strict;
      use warnings;

      my $filename = $ARGV[0];
      my $exitpid = $ARGV[1];
      my $timeout;
      if($#ARGV >= 3) {
        $timeout = $ARGV[2];
      } else {
        $timeout = -1;
      }
      my $noexitpid = 0;
      my $curpos;
      my $filevar;
      my $finished;
      my $timeoutcounter;
      my $line;

      $timeoutcounter = $timeout ;

      if($exitpid eq "") { $noexitpid = 1; };

      $SIG{USR1} = sub { $finished = 1; };

      while (! -e $filename && ($noexitpid || kill 0, $exitpid)) {
        sleep 1;
        if($timeoutcounter != -1) {
          $timeoutcounter -= 1;
          if($timeoutcounter == 0) {
            print "\n";
            print "HT_TIMEOUT (NO FILE)\n";
            $finished = 1;
          }
        } 
      }

      if(-e $filename) {
        open($filevar,$filename);
        seek($filevar, 0, 0);      
        while (!$finished) {    
  	  for ($curpos = tell($filevar); !$finished && ($line = <$filevar>); $curpos = tell($filevar)) {
	      print $line;
              #print { STDERR } "CHECK:",$filename,":",$line,"\n";
              $timeoutcounter = $timeout;
  	  }
	  sleep 1;
          if($timeoutcounter != -1) {
            $timeoutcounter -= 1;
            if($timeoutcounter == 0) {
              print "\n";
              print "HT_TIMEOUT\n";
              $finished = 1;
            }
          } 
          if(!$noexitpid && !kill 0, $exitpid) { $finished = 1 };
          #print { STDERR } "CHECK:",$filename,"\n";
	  #select()->flush();
	  $|=1;
	  seek($filevar, $curpos, 0);
        }
        # Make sure we have seen the last part
        sleep 1;
        for ($curpos = tell($filevar); $line = <$filevar>; $curpos = tell($filevar)) {
	  print $line;
          #print { STDERR } "XCHECK:",$filename,":",$line,"\n";
        }
      }
      #print { STDERR } "END:",$filename,"\n";
      exit(0);
    ' "$1" "$2"
}

function HT_TASK_SET_PRIORITY {
    echo "$1" > "ht.priority"
}

function HT_TASK_COMPRESS {
    find . -type f -not -name "ht.*" -print0 | xargs -0 bzip2
    if [ -e ht.RUNLOG ]; then
	bzip2 ht.RUNLOG
    fi
}

function HT_TASK_UNCOMPRESS {
    find . -type f -name "*.bz2" -print0 | xargs -0 bunzip2
}

function HT_TASK_STORE_VAR {
    TAG="$1"
    VALUE="$2"
    if [ -e ht.vars ]; then
	(awk '!/^ *'$TAG' *=/{print $0}' ht.vars; echo "$TAG=$VALUE") > ht.tmp.vars
    else
	echo "$TAG=$VALUE" > ht.tmp.vars
    fi
    mv ht.tmp.vars ht.vars
}

function HT_TASK_CLEANUP {
    rm -f ht.vars ht.controlled.msgs 
    rm -rf ht.tmp.*
}

function HT_TASK_ATOMIC_RUNLOG_APPEND {
    local FILE
    local BASENAME
    OLDLOG=../ht.RUNLOG

    (
        if [ -e ht.RUNLOG ]; then
	    cat ht.RUNLOG
	elif [ -e "../ht.RUNLOG" ]; then
	    cat ../ht.RUNLOG
	fi
	for FILE in "$@"; do
	    if [ ! -e "$FILE" ]; then
		continue
	    fi
	    BASENAME=$(basename "$FILE")
	    echo "====================================================="
	    echo "$BASENAME"
	    echo "====================================================="
	    cat "$FILE"
	    echo "====================================================="
	    echo ""
	done
    ) > ht.tmp.RUNLOG
    mv ht.tmp.RUNLOG ht.RUNLOG
}


function HT_TASK_ATOMIC_RUNLOG_HEADLINE {
    local OLDLOG="../ht.RUNLOG"
    (
        if [ -e ht.RUNLOG ]; then
	    cat ht.RUNLOG
	elif [ -e "../ht.RUNLOG" ]; then
	    cat ../ht.RUNLOG
	fi
	echo "*****************************************************"
	echo "$(date -R): $@"
	echo "*****************************************************"
	echo ""
    ) > ht.tmp.RUNLOG
    mv ht.tmp.RUNLOG ht.RUNLOG
}

function HT_TASK_ATOMIC_RUNLOG_NOTE {
    local OLDLOG="../ht.RUNLOG"

    (
        if [ -e ht.RUNLOG ]; then
	    cat ht.RUNLOG
	elif [ -e "../ht.RUNLOG" ]; then
	    cat ../ht.RUNLOG
	fi
	echo "$@"
    ) > ht.tmp.RUNLOG
    mv ht.tmp.RUNLOG ht.RUNLOG
}

function HT_FIND_NBR_NODES {
    # Extremely convolted way of counting number of nodes when all we know is that there is an
    # mpirun program that is supposed to run things in parallel over all nodes. Note that you
    # can never be sure if mpirun garbles the order of your ourput...
    OUTPUT=$(mpirun -q echo "~^" 2>/dev/null)
    ONE=$(echo "$OUTPUT" | awk -F'~' '{sum+=NF-1} END {print sum}')
    TWO=$(echo "$OUTPUT" | awk -F'^' '{sum+=NF-1} END {print sum}')
    if [ "$ONE" == "$TWO" -a "$ONE" -gt 1 ]; then
	echo "$ONE"
    else
	echo 1
    fi
}

