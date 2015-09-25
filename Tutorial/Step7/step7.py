#!/usr/bin/env python

import httk, httk.db
from httk.atomistic import Structure

class StructureIsEdible(httk.HttkObject):
    @httk.httk_typed_init({'structure ':Structure,'is_edible':bool})
    def __init__ (self,structure,is_edible):
        self.structure = structure
        self.is_edible = is_edible

backend = httk.db.backend.Sqlite('example.sqlite')
store = httk.db.store.SqlStore(backend)
tablesalt = httk.load ('NaCl.cif')
arsenic = httk.load ('As.cif')
edible = StructureIsEdible(tablesalt,True)
store.save (edible)
edible = StructureIsEdible(arsenic,False)
store.save(edible)
