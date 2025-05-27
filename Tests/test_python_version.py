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

import os, sys, unittest, subprocess, argparse, codecs, re

if 'HTTK_TEST_EXPECT_PYVER' in os.environ:
    m = re.match(r"py(\d)(\d+)", os.environ.get("HTTK_TEST_EXPECT_PYVER"))
    if m:
        major, minor = m.groups()
        expect_pyver = str(major)+"."+str(minor)
    else:
        expect_pyver = "<could not parse env var HTTK_TEST_EXPECT_PYVER>"
else:
    expect_pyver=None

testdir = os.path.abspath(os.path.dirname(__file__))

def run(command,args=[]):
    args = list(args)
    popen = subprocess.Popen([command] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = popen.communicate()
    out = codecs.decode(out,'ascii')
    err = codecs.decode(err,'ascii')
    return out,err

class TestPythonVer(unittest.TestCase):
    def test_python_version_internal(self):

        self.assertTrue(expect_pyver is not None, msg="Environment variable HTTK_TEST_EXPECT_PYVER not set.")

        if expect_pyver == 'ignore':
            self.assertTrue(True)
        else:
            self.assertTrue(sys.version.startswith(expect_pyver+" ") or sys.version.startswith(expect_pyver+"."), msg=sys.version + " does not start with "+expect_pyver)
            #print("Internal python version string:"+str(sys.version))

    def test_python_version_exec(self):

        self.assertTrue(expect_pyver is not None, msg="Environment variable HTTK_TEST_EXPECT_PYVER not set.")

        if expect_pyver == 'ignore':
            self.assertTrue(True)
        else:
            out, err = run('python',['--version'])
            # Python2 prints version on stderr, Python3 on stdout...
            msg = out + err
            self.assertTrue(msg.startswith("Python "+expect_pyver+".") or msg.startswith("Python "+expect_pyver+" "), msg=msg + " does not start with "+expect_pyver)
            #print("Executable python version string:"+str(msg))

    def test_python_version_hashbang(self):

        self.assertTrue(expect_pyver is not None, msg="Environment variable HTTK_TEST_EXPECT_PYVER not set.")

        if expect_pyver == 'ignore':
            self.assertTrue(True)
        else:
            out, err = run(os.path.join(testdir,'python_versions/print_python_version.py'))
            self.assertTrue(out.startswith(expect_pyver+" ") or out.startswith(expect_pyver+"."), msg=out + " does not start with "+expect_pyver)
            #print("Hashbang python version string:"+out)


#############################################################################


if __name__ == '__main__':

    ap = argparse.ArgumentParser(description="Parser tests")
    args, leftovers = ap.parse_known_args()

    suite = unittest.TestLoader().loadTestsFromTestCase(TestPythonVer)
    unittest.TextTestRunner(verbosity=2).run(suite)
