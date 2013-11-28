#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)
# This program adds two (geometrically identical) structures to an sqlite database
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

import argparse

def main():
    parser = argparse.ArgumentParser(description="Example program creating two structures in an sqlite database.")
    parser.add_argument('-debug', action='store_true')
    args = parser.parse_args()    

    debug = args.debug

    backend = httk.db.backend.Sqlite('database.sqlite')
    store= httk.db.store.SqlStore(backend)

    # When you writing programs that *change* a database, always do the following to "register" the program
    # using the database. This makes it easier to trace what piece of code is responsible for something a later stage.
    codeobj = httk.db.register_code(store, 'db_import_2','1.0',['httk'])        
    print "==== Name of this code:",codeobj.name

    today = datetime.datetime.today().isoformat()
    print "==== Db import program started: "+today
    print "(Note: this program is quite slow when run with a missing database.sqlite, since the database then needs to be setup from scratch.)"

    # This is good practice if you are going to add several things to the database, nothing is written to the database until 'commit' is called.
    store.delay_commit()

    # We are now going to create three structures
    
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

    PbTiO3 = Structure.create(cell=cell,coordgroups=coordgroups,assignments=assignments,volume=62.79,spacegroup='P m -3 m')

    # Don't try to create DbStructure objects yourself, always get a Structure object first and then use 'use'.
    newdbimport = httk.db.DbStructure.use(PbTiO3,store=store,reuse=True)    
    # Note: creating new tables takes time, and for most database layers is not 'safe' in the sense that the database is only changed 

    # For the second structure we re-use everything except the assignment
    assignments = ['Pb','Zr','O']
    PbZrO3 = Structure.create(cell=cell,coordgroups=coordgroups,assignments=assignments,volume=60.24,spacegroup='P m -3 m')
    newdbimport = httk.db.DbStructure.use(PbZrO3,store=store,reuse=True)    

    cell = [[1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]]

    coordgroups = [[
                   [0.0, 0.0, 0.0]
                ],[
                   [0.25, 0.25, 0.25]
                ]]

    assignments = ['Zr','O']

    ZnO2 = Structure.create(cell=cell,coordgroups=coordgroups,assignments=assignments,volume=132.65,spacegroup='F m -3 m')
    newdbimport = httk.db.DbStructure.use(ZnO2,store=store,reuse=True) 

    print "==== Committing changes to database."
    store.commit()
    print "==== Commit complete."

if __name__ == "__main__":
    main()




