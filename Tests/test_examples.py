#!/usr/bin/env python
import sys, os, unittest, subprocess, argparse
from contextlib import contextmanager
from StringIO import StringIO

logdata = []

here = os.path.abspath(os.path.dirname(__file__))
examples_path_rel = '../Examples'
examples_path = os.path.join(here,examples_path_rel)

def run(command,args=[]):
    global logdata

    logdata += ['Try to run: ' + command]
    p = subprocess.Popen([command] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate()

class TestExamples(unittest.TestCase):

    def test_example_import_httk(self):
        out,err = run(os.path.join(examples_path,'0_import_httk','0_import_httk.py'))
        self.assertTrue(err.strip() == '')
        self.assertTrue(out.startswith(expected_output_example_import_httk))

    def test_example_vectors(self):
        out,err = run(os.path.join(examples_path,'1_simple_things','0_vectors.py'))
        self.assertTrue(err.strip() == '')
        if sys.version_info[0] < 3:
            self.assertTrue(out.startswith(expected_output_example_vectors_python2),msg="\n----\n"+out+"\n----\n .VS. \n----\n"+expected_output_example_vectors_python2+"\n----\n")
        else:
            self.assertTrue(out.startswith(expected_output_example_vectors_python3),msg="\n----\n"+out+"\n----\n .VS. \n----\n"+expected_output_example_vectors_python3+"\n----\n")


expected_output_example_import_httk = "Imported httk version: "

expected_output_example_vectors_python2 = \
"""
(1/1)*((2, 3, 5), (3, 5, 4), (4, 6, 7))
(1/1)*[[2, 3, 5], [3, 5, 4], [4, 6, 7]]
('MAX in row [1]:', FracVector(5,1))
('MAX in all of a', FracVector(7,1))
<class 'httk.core.vectors.mutablefracvector.MutableFracVector'>
(1/1)*((2, 3, 5), (3, 5, 4), (4, 6, 7))
(1/1)*[[2, 3, 5], [3, 5, 4], [4, 4711, 23]]
(1/2251799813685248)*[[571957152676053L, 6755399441055744, 11258999068426240], [6755399441055744, 11258999068426240, 9007199254740992], [9007199254740992, 10608228922271203328L, 51791395714760704]]
(1/749577174842692567578302780529767549997370209992704)*[[-213847376293519380898725103374556755274499692167168L, 268162714487137390132279234227926742184681497690112L, -148433760041419827630061740822747494183805648896L], [-605153021707326989568713251046585937826284568576L, -161655782666647839035194860275750777625681854464L, 159669053878401143651493291145040556505832620032L], [161141973497273694411004719094725798878157624836096L, -13525672426346590905839736963158480667136468451328L, -88260997316936558841820308314240074994436538368L]]
(1/2)*((5, 7, 11), (7, 11, 9), (9, 13, 15))
""".strip()

expected_output_example_vectors_python3 = \
"""
(1/1)*((2, 3, 5), (3, 5, 4), (4, 6, 7))
(1/1)*[[2, 3, 5], [3, 5, 4], [4, 6, 7]]
'MAX in row [1]:', FracVector(5,1)
'MAX in all of a', FracVector(7,1)
<class 'httk.core.vectors.mutablefracvector.MutableFracVector'>
(1/1)*((2, 3, 5), (3, 5, 4), (4, 6, 7))
(1/1)*[[2, 3, 5], [3, 5, 4], [4, 4711, 23]]
(1/2251799813685248)*[[571957152676053, 6755399441055744, 11258999068426240], [6755399441055744, 11258999068426240, 9007199254740992], [9007199254740992, 10608228922271203328, 51791395714760704]]
(1/749577174842692567578302780529767549997370209992704)*[[-213847376293519380898725103374556755274499692167168, 268162714487137390132279234227926742184681497690112, -148433760041419827630061740822747494183805648896], [-605153021707326989568713251046585937826284568576, -161655782666647839035194860275750777625681854464, 159669053878401143651493291145040556505832620032], [161141973497273694411004719094725798878157624836096, -13525672426346590905839736963158480667136468451328, -88260997316936558841820308314240074994436538368]]
(1/2)*((5, 7, 11), (7, 11, 9), (9, 13, 15))
""".strip()


#############################################################################


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Examples tests")
    ap.add_argument("--debug", help = 'Debug output', action='store_true')
    args, leftovers = ap.parse_known_args()

    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestExamples)
        unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        if args.debug:
            print("")
            print("Loginfo:")
            print(logdata)
