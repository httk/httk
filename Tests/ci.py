#!/usr/bin/env python
import unittest, argparse

import test_python_version
import test_examples
import test_structreading
import test_httk_src_inline

logdata = []
test_examples.logdata = logdata

ap = argparse.ArgumentParser(description="Run all tests")
ap.add_argument("--debug", help = 'Debug output', action='store_true')
args, leftovers = ap.parse_known_args()

try:

    suite = unittest.TestLoader().loadTestsFromTestCase(test_python_version.TestPythonVer)

    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(test_examples.TestExamples))

    unittest.TextTestRunner(verbosity=2).run(suite)

finally:
    if args.debug:
        print("")
        print("Loginfo:")
        print("-------------------------------------------------------")
        print("\n".join(logdata))
        print("-------------------------------------------------------")
