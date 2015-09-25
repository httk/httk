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

from httk.core import citation
citation.add_ext_citation('Jmol', "An open-source Java viewer for chemical structures in 3D. http://www.jmol.org/")

import os, time, threading, subprocess, signal, sys

import httk
from httk.iface.jmol_if import *
import distutils.spawn
from httk import config
from httk.core.basic import create_tmpdir, destroy_tmpdir, micro_pyawk
from command import Command

try:
    jmol_path=config.get('paths', 'jmol')
    jmol_dirpath, jmol_filename = os.path.split(jmol_path)

except Exception:
    jmol_path = distutils.spawn.find_executable("jmol") 
    if jmol_path == None:
        raise Exception("jmol_ext: No path is set for jmol in httk configuration, and no jmol executable was found.")

jmol_version = None
jmol_version_date = None

def check_works():
    global jmol_version, jmol_version_date

    if jmol_path == "" or not os.path.exists(jmol_path):
        raise ImportError("httk.external.jmol imported without access to a jmol binary to run.")
    
    out, err, completed = Command(jmol_path,['-n','-o'],cwd='./').run(15,debug=False)
    if completed == None or completed != 0:
        raise Exception("jmol_ext: Could not execute jmol. Return code:"+str(completed)+" out:"+str(out)+" err:"+str(err))

    def get_version(results,match):
        results['version'] = match.group(1)
        results['version_date'] = match.group(2)

    results = micro_pyawk(os.path.join(httk.IoAdapterString(out)),[
            ['^ *Jmol Version: ([^ ]+) +([^ ]+)',None,get_version],
          ],debug=False)

    if not 'version' in results:
        raise Exception("jmol_ext: Could not extract version string from jmol -n -o. Return code:"+str(completed)+" out:"+str(out)+" err:"+str(err))        

    jmol_version = results['version']
    jmol_version_date = results['version_date']

check_works()

def run(cwd, args,timeout=None):
    #print "COMMAND JMOL"
    out,err,completed = Command(jmol_path,args,cwd=cwd).run(timeout)
    #print "COMMMDN JMOL END"
    return out, err, completed    

def _jmol_stophook(command):
    # Lets be nice and let jmol close down on its own
    command.send("exitJmol;\n")    
    command.wait_finish(timeout=5)

def start(cwd='./', args=['-I']):

    version = jmol_version.split('.')
    if int(version[0])<12 or (int(version[0])==12 and int(version[1])<3):
        raise Exception("jmol_ext.start_jmol: requires at least jmol version 12.3, your version:"+str(jmol_version))

    command = Command(jmol_path,args,cwd=cwd,stophook=_jmol_stophook)
    command.start()
    
    return command

def main():
    print("VERSION:",jmol_version," DATE:",jmol_version_date)
    jmol = start()
    jmol.send("background '#F5F5F5';\n")
    time.sleep(1)
    print jmol.receive()
    time.sleep(3)
    jmol.send("background '#FFFFFF';\n")
    time.sleep(3)
    jmol.send("background '#FF0000';\n")
    print "Waiting..."
    time.sleep(1)
    print "Print output"
    print jmol.receive()
    print "Killing..."
    jmol.stop()
    print "Killed."

if __name__ == "__main__":
    main()
    
    
