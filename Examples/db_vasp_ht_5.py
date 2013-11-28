#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)
# This program makes a simple search in the database created by db_import_2.py and generates vasp input for high-throughput runs
# TODO: WARNING this program uses features not yet working as they should in httk
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

        # Convert the database structure object into a regular structure object to do operations on it, etc.
        struct = Structure.use(dbstructure) 

        def get_magmom(symbol):
            return 8

        dirname = vasp.instantiate_step1('./runs', 'vasp-relax-formenrg', struct.formula+"_"+struct.hexhash)

        ioa = httk.IoAdapterFileWriter.use(os.path.join(dirname,"POSCAR"))
        httk.iface.vasp_if.structure_to_poscar(ioa, struct)            

        # Setup POTCAR, this should be done by a call within the run template setup.py
        ioa = httk.IoAdapterFileWriter.use(os.path.join(dirname,"POTCAR"))
        f = ioa.file            
        spieces_counts=[]
        magmoms=[]
        for i in range(len(struct.p1assignments)):
            assignment = struct.p1assignments[i]
            count = struct.p1counts[i]
            symbol = htdata.periodictable.atomic_symbol(assignment)
            f.write(httk.iface.vasp_if.get_pseudopotential(symbol))
            spieces_counts.append(count)
            magmoms.append(str(count)+"*"+str(get_magmom(symbol)))

        data = {}
        data['VASP_SPIECES_COUNTS'] = " ".join(map(str,spieces_counts))
        data['VASP_MAGMOM'] = " ".join(map(str,magmoms))
                            
        httk.exe.vasp.instantiate_step2(dirname,struct.formula+"_"+struct.hexhash,data)

if __name__ == "__main__":
    main()




