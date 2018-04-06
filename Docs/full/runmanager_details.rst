=====================================================================
*httk* Runmanager Details
=====================================================================
.. raw:: text
   :file: header.tpl

The httk 'taskmanager toolset' is centered around the taskmanager.sh
program. This program is responsible for handling a large set of
'tasks' you want to execute on a computer cluster. It can distribute
resources between your runs, and re-start them when they break due to,
e.g., a computer node breaks, or your job is stopped due to running
out of allocated time, etc.

The general philosophy is that 'taskmanager.sh' handles all the tricky
parts with overseeing your runs, keeping track of which ones are in
which states, and can even restart them automatically when needed. The
taskmanager.sh is, in a way, a "second layer of queue system" for your
runs.

taskmanager.sh is started in a 'task directory'. It looks in this
directory and descends into subdirectories, looking for anything that
is setup as a task that is waiting to be run, and then runs it. You
can have more than one taskmanager.sh run in the same task directory,
taskmanager.sh is very carefully programmed to avoid inference between
several instances of itself.

The taskmanager.sh runs until there is nothing more to do in the task
directory, at which points it terminates. This is what you typically
want if you submit taskmanager.sh to run on supercomputer cluster
nodes. Alternatively you can start it with 'taskmanager.sh --daemon",
in which case it keeps running forever, looking for new tasks to
arrive. You could, e.g., setup a taskmanager daemon running on your
own personal computer.

Anatomy of a task
---------------------

There are a number of conventions you have to follow when setting up a
task to be run by taskmanager.sh.

A task is stored in its own directory. The directory name has a very specific 
format::

  ht.task.<computer>.<taskid>.<step>.<restarts>.<owner>.<prio>.<status>

where:
  <computer> this is the computer that the task has been assigned to, or 'unassigned'.
  <prio> is a priority number 1-5. Use '3' as default.
  <taskid> is a "name" for the task
  <step> is the present 'step' that a multi-step task is on
  <restarts> is a counter that keeps track on how many times the task has been restarted, when created should be 0
  <owner> 'unclaimed' when created, which is changed into a code belonging to a running taskmanager that presently is handling the task. 
  <status> is one of:

           - waitstart: the task is waiting to be started for the first time

           - running: the task is currently being executed

           - waitstep: the task is partially completed and waits for the next step

           - waitsubtasks: the task has split into a number of subtasks and is waiting for them to complete

           - finished: the task has successfully run to completion

           - broken: the task has returned an error code that specifies that it wants to be set aside as 'broken'.

           - stopped: the taskmanager have stopped the job for some reason (timeout, too many restarts, etc.)

The primary component of a task is a "runscript" or a "runprogram" (you can use any language to write these) that
is responsible for executing your computational task. The task directory should contain this runscript. It can have either one
of two names:

  - ht_run: A 'simplified' run script that is meant for simple jobs. "Just run this".
    If the run breaks (e.g. is stopped by the computer cluster), it will simply
    be restarted the next time (you are responsible for necessary cleanup).
           
  - ht_steps: Step-scripts allows for more functionality, most importantly, a run can
    be executed in a series of steps, and re-start is done from the last
    completed step rather than as a complete do-over.


The ht.parameters file
----------------------

[*IMPORTANT:* This section describes functionality not yet
fully implemented. Presently ht.taskmanger starts all tasks. To handle
resources, you presently need to setup e.g. a single cluster as
different 'computers']

The run directory may contain a file ht.parameters that, in that case, 
is consulted by taskmanager.sh before executing the run. The file should 
be formatted as rows of 'parameter=value'. 

Relevant parameters are:
  'cores=X' : The task needs to run at at least X cores.

  'nodes=X' : The task needs to run at at least X computer nodes.
 
  'memory=X': The task needs at least X amount of memory.

  'restart=false': Never restart the run, always re-init it from scratch if possible (if not, set it in a 'broken' state).
  
If the requirements cannot be fulfilled (at a given time) the process
is skipped and taskmanager.sh looks for another process (possibly of
lower priority)

Note: taskmanager.sh does not at this time implement a fancy resource
management algorithm, but rather just uses a 'greedy' algorithm where
it tries to start jobs in priority order. A high-priority job
with harsh resource requirements (e.g., many nodes) may thus be
starved by a massive amount of small low priority jobs. If this is a
problem, you will have to setup a separate 'computer' for jobs that
would otherwise starve.


Simplified 'ht_run' runscript
-----------------------------

When your 'ht_run' is executed, your current working directory is your
task directory. The script gets called with one command line
parameter, the name of the <step> in the task directory name. The
runscript should simply execute your run.

IMPORTANT: In case your run gets stopped (e.g., by the computer
cluster because your job runs out of time, or the computer node it is
running on crashes), it needs to handle being re-started with no ill
effects, i.e., 'ht_run' will get executed again in an 'unclean'
directory.  If this is not possible, set 'restart=false' in the
ht.parameters file. But note, the latter means your run will end up in
a 'broken' state if it needs to be restarted. This is a bad idea for
real high-throughput jobs. In this situation, you are strongly
recommended to use a ht_steps script instead. (see below)

See APPENDIX A.1 below for an outline of how taskmanager.sh actually process
a ht_run-type task. This may be very helpful to understand what
actually happens.


The more advanced 'ht_steps' runscript
--------------------------------------

When your 'ht_steps' is executed, your current working directory is an
empty *subdirectory* of your task directory named 'ht.run.<date>'. You
should access files in your task directory simply by '../filename',
etc.  Your 'ht_steps' script is supposed to setup the run in this
directory by copying or use symbolic linking ('ln -s') of the
appropriate files from your run directory. You should then execute
your run, and end your run script in a normal way.

You are 'forced' into using a subdirectory this way rather than simply
executing your run in the run directory itself. The motivation for
this is to unify task handling for restarts, etc.

When a 'ht_steps' runscript is executed it gets a single parameter set
to the <step> part of the task directory name.  When it finishes, it
should first write a file 'ht.status' in the task directory that
contains a simple string naming its next 'step', and then it should
return with a specific exit code:

  - exit code 2: Waiting for next task

  - exit code 3: Subtasks have been created, do not restart again until all are completed.

  - exit code 4: Restart me completely

  - exit code 5: the run is in a broken state, mark it broken and leave it. 
 
Usually you don't need to think about this, just use the provided httk
task api routines for the language being used, and exit the task with,
e.g. 'TASK_NEXT' (in bash) or similar. See the corresponding httk task
api instructions for more details.

IMPORTANT: a ht_steps script *must be capable of being restarted at
the same step*. I.e., if it is started on a 'relax' step, the job may
be stopped (running out of runtime) at any time. It may then be
restarted again on the same 'relax' step in which case it needs to be
able to 're-init' the job and restart (or just continue it, if
applicable). The script needs to be written such that it can handle
this transparently. For example, some electronic structure software
overwrites input files (e.g., VASP overwrites the CHGCAR which
sometimes is used as an input file for a run). In this case, one
*needs* to write ht_steps to keep around a copy CHGCAR.before so that
it can be used to re-initalize the file as the job is
restarted. Alternatively, a task may return '4' to indicate that it is
in such a broken state that it has to be completely restarted. You are
recommended to read the code of some tasks provided along with httk to
learn how tasks should be written.

See APPENDIX A.2 for an outline of how taskmanager.sh actually process
a ht_steps-type task. This may be very helpful to understand what
actually happens.


'ht_steps' subtasks
-------------------

In a ht_steps script one can create 'subtasks'.  This is done is
simply by the runscript generating subdirectories with appropriate
naming (see section 6.2 Anatomy of a task above.) Note that as soon as
the directories fulfill this naming scheme, the run may be executed by
another taskmanager.sh process, so one must follow the following
process:

  1. Create a directory called ht.tmp.task.(something)

  2. Populate the directory with necessary files to run as a subtask. 
     (Primarily, a ht_run, or ht_steps)

  3. Only when the subtask is ready, 
     `mv ht.tmp.task.<something> ht.task.<something>`

Using specifically the 'ht.tmp.' prefix for your temporary directories
has the advantage that such directories are automatically removed when
runs are restarted, which avoids leaving half-complete subtask
directories in case your job is stopped while creating subtasks.

When a ht_steps script exits with exit code 3, it will be put on hold
until all subtasks that reside inside its subdirectories have run to
completion. Once this has happened, it will be restarted as usual with
'ht_steps <step>'.

Note that subtasks are handled exactly like regular tasks, so they can
themselves create substasks, and so on.

A couple of neat tricks:

  - Use a symbolic link ('ln -s') to make your subtasks use the same
    ht_steps script as the topmost task. This way all the run
    functionality can conveniently be kept inside one and the same
    script/program.

  - Even if your main job uses a 'ht_steps' runscript, your subtasks
    can use 'ht_run' scripts to decrease the overhead.  (You can even
    make a symbolic link from the subruns 'ht_runs' to your main
    'ht_steps'.)


single_job_taskmanager.sh
-------------------------

There is a 'light' version of the taskmanager named
single_job_taskmanager.sh that may be helpful in a few situations,
e.g.,

  - You are in the process of developing a run script and "just want
    to run through this task" to debug it, with all output in the
    console.

  - You don't care for the parallelism, resource handling, and
    restart/continuation capability of the full httk taskmanager, and
    just want something to put in your cluster submit script that will
    simply run one task to completion with a minimum of hassle.

You start single_job_taskmanager.sh with the task directory as the
current working directory, and it will run that one task to
completion. It never 'restarts' a task. It thus always create a new
'run.<date and timestamp>' and run the task in this directory. It will
not rename the task directory itself, and there is no need to follow
the naming convention of the task directory at all. It ignores all
'ht.parameters' files. Other than this, it mimics the exact
functionality of the full task manager both for 'ht_run' and
'ht_steps' type runscripts.
 
taskmanager.sh prioritization
-----------------------------

The priority order of waiting tasks is the following:

  - First it handles tasks of priority 1, then 2, ... , and last 5.

  - It first prioritize finishing tasks that have been started before 
    starting new ones.

  - It always runs subtasks 'depth first'.


Provided helper scripts
-----------------------

In the httk directory, under Execution/tasks-templates/* you can find
a number of provided scripts that can be used as-is for your own runs.
Reading and understanding them may help you develop / adapt them to
your own needs.


Writing runscripts in python
----------------------------

The present aid in the python library for run scripts is limited to
use of ready-made templates under Execution/tasks-templates/
Please consult the tutorial Step6.

It is the idea that the httk library will be extended with helper
functionality for writing your own runscripts in python. One of the
leading design ideas is to make it possible to write scripts that
describes how to do a calculation in a *code-independent-way*. I.e.,
relying on higher-order routines of type 'converge' and 'relax' which
then call out to a specific code.


Writing runsscripts in bash
---------------------------

httk presently come with a helper library of routines for writing
runscripts in bash. 

There is a general tasks API for bash in:
  Execution/tasks/ht_tasks_api.sh

and specifically a set of helper routines for runs with the electronic structure software VASP in:
  Execution/tasks/vasp/vasptools.sh


APPENDIX A: taskmanager.sh process outlines
-------------------------------------------


The taskmanager.sh process with a `ht_run` runscript
....................................................

Here is an outline of the process as taskmanager.sh executes a ht_run script:

  1. taskmanager.sh looks in the task directory and finds a
     `*.waitstart` directory

  2. taskmanager.sh 'adopts' this task by renaming the directory so
     that it includes a taskmanager-id (an id that pertains to this
     runmanager.sh instance) This 'locks' the run from being tampered
     with by other runmanagers.

  3. taskmanager.sh executes the ht_run script in this directory.

  4. the ht_run script does what it needs to do and simply finishes as
     usual.

  5. taskmanager.sh renames the task directory to both remove the
     taskmanager-id and so that it now ends with a '.finished' suffix.

IF the taskmanager and the job is stopped at any of the points 3-5
(e.g., the cluster runtime ends and stops the processes), you can
simply submit another job with a new taskmanager.sh. This is an
outline of what happens then:

  1. taskmanager.sh notices a directory named 'ht.task.*.running' that
     has a filesystem 'ctime' that is > 10 minutes old. This marks an
     abandonded run, because an alive taskmanager.sh makes sure to
     update ctime periodically on any ongoing runs.

  2. taskmanager.sh 'adopts' this task by renaming the directory so
     that it removes the old taskmanager-id and replaces it with that
     of the present instance.

  3. taskmanager.sh simply restarts the ht_run scripts in this
     directory (expecting it to know what to do with regards to
     cleanup etc.)
  
  4. Everything continues from point #4 and onwards in the regular
     outline above.
 
   
The taskmanager.sh process with a ht_steps runscript  
.........................................................

The process outlined in 6.3 changes when a tasks_steps script is
used. Steps 1-2 are the same, after that, this happens:

  3. taskmanager.sh creates a subdirectory in the task directory named
     similar to 'ht.run.2014-05-05_12_15_36' (i.e., 
     ht.run.<date and time-stamp>) and makes this directory the current 
     working directory.

  4. taskmanager.sh executes 'ht_steps <step>' where step is the name
     of the .<step>. part of the task directory name.

  5. ht_steps executes the apropriate part of the run, writes the
     ht.status file, and exits with an apropriate exit status.
  
  6. The directory is renamed to remove the taskmanager-id and,
     depending on the exit status, is made to end with any one of
     '.finished', 'waitstep' or , 'waitsubtasks'. If '.finished',
     then this job is complete and will be left alone. Otherwise,
     continue below.

  7. taskmananger.sh goes back to scanning the task directory for
     runs, but will eventually find this job again.

  [If it ends in .waitsubtasks] 

  8a. subtasks are handled by taskmanager.sh just like any normal
      tasks. The .waitsubtasks ht_step script itself is not touched
      until all subtasks in its subdirectories are in a finished
      state. When this happens, it is restarted following point #4 and
      onwards.
  
  [If it ends in .waitstep]
     
  8b. taskmananger.sh restart the run following point #4 and onwards. 

IF the taskmanager and the job is stopped at any of the points 3-6
(e.g., the cluster runtime ends and stops the processes), you can
simply submit another job with a new taskmanager.sh. This is an
outline of what happens then:

  1. taskmanager.sh notices a directory named 'ht.task.*.running' that
     has a filesystem 'ctime' that is > 10 minutes old. This marks an
     abandonded run, because an alive taskmanager.sh makes sure to
     update ctime periodically on any ongoing runs.

  2. taskmanager.sh 'adopts' this task by renaming the directory so
     that it removes the old taskmanager-id and replaces it with that of
     the present instance.

  3. taskmanager.sh now just continues from point #4 and onwards in the regular outline.
  
The exception to #3 is if the ht.parameters file (see below) contains
'restart=false'. In that case, the old 'run.*' directory will be
removed, and taskmanager.sh instead restarts from #3 in the regular
outline.

