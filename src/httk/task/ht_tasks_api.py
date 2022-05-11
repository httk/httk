#!/usr/bin/env python
#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2022 Henrik Levämäki
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

import os
import sys
import signal
import ast
import shutil
import datetime
import re
import glob
import time
from six import string_types
import subprocess
import multiprocessing as mp
import types


def print_python_info():
    header = "=" * 32 + " Python environment information: " + "=" * 32
    print(header, flush=True)
    print("Are we inside a Singularity container: ",
          "SINGULARITY_CONTAINER" in os.environ, flush=True)
    print("Python version: ", re.sub("\n", " ", sys.version), flush=True)
    print("Python path: ", sys.executable, flush=True)
    print("Imported modules:", flush=True)
    loaded_modules = find_loaded_modules(only_versioned_modules=False)
    loaded_modules.insert(0, ["Name", "Version"])
    column_max_lens = []
    for i in range(len(loaded_modules[0])):
        len_sorted_list = sorted(loaded_modules, key=lambda x: len(x[i]))
        column_max_lens.append(int(len(len_sorted_list[-1][i])))
    print("-" * (sum(column_max_lens) + 3 * (len(column_max_lens) - 1)), flush=True)
    print("Name".ljust(column_max_lens[0]) + " | " + "Version".ljust(column_max_lens[1]), flush=True)
    print("-" * (sum(column_max_lens) + 3 * (len(column_max_lens) - 1)), flush=True)
    for x in loaded_modules[1:]:
        string = ""
        for i in range(len(x)):
            string += x[i].ljust(column_max_lens[i]) + " | "
        string = string[:-3]
        print(string, flush=True)
    print("=" * len(header), flush=True)
    print("", flush=True)


def module_version(mod):
    '''Return version string for module *mod*, or nothing if
    it doesn't have a "version" or "__version__" attribute.'''
    version = []
    if hasattr(mod, '__dict__'):
        for key in mod.__dict__.keys():
            if key.lower() == 'version' or key.lower() == '__version__':
                v = mod.__dict__[key]
                if isinstance(v, string_types):
                    version.append(v)

    # Remove duplicate version info in cases where both 'version' and
    # '__version__' keys were found above:
    version = set(version)
    if version:
        return ', '.join(version)
    else:
        return ''


def find_loaded_modules(only_versioned_modules=True):
    '''Return list of loaded modules for which there is a version
    number or a Git repository commit SHA.

    Return a list of *(name, version, path_to_git_repo, git_head_sha)*,
    which has an HTML property for pretty display in IPython Notebooks.
    '''
    objs = []
    for mod in globals().values():
        if isinstance(mod, types.ModuleType):
            if hasattr(mod, '__name__'):
                name = mod.__name__
            else:
                name = ''
            if name in sys.builtin_module_names:
                continue

            version = module_version(mod)

            if only_versioned_modules:
                flag = version
            else:
                flag = True

            if flag:
                # objs.append([mod.__name__, version, path, sha])
                objs.append([mod.__name__, version])
    objs.sort(key=lambda r: r[0])
    return objs


def find_in_remedy_files(pattern):
    remedy_files = glob.glob("ht.remedy.*")
    pattern_found = False
    for f in remedy_files:
        with open(f, "r") as tmp:
            lines = tmp.read().splitlines()
        for line in lines:
            match = re.search("^{}$".format(pattern), line)
            if match is not None:
                pattern_found = True
                break
        if pattern_found:
            break
    return pattern_found


def find_in_file(pattern, file):
    pattern_found = False
    with open(file, "r") as tmp:
        lines = tmp.read().splitlines()
    for line in lines:
        match = re.search("{}".format(pattern), line)
        if match is not None:
            pattern_found = True
            break
    return pattern_found


def follow_file(fn, timeout=None, immediate_stop=False):
    time_to_stop = False
    time_to_immediately_stop = False

    def sigterm_handler(*args):
        nonlocal time_to_stop, time_to_immediately_stop, immediate_stop
        time_to_stop = True
        if immediate_stop:
            time_to_immediately_stop = True

    def sigint_handler(*args):
        nonlocal time_to_stop, time_to_immediately_stop, immediate_stop
        time_to_stop = True
        if immediate_stop:
            time_to_immediately_stop = True

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    # Do not try to follow a file before there is a file to follow.
    timer_start = time.time()
    while not os.path.exists(fn):
        time.sleep(1)
        if timeout is not None:
            if time.time() - timer_start > timeout:
                yield "HT_TIMEOUT (NO FILE)\n"
                return

    timer_start = time.time()
    with open(fn, "r") as file:
        line = ''
        while True:
            # tmp = '' means EOL.
            # In file following mode we don't care if
            # we hit the EOL, because we know that there
            # should be more text coming.
            #
            # When it is time to stop, keep
            # scanning until we hit the EOL
            # and then exit.
            if time_to_immediately_stop:
                return
            tmp = file.readline()
            if tmp != '':
                line += tmp
                if line.endswith("\n"):
                    yield line
                    line = ''
                    timer_start = time.time()
            else:
                if time_to_stop:
                    return
                if not os.path.exists(fn):
                    return
                time.sleep(1)
                if timeout is not None:
                    if time.time() - timer_start > timeout:
                        yield "HT_TIMEOUT\n"
                        time_to_stop = True


def find_type_conversion(value):
    """For the string input value, see if it can be converted to a float,
    an int or a boolean.
    """
    try:
        value = ast.literal_eval(value)
    except:
        pass
    return value


def cp(from_file, to_file, follow_symlinks=True):
    shutil.copyfile(from_file, to_file, follow_symlinks=follow_symlinks)


def mv(from_file, to_file):
    shutil.move(from_file, to_file)


def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def get_bashlike_date():
    """Return current date as a formatted string
    in a similar format what GNU date coreutil returns.
    Actually, the output format of the `date` command
    depends on the Linux distro.
    """
    date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
    return date


def remove_file_or_folder(f):
    if os.path.exists(f):
        if os.path.isdir(f):
            shutil.rmtree(f, ignore_errors=True)
        else:
            os.remove(f)


def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd else fname,
                 dir_fd=None if os.supports_fd else dir_fd, **kwargs)


def re_line_matches(pattern, line):
    match = re.search(pattern, line)
    if match is not None:
        return True
    else:
        return False


def delete_keyword_line(incar, keyword):
    """Simply checks if a certain keyword is mentioned in a line.
    If it is, delete the line.
    """
    with open(incar, "r") as f:
        lines = f.read().splitlines()
    with open(incar, "w") as f:
        for line in lines:
            line_is_comment = False
            if line.lstrip().startswith("#"):
                line_is_comment = True
            match = re.search("^[\t ]*{}[\t ]*=.*".format(keyword), line)
            if match is not None and not line_is_comment:
                continue
            f.write(line + "\n")


def HT_TASK_INIT(args):
    STEP = args[1]
    HT_TASK_ATOMIC_EXEC()
    if os.path.exists("ht.nextstep"):
        with open("ht.nextstep", "r") as f:
            STEP = f.read().rstrip()
    if STEP == "ht_finished":
        HT_TASK_FINISHED()
    if STEP == "ht_broken":
        HT_TASK_BROKEN()

    # Store ht.vars in a dictionary
    htvars = {}
    if os.path.exists("ht.vars"):
        with open("ht.vars", "r") as f:
            lines = f.read().splitlines()
        for line in lines:
            match = re.search("[\t ]*(\w*)[\t ]*=[\t ]*(\w*)", line)
            if match is not None:
                tag = match.groups()[0]
                value = match.groups()[1]
                htvars[tag] = find_type_conversion(value)

    global HT_NBR_NODES
    if "HT_NBR_NODES" not in os.environ:
        HT_NBR_NODES = HT_FIND_NBR_NODES()
    else:
        HT_NBR_NODES = int(os.environ["HT_NBR_NODES"])
    return STEP, htvars


def HT_TASK_ATOMIC_EXEC():
    for f in glob.glob("ht.tmp.atomic.*"):
        remove_file_or_folder(f)

    for ATOMDIR in glob.glob("ht.atomic.*"):
        for f in glob.glob(ATOMDIR + "/ht.atommv.*"):
            f_src = os.path.basename(f).lstrip("ht.atommv.")
            with open(f, "r") as tmp:
                f_dest = tmp.read()

            mv(f_src, f_dest)
            os.remove(f)

        for tmp in glob.glob(ATOMDIR + "/*"):
            mv(tmp, os.path.basename(tmp))

        shutil.rmtree(ATOMDIR)

    # Yes, repeat this again, in case evaluating the ht.atomic have created ht.tmp.atomic files,
    # a trick that can be used to remove files is thus moving them to ht.tmp.atomic.<name>
    for f in glob.glob("ht.tmp.atomic.*"):
        remove_file_or_folder(f)


def HT_TASK_ATOMIC_MV(from_file, to_file):
    with open("ht.atommv." + from_file, "w") as f:
        f.write(to_file)


def HT_FILE_MATCH(pattern):
    if len(glob.glob(pattern)) > 0:
        return True
    else:
        return False


def HT_FIND_NBR_NODES():
    print("", flush=True)
    print("#" * 80, flush=True)
    print("Warning: Assuming this run is on a local computer, because \"HT_NBR_NODES\" environment variable is not found.\nHT_NBR_NODES will be set to 1.\nIf this is a supercomputer run, HT_NBR_NODES should be calculated\nusing Slurm environment variables instead! (in start-taskmgr)", flush=True)
    print("#" * 80, flush=True)
    print("", flush=True)
    return 1


def HT_TASK_ATOMIC_RUNLOG_HEADLINE(msg):
    with open("ht.tmp.RUNLOG", "w") as f_dest:
        if os.path.isfile("ht.RUNLOG"):
            with open("ht.RUNLOG", "r") as f_src:
                f_dest.write(f_src.read())
        elif os.path.isfile("../ht.RUNLOG"):
            with open("../ht.RUNLOG", "r") as f_src:
                f_dest.write(f_src.read())

        date = get_bashlike_date()
        f_dest.write("*****************************************************\n")
        f_dest.write("{}: {}\n".format(date, msg))
        f_dest.write("*****************************************************\n")
        f_dest.write("\n")

    mv("ht.tmp.RUNLOG", "ht.RUNLOG")


def HT_PATH_PREFIX(FROM, prefix):
    try:
        count = 0
        while os.path.exists(prefix + str(count)):
            count += 1
        if FROM == "-d":
            os.mkdir(prefix + str(count))
        elif FROM == "-f":
            touch(prefix + str(count))
        else:
            mv(FROM, prefix + str(count))
        return prefix + str(count)
    except Exception as e:
        return e


def HT_TASK_ATOMIC_RUNLOG_APPEND(*args):
    with open("ht.tmp.RUNLOG", "w") as f_dest:
        if os.path.isfile("ht.RUNLOG"):
            with open("ht.RUNLOG", "r") as f_src:
                f_dest.write(f_src.read())
        elif os.path.isfile("../ht.RUNLOG"):
            with open("../ht.RUNLOG", "r") as f_src:
                f_dest.write(f_src.read())

        for arg in args:
            for FILE in glob.glob(arg):
                if not os.path.isfile(FILE):
                    continue
                # BASENAME = os.path.splitext(os.path.basename(FILE))[0]
                BASENAME = os.path.basename(FILE)
                f_dest.write("=====================================================\n")
                f_dest.write(BASENAME + "\n")
                f_dest.write("=====================================================\n")
                with open(FILE, "r") as f_src:
                    f_dest.write(f_src.read())
                f_dest.write("=====================================================\n")
                f_dest.write("\n")

    mv("ht.tmp.RUNLOG", "ht.RUNLOG")


def HT_TASK_ATOMIC_RUNLOG_NOTE(msg):
    with open("ht.tmp.RUNLOG", "w") as f_dest:
        if os.path.isfile("ht.RUNLOG"):
            with open("ht.RUNLOG", "r") as f_src:
                f_dest.write(f_src.read())
        elif os.path.isfile("../ht.RUNLOG"):
            with open("../ht.RUNLOG", "r") as f_src:
                f_dest.write(f_src.read())

        f_dest.write(msg + "\n")

    mv("ht.tmp.RUNLOG", "ht.RUNLOG")


def HT_TASK_NEXT(nextstate):
    with open("ht.nextstep", "w") as f:
        f.write(nextstate)
    sys.exit(2)


def HT_TASK_SUBTASKS(nextstate):
    with open("ht.nextstep", "w") as f:
        f.write(nextstate)
    sys.exit(3)


def HT_TASK_FINISHED():
    with open("ht.nextstep", "w") as f:
        f.write("ht_finished")
    sys.exit(10)


def HT_TASK_BROKEN():
    with open("ht.nextstep", "w") as f:
        f.write("ht_broken")
    sys.exit(4)


def HT_TASK_LOG(msg):
    with open("ht.log", "a") as f:
        f.write(msg)


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
def HT_TASK_ATOMIC_SECTION_START():
    TMPDIR = HT_PATH_PREFIX("-d", "ht.tmp.atomic.")
    os.chdir(TMPDIR)


def HT_TASK_ATOMIC_SECTION_END():
    ATOMDIR = os.path.basename(os.getcwd())
    os.chdir("..")
    # This is the atomic step, before this, all gets ignored, after this, we are at the next step.
    OUTDIR = HT_PATH_PREFIX(ATOMDIR, "ht.atomic.")


def HT_TASK_ATOMIC_SECTION_END_NEXT(nextstate):
    with open("ht.nextstep", "w") as f:
        f.write(nextstate)
    HT_TASK_ATOMIC_SECTION_END()
    HT_TASK_ATOMIC_EXEC()
    HT_TASK_NEXT(nextstate)


def HT_TASK_ATOMIC_SECTION_END_SUBTASKS(nextstate):
    with open("ht.nextstep", "w") as f:
        f.write(nextstate)
    HT_TASK_ATOMIC_SECTION_END()
    HT_TASK_ATOMIC_EXEC()
    HT_TASK_SUBTASKS(nextstate)


def HT_TASK_ATOMIC_SECTION_END_FINISHED():
    with open("ht.nextstep", "w") as f:
        f.write("ht_finished")
    HT_TASK_ATOMIC_SECTION_END()
    HT_TASK_ATOMIC_EXEC()
    HT_TASK_FINISHED()


# One may think this isn't really needed, but it is really convinient to be
# able to find out inside an atomic section that things have gone wrong and
# we must end in a broken state.
def HT_TASK_ATOMIC_SECTION_END_BROKEN():
    with open("ht.nextstep", "w") as f:
        f.write("ht_broken")
    HT_TASK_ATOMIC_SECTION_END()
    HT_TASK_ATOMIC_EXEC()
    HT_TASK_BROKEN()


def HT_TASK_CLEANUP():
    files_to_remove = ["ht.vars", "ht.controlled.msgs"]
    for f in files_to_remove:
        remove_file_or_folder(f)
    for f in glob.glob("ht.tmp.*"):
        remove_file_or_folder(f)


def HT_TASK_SET_PRIORITY(priority):
    with open("ht.priority", "w") as f:
        f.write(str(priority))


def HT_TASK_STORE_VAR(tag, value):
    if os.path.exists("ht.vars"):
        with open("ht.vars", "r") as f:
            lines = f.read().splitlines()
        htvars_after = []
        tag_found = False
        for line in lines:
            match = re.search("[\t ]*{}[\t ]*=".format(tag), line)
            if match is not None:
                htvars_after.append("{}={}".format(tag, value))
                tag_found = True
            else:
                htvars_after.append(line)
        if not tag_found:
            htvars_after.append("{0}={1}".format(tag, value))
    else:
        htvars_after = ["{0}={1}".format(tag, value)]
    with open("ht.vars", "w") as f:
        for line in htvars_after:
            f.write(line + "\n")


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
def HT_TASK_RUN_CONTROLLED(TIMEOUT, STDOUTCHECKER, *args):
    STOPPED = 0
    TIMEDOUT = 0
    RETURNCODE = 0

    # def kill_script(timeout_pid, script_pid):
    #     print("got EXIT", flush=True)
    #     if check_pid(timeout_pid):
    #         os.kill(timeout_pid, signal.SIGTERM)
    #     os.kill(script_pid, signal.SIGKILL)

    # def kill_timeout_process(pid):
    #     os.kill(pid, signal.SIGTERM)

    def sigusr1_handler(*args):
        nonlocal STOPPED, RETURNCODE
        # print("HT_TASK_RUN_CONTROLLED: got USR1 signal, stopping", flush=True)
        STOPPED = 1
        RETURNCODE = 2

    def sigusr2_handler(*args):
        nonlocal STOPPED, TIMEDOUT, RETURNCODE
        # print("HT_TASK_RUN_CONTROLLED: got USR2 signal, stopping", flush=True)
        STOPPED = 1
        TIMEDOUT = 1
        RETURNCODE = 99

    def sigterm_handler(*args):
        nonlocal STOPPED, RETURNCODE
        # print("HT_TASK_RUN_CONTROLLED: got SIGTERM signal, shutting down", flush=True)
        STOPPED = 1
        RETURNCODE = 3
        # TODO: trap - TERM

    def sigint_handler(*args):
        nonlocal STOPPED, RETURNCODE
        # print("HT_TASK_RUN_CONTROLLED: got SIGINT signal, shutting down", flush=True)
        STOPPED = 1
        RETURNCODE = 100
        # TODO: trap - INT

    if STDOUTCHECKER == '--':
        STDOUTCHECKER = ""

    BASHPID = os.getpid()
    os.environ["HT_SIGNAL_PID"] = str(BASHPID)

    print("HT_TASK_RUN_CONTROLLED: Starting with PID {} and timeout {}".format(BASHPID, TIMEOUT), flush=True)

    def timeout_process(TIMEOUT):
        TIMEOUT_EARLY_STOP = 0

        def timeout_sigterm_handler(*args):
            nonlocal TIMEOUT_EARLY_STOP
            TIMEOUT_EARLY_STOP = 143

        def timeout_sigint_handler(*args):
            nonlocal TIMEOUT_EARLY_STOP
            TIMEOUT_EARLY_STOP = 300

        signal.signal(signal.SIGTERM, timeout_sigterm_handler)
        signal.signal(signal.SIGINT, timeout_sigint_handler)

        t0 = time.time()
        while time.time() - t0 < TIMEOUT:
            time.sleep(1)
            if TIMEOUT_EARLY_STOP:
                break

        print("HT_TASK_RUN_CONTROLLED: TIMEOUT watchdog wait stopped with code: {}".format(TIMEOUT_EARLY_STOP), flush=True)

        if TIMEOUT_EARLY_STOP == 0:
            os.kill(int(os.environ["HT_SIGNAL_PID"]), signal.SIGUSR2)
            sys.exit(signal.SIGUSR2)
        else:
            # Prints are not safe inside signal handler functions!
            # E.g. the following error can happen:
            # RuntimeError: reentrant call inside <_io.BufferedWriter name='<stdout>'>
            # Solution is to move prints out of the handler functions.
            if TIMEOUT_EARLY_STOP == 143:
                print("HT_TASK_RUN_CONTROLLED: TIMEOUT watchdog process got term signal.", flush=True)
            elif TIMEOUT_EARLY_STOP == 300:
                print("HT_TASK_RUN_CONTROLLED: TIMEOUT watchdog process got int signal.", flush=True)
            sys.exit(TIMEOUT_EARLY_STOP)

    def checker_process(CHECKER, i, timeout_pid):
        returncode = CHECKER("ht.tmp.msgs.{}".format(i), timeout_pid)
        if returncode == 2:
            print("HT_TASK_RUN_CONTROLLED - CHECKER {} EXITED WITH ERROR, STOPPING RUN.".format(CHECKER.__name__), flush=True)
            os.kill(int(os.environ["HT_SIGNAL_PID"]), signal.SIGUSR1)
            sys.exit(signal.SIGUSR1)
        else:
            sys.exit(0)

    def stdoutchecker_process(run_args, STDOUTCHECKER, timeout_pid, run_pid):
        p = subprocess.Popen(run_args, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        run_pid.value = p.pid

        def stdout_sigterm_handler(*args):
            nonlocal p
            p.terminate()

        def stdout_sigint_handler(*args):
            nonlocal p
            p.terminate()

        signal.signal(signal.SIGTERM, stdout_sigterm_handler)
        signal.signal(signal.SIGINT, stdout_sigint_handler)

        if isinstance(STDOUTCHECKER, types.FunctionType):
            returncode = STDOUTCHECKER("ht.tmp.msgs.stdout", timeout_pid, p)
            if returncode == 2:
                print("HT_TASK_RUN_CONTROLLED - STDOUTCHECKER EXITED WITH ERROR, STOPPING RUN.", flush=True)
                os.kill(int(os.environ["HT_SIGNAL_PID"]), signal.SIGUSR1)
                sys.exit(signal.SIGUSR1)
            else:
                sys.exit(0)
        else:
            with open("stdout.out", "w") as f:
                for line in p.stdout:
                    line = line.decode().rstrip()
                    f.write(line)
                    f.flush()
                    sys.stdout.write(line)
                    sys.stdout.flush()
            sys.exit(0)

    ############################################################################

    p_all = []
    p_timeout = mp.Process(name="TIMEOUT", target=timeout_process, args=(TIMEOUT,), daemon=True)
    p_all.append(p_timeout)
    p_timeout.start()
    print("HT_TASK_RUN_CONTROLLED: Timeout watchdog started with pid: {}".format(p_timeout.pid), flush=True)

    signal.signal(signal.SIGUSR1, sigusr1_handler)
    signal.signal(signal.SIGUSR2, sigusr2_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigint_handler)
    # atexit.register(kill_timeout_process, p_timeout.pid)

    if "--" not in args:
        print("HT_TASK_RUN_CONTROLLED need one argument named " +
              "'--' to separate CHECKERS and command to run.", flush=True)
        sys.exit(0)

    i = 0
    p_checkers = []
    for CHECKER in args:
        if CHECKER == "--":
            break
        i += 1
        if os.path.exists("ht.tmp.msgs.{}".format(i)):
            os.remove("ht.tmp.msgs.{}".format(i))

        p = mp.Process(name=CHECKER, target=checker_process, args=(CHECKER, i, p_timeout.pid), daemon=True)
        p_checkers.append(p)
        p_all.append(p)
        p.start()

    run_args = " ".join(args[i + 1:])
    run_pid = mp.Value('i', -9999)
    p_stdout = mp.Process(name="STDOUT_CHECKER", target=stdoutchecker_process, args=(run_args,
                          STDOUTCHECKER, p_timeout.pid, run_pid), daemon=True)
    p_all.append(p_stdout)
    p_stdout.start()

    print("HT_TASK_RUN_CONTROLLED: Started main process with pid: {}".format(BASHPID), flush=True)
    # atexit.register(kill_script, p_timeout.pid, BASHPID)

    # Wait until the first subprocess exits and capture the exitcode
    i = 0
    while True:
        p = p_all[i]
        if not p.is_alive():
            PROCEXITCODE = p.exitcode
            break
        i += 1
        i = i % len(p_all)
        time.sleep(1)

    # Move prints out of the signal handler functions, because
    # printing there can cause RuntimeErrors
    if STOPPED == 1 and RETURNCODE == 2:
        print("HT_TASK_RUN_CONTROLLED: got USR1 signal, stopping", flush=True)

    elif STOPPED == 1 and TIMEDOUT == 1 and RETURNCODE == 99:
        print("HT_TASK_RUN_CONTROLLED: got USR2 signal, stopping", flush=True)

    elif STOPPED == 1 and RETURNCODE == 3:
        print("HT_TASK_RUN_CONTROLLED: got SIGTERM signal, shutting down", flush=True)
        # TODO: trap - TERM

    elif STOPPED == 1 and RETURNCODE == 100:
        print("HT_TASK_RUN_CONTROLLED: got SIGINT signal, shutting down", flush=True)
        # TODO: trap - INT

    if STOPPED == 1:
        print("HT_TASK_RUN_CONTROLLED: Run was STOPPED.", flush=True)
    else:
        print("HT_TASK_RUN_CONTROLLED: Run finished (or timed out.)", flush=True)

    if TIMEDOUT == 1:
        print("HT_TASK_RUN_CONTROLLED: Run timed out.", flush=True)
        with open("ht.tmp.msgs.timeout", "w") as f:
            f.write("TIMEOUT")
    else:
        print("HT_TASK_RUN_CONTROLLED: Run did not time out.", flush=True)

    # Allow a short delay to let timeout process run to completion
    time.sleep(1)

    if p_timeout.is_alive():
        print("HT_TASK_RUN_CONTROLLED: Timeout process pid {} was still alive (killed now)".format(p_timeout.pid), flush=True)
        p_timeout.terminate()
    else:
        print("HT_TASK_RUN_CONTROLLED: Timeout process NOT alive.", flush=True)

    if check_pid(run_pid.value):
        print("HT_TASK_RUN_CONTROLLED: Run process still alive, sent SIGTERM, sheduled definite SIGKILL in 10 secs.", flush=True)
        os.kill(run_pid.value, signal.SIGTERM)
        time.sleep(10)
        if check_pid(run_pid.value):
            os.kill(run_pid.value, signal.SIGKILL)
    else:
        print("HT_TASK_RUN_CONTROLLED: Run process no longer alive.", flush=True)
        if STOPPED != 1 and TIMEDOUT != 1:
            RETURNCODE = PROCEXITCODE

    print("HT_TASK_RUN_CONTROLLED: Waiting for all checker processes to catch up and finish.", flush=True)

    for p in p_all:
        p.terminate()
        p.join()

    tmp_msg_files = glob.glob("ht.tmp.msgs.*")
    with open("ht.controlled.msgs", "w") as f_dest:
        for file in tmp_msg_files:
            with open(file, "r") as f_src:
                f_dest.write(f_src.read())
            os.remove(file)

    sys.stderr.write("HT_TASK_RUN_CONTROLLED: ends\n")
    return RETURNCODE


def HT_TASK_COMPRESS(method="bz2"):
    if method == "bz2":
        import bz2
    elif method == "zstd":
        import pyzstd
    else:
        sys.stdout.write("HT_TASK_COMPRESS: Unknown compression method {}. Files will not be compressed!".format(method))
        sys.stdout.flush()
        return

    for root, dirs, files in os.walk("."):
        for f in files:
            if not f.startswith("ht."):
                fn = os.path.join(root, f)
                if method == 'bz2':
                    with open(fn, "rb") as f_src:
                        with bz2.open(fn + ".bz2", "wb") as f_dest:
                            f_dest.write(f_src.read())
                elif method == 'zstd':
                    with open(fn, "rb") as f_src:
                        with open(fn + ".zst", "wb") as f_dest:
                            pyzstd.compress_stream(f_src, f_dest)
                os.remove(fn)

    if os.path.exists("ht.RUNLOG"):
        if method == 'bz2':
            with open("ht.RUNLOG", "rb") as f_src:
                with bz2.open("ht.RUNLOG" + ".bz2", "wb") as f_dest:
                    f_dest.write(f_src.read())
        elif method == 'zstd':
            with open("ht.RUNLOG", "rb") as f_src:
                with open("ht.RUNLOG" + ".zst", "wb") as f_dest:
                    pyzstd.compress_stream(f_src, f_dest)
            os.remove("ht.RUNLOG")
