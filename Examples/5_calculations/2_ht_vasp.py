#!/usr/bin/env python

import httk
import httk.db
from httk.atomistic import Structure
import httk.task

# Must be updated to your path to poscars, OR, set to None if you have 
# 'vasp_pseudolib' configured in httk.cfg
poscarspath = '/opt/vasp/Pseudopotentials.raw/POT_GGA_PAW_PBE/'
#poscarspath = None

backend = httk.db.backend.Sqlite('../../Tutorial/tutorial_data/tutorial.sqlite')
store = httk.db.store.SqlStore(backend)

search = store.searcher()
search_struct = search.variable(Structure)
search.add_all(search_struct.formula_symbols.is_in('O', 'Ca', 'Ti'))

search.output(search_struct, 'structure')

for match, header in search:
    struct = match[0]
    
    try:
        dir = httk.task.create_batch_task('Runs/', 't:vasp/batch/vasp-relax-two', {"structure": struct}, name=struct.hexhash, overwrite_head_dir=True)
        print("Generated run for:", struct.formula+" in "+dir)
    except Exception as e:
        raise
        print e
        pass
