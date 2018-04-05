#!/usr/bin/env python
import os, errno

import httk
import httk.db
from httk.atomistic import Structure

# Remove example database
try:
    os.remove('example.sqlite')
except OSError as e:
    if e.errno != errno.ENOENT:
        raise

backend = httk.db.backend.Sqlite ('example.sqlite')
store = httk.db.store.SqlStore (backend)

struct = Structure.io.load("example.cif")
store.save(struct)

search = store.searcher()
search_struct = search.variable(Structure)
search.add(search_struct.uc_nbr_atoms<40)

search.output (search_struct,'structure ')

for match in search:
    structure = match[0][0]
    print("Found:",struct.formula)




