#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)
# This program makes a simple search in the database created by db_import_2.py and generates vasp POSCARs from the found structures
# 
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

from httk.exe import vasp

import argparse

def main():
    parser = argparse.ArgumentParser(description="Example program searching in a database.")
    parser.add_argument('-debug', action='store_true')
    args = parser.parse_args()    

    debug = args.debug

    backend = httk.db.backend.Sqlite('database.sqlite')
    store= httk.db.store.SqlStore(backend)

    today = datetime.datetime.today().isoformat()
    print "==== Db search program started: "+today

    search = store.searcher()
    s_struct = httk.db.DbStructure.variable(search, 's_struct')
    s_proto = httk.db.DbPrototype.variable(search, 's_proto')

    # Find all small (less than 4 nonequivalent atoms in the unit cell) ordered compounds that contains Zr 
    search.add(s_struct.formula_parts.symbol == 'Zr')
    search.add(s_struct.extended == 0) # i.e., regular, ordered, crystal
    search.add(s_struct.sgprototype == s_proto)
    search.add(s_proto.site_count < 4)

    # The search returns the matched compound and structure objects under headers 'compound' and 'structure'
    search.output(s_struct,'structure')

    for match in search:
        dbstructure = match[0][0]

        struct = Structure.use(dbstructure) 
        filename = struct.formula+".vasp"
        httk.iface.vasp_if.structure_to_poscar(filename, struct)            

        print "==== Created / overwrote file: "+filename

if __name__ == "__main__":
    main()




