#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)
# This program just creates a structure object
import sys, os.path, inspect, datetime

# Workaround to allow this program to be run in a subdirectory of the httk directory even if the paths are not setup correctly.
try:
    import httk
    from httk.core import *
except Exception:
    _realpath = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
    sys.path.insert(1, os.path.join(_realpath,'..'))
    import httk
    from httk.core import *

import argparse

def main():
    parser = argparse.ArgumentParser(description="Example program creating a simple structure object and prints out the abstract formula.")
    parser.add_argument('-debug', action='store_true')
    args = parser.parse_args()    

    debug = args.debug

    today = datetime.datetime.today().isoformat()
    print "==== One_structure program started: "+today

    # First we create a structure object in P1 symmetry. This is not *wrong*, but also
    # not ideal if you know the full symmetry-representation of the structure.

    cell = [[1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]]
    coordgroups = [[
                   [0.5, 0.5, 0.5]
                ],[
                   [0.0, 0.0, 0.0]
                ],[
                   [0.5, 0.0, 0.0],[0.0, 0.5, 0.0],[0.0, 0.0, 0.5]
                ]]
    assignments = ['Pb','Ti','O']


    struct = Structure.create(cell=cell,coordgroups=coordgroups,assignments=assignments,volume=62.79)

    print "The formula is:",struct.formula+" ("+struct.abstract_formula+")"

    # Now we create the same structure with full symmetry, the hall symbol of the group is 'P m -3 m'

    cell = [[1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]]
    coordgroups = [[
                   [0.5, 0.5, 0.5]
                ],[
                   [0.0, 0.0, 0.0]
                ],[
                   [0.5, 0.0, 0.0]
                ]]
    assignments = ['Pb','Ti','O']

    struct = Structure.create(cell=cell,coordgroups=coordgroups,assignments=assignments,volume=62.79,spacegroup='P m -3 m')
    print "The formula is:",struct.formula+" ("+struct.abstract_formula+")"

if __name__ == "__main__":
    main()
