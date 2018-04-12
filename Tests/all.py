#!/usr/bin/env python
import argparse, unittest

import test_examples

logdata = []
test_examples.logdata = logdata

ap = argparse.ArgumentParser(description="Run all tests")
ap.add_argument("--debug", help = 'Debug output', action='store_true')
args, leftovers = ap.parse_known_args()

try:
    suite = unittest.TestLoader().loadTestsFromTestCase(test_examples.TestExamples)
    unittest.TextTestRunner(verbosity=2).run(suite)        
finally:
    if args.debug:
        print("") 
        print("Loginfo:")
        print("-------------------------------------------------------")
        print("\n".join(logdata))
        print("-------------------------------------------------------")
