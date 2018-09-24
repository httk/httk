# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2015 Rickard Armiento
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

import threading, subprocess, sys, os, signal, glob, distutils.spawn
import httk.core
from httk.core.basic import is_sequence
from httk import config
from httk.config import httk_root    
import platform

if httk.core.python_major_version >= 3:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty


class Command(object):

    def __init__(self, cmd, args, cwd=None, inputstr=None, stophook=None):
        self.args = args
        self.cmd = cmd
        self.process = None
        self.out = None
        self.err = None
        self.inputstr = inputstr
        self.cwd = cwd
        self.stophook = stophook

    def run(self, timeout, debug=False):

        self.process = subprocess.Popen([self.cmd]+self.args, stdout=subprocess.PIPE, 
                                        stdin=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cwd)
        
        def target():
            if debug:
                print "Command: Launching subprocess:", self.cmd, " with args ", self.args
            
            if debug:
                print "Command: Running communicate with inputstr:", self.inputstr
            
            self.out, self.err = self.process.communicate(input=self.inputstr)

            if debug:
                print "Command: Got back", self.out, self.err

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            thread.join()
            completed = None
        else:
            if self.process is not None:
                completed = self.process.returncode
            else:
                completed = None

        self.process = None
                
        return self.out, self.err, completed

    def start(self):

        if self.process is not None:
            self.stop()

        # I really don't know if the windows support works as I have not tested anything on Windows myself
        kwargs = {}
        if platform.system() == 'Windows':
            # from msdn [1]
            CREATE_NEW_PROCESS_GROUP = 0x00000200  # note: could get it from subprocess
            DETACHED_PROCESS = 0x00000008          # 0x8 | 0x200 == 0x208
            kwargs['creationflags'] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        elif sys.version_info < (3, 2):  # assume posix
            kwargs['preexec_fn'] = os.setsid
            kwargs['close_fds'] = 'posix' in sys.builtin_module_names
        else:  # Python 3.2+ and Unix
            kwargs['start_new_session'] = True        
        
        def enqueue_output(out, queue):
            for line in iter(out.readline, b''):
                queue.put(line)
            out.close()
        
        self.process = subprocess.Popen([self.cmd]+self.args, stdout=subprocess.PIPE, 
                                        stdin=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cwd, bufsize=1, **kwargs)
    
        self.output_queue = Queue()
        self.output_thread = threading.Thread(target=enqueue_output, args=(self.process.stdout, self.output_queue))
        self.output_thread.start()

    def wait_finish(self, timeout=None):
        if self.process is not None:                 
            def target():            
                self.process.wait()
    
            thread = threading.Thread(target=target)
            thread.start()
    
            thread.join(timeout)
            if thread.is_alive():
                self._terminate()
                thread.join()

    def _terminate(self):
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except OSError:
                # Possible racing condition, the process may have died
                pass
            try:
                self.process.terminate()
            except OSError:
                # Possible racing condition, the process may have died
                pass
                
        self.output_thread.join()
        self.output_thread = None
        self.output_queue = None
        self.process = None            
    
    def stop(self):
        if self.process is not None:                 
            
            if self.stophook is not None:
                self.stophook(self)
            
            self._terminate()            
    
    def receive(self):
        lines = ""
        try:
            while(True):
                line = self.output_queue.get_nowait()
                lines += line
        except Empty:
            pass
        
        return lines
    
    def send(self, command):
        self.process.stdin.write(command)

    @property
    def stdin(self):
        return self.process.stdin


def find_executable(executables, config_name):
    if not is_sequence(executables):
        executables = [executables]
    
    path_conf = config.get('paths', config_name)
    if path_conf is not None and path_conf != "":
        paths = glob.glob(os.path.expandvars(os.path.expanduser(path_conf)))
        if len(paths) == 0:
            raise IOError("find_executable: Configured executable in httk.cfg for "+str(config_name)+" not found in "+path_conf)
        return paths[0]
    else:
        try:
            path = os.path.join(httk_root, 'External')
            externaldirs = [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]
            extvers = [name.split('-')[1] for name in externaldirs if name.split('-')[0] == config_name]    
            extvers = sorted(extvers, key=lambda x: map(int, x.split('.')))    
            bestversion = config_name+'-'+extvers[-1]
            for executable in executables:
                p = os.path.join(path, bestversion, executable)
                if os.path.exists(p):
                    return p
        except Exception:
            pass

        for executable in executables:        
            path = distutils.spawn.find_executable(executable) 
            if path is not None:
                return path

        raise Exception("find_executable: executable for "+str(config_name)+" not found. No path set in httk.cfg, and no binary '"+str(executable)+"' found in subdirectories to External/, or otherwise in the system path.")
