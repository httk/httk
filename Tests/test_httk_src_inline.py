#!/usr/bin/env python
#
# Copyright 2019 Rickard Armiento
#
# This file is part of a Python candidate reference implementation of
# the optimade API [https://www.optimade.org/]
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os, unittest, subprocess, argparse, fnmatch

top = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
httk_src_dir = os.path.join(top,'src','httk')

def run(command,args=[]):
    args = list(args)
    popen = subprocess.Popen([command] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return popen.communicate()

def execute(self, command, *args):
    os.chdir(os.path.dirname(command))
    out,err = run("python",[os.path.join(httk_src_dir,command)]+list(args))
    self.assertTrue(len(err.strip())==0, msg=err)

class TestHttkSrcInline(unittest.TestCase):
    pass

test_programs = []
for root, d, files in os.walk(httk_src_dir):
    for f in fnmatch.filter(files, "*.py"):
        fullname = os.path.join(root,f)
        if not f.startswith('_'):
            with open(fullname,'r') as ff:
                lines = ff.readlines()
                if 'if __name__ == "__main__":\n' in lines:
                    test_programs += [fullname]

def function_factory(program):
    def exec_func(slf):
        execute(slf,program)
    return exec_func

for program in test_programs:
    exec_func = function_factory(program)
    program_path = os.path.dirname(program)
    program_file = os.path.basename(program)
    rel_program = os.path.relpath(program, httk_src_dir)
    program_name, ext = os.path.splitext(rel_program)
    program_name = program_name.replace('/','_')
    setattr(TestHttkSrcInline,'test_'+program_name,exec_func)


#############################################################################


if __name__ == '__main__':

    ap = argparse.ArgumentParser(description="Example tests")
    args, leftovers = ap.parse_known_args()

    suite = unittest.TestLoader().loadTestsFromTestCase(TestHttkSrcInline)
    unittest.TextTestRunner(verbosity=2).run(suite)


