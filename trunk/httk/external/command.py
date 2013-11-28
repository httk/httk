# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2013 Rickard Armiento
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

import threading, subprocess

class Command(object):
    def __init__(self, cmd, args, cwd=None, inputstr = None):
        self.args = args
        self.cmd = cmd
        self.process = None
        self.out = None
        self.err = None
        self.inputstr = inputstr
        self.cwd = cwd

    def run(self, timeout,debug=False):
        def target():
            self.process = subprocess.Popen([self.cmd]+self.args, stdout=subprocess.PIPE, 
                                       stdin=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cwd)

            if debug:
                print "Launching subprocess with input",self.inputstr
            
            self.out, self.err = self.process.communicate(input=self.inputstr)

            if debug:
                print "Got back",self.out,self.err

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            thread.join()
            completed = False
        else:
            completed = True
        
        return self.out, self.err, completed


