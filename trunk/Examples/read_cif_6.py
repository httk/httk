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
    parser.add_argument('file', metavar='run', nargs='+', help='filenames or directories to import')
    args = parser.parse_args()    

    debug = args.debug

    today = datetime.datetime.today().isoformat()
    print "==== One_structure program started: "+today

    for i in range(len(args.file)):
        filename = args.file[i]
        try:
            struct = httk.io.cif_to_struct(filename,backends=['cif2cell'])
            print "The formula is:",struct.formula+" ("+struct.abstract_formula+")"
        except Exception as e:
            if debug: raise
            print "Failed to read "+filename+" due to error:"+str(e)
            

if __name__ == "__main__":
    main()
