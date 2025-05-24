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
httk_examples_dir = os.path.join(top,'Examples')

def run(command,args=[]):
    args = list(args)
    popen = subprocess.Popen([command] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return popen.communicate()

def execute(self, command, *args):
    os.environ["HTTK_DONT_HOLD"] = "1"
    os.chdir(os.path.dirname(command))
    out,err = run("python",[os.path.join(httk_examples_dir,command)]+list(args))
    self.assertTrue(len(err.strip())==0, msg=err)

class TestExamples(unittest.TestCase):
    pass

test_programs = []
for root, d, files in os.walk(httk_examples_dir):
    for f in fnmatch.filter(files, "*.py"):
        fullname = os.path.join(root,f)
        if not f.startswith('_'):
            test_programs += [fullname]

def function_factory(program):
    def exec_func(slf):
        execute(slf,program)
    return exec_func

ignore_programs = ['1_simple_things/6_write_cif.py', # Need to fix symmetry warning
                   '2_visualization/2_ase_visualizer.py', # Ase visualizer stops forever waiting for user input
                   '6_website/4_search_app/run_as_app.py', # The qt apps don't work that well in testing
                   '6_website/5_widgets/run_as_app.py', # The qt apps don't work that well in testing
                   '6_website/3_hello_world_app/run_as_app.py', # The qt apps don't work that well in testing
                   '3_external_libraries/2_phasediagram_from_materialsproject.py', # Requires pymatgen
                   '3_external_libraries/3_phasediagram_pymatgen.py', # Requires pymatgen
                   '5_calculations/1_simple_vasp.py', '5_calculations/2_ht_vasp.py' # Requires pseudopotentials
                  ]

if 'HTTK_TESTS_SKIP_EXTERNAL' in os.environ and os.environ['HTTK_TESTS_SKIP_EXTERNAL'] not in [ "", "0" ]:
    ignore_programs+='2_visualization/1_structure_visualizer.py'

for program in test_programs:

    exec_func = function_factory(program)
    program_path = os.path.dirname(program)
    program_file = os.path.basename(program)
    rel_program = os.path.relpath(program, httk_examples_dir)

    if rel_program in ignore_programs:
        continue

    program_name, ext = os.path.splitext(rel_program)
    program_name = program_name.replace('/','_')
    setattr(TestExamples,'test_'+program_name,exec_func)

#############################################################################


if __name__ == '__main__':

    ap = argparse.ArgumentParser(description="Example tests")
    args, leftovers = ap.parse_known_args()

    suite = unittest.TestLoader().loadTestsFromTestCase(TestExamples)
    unittest.TextTestRunner(verbosity=2).run(suite)


