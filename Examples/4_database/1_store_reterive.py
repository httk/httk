#!/usr/bin/env python

import httk, httk.db
from httk.atomistic import Structure

backend = httk.db.backend.Sqlite('example.sqlite')
store = httk.db.store.SqlStore(backend)
tablesalt = httk.load('../../Tutorial/Step7/NaCl.cif')
tablesalt.add_tag('common name', 'salt')
arsenic = httk.load('../../Tutorial/Step7/As.cif')
store.save(tablesalt)
store.save(arsenic)

# Search for anything with Na (cf. the search for a material system in tutorial step6, where all symbols must be in a set, 'add' vs. 'add_all'.)
search = store.searcher()
search_struct = search.variable(Structure)
search.add(search_struct.formula_symbols.is_in('Na'))

search.output(search_struct, 'structure')

for match, header in list(search):
    struct = match[0]
    print("Found structure", struct.formula, [str(struct.get_tags()[x]) for x in struct.get_tags()])
