#!/usr/bin/env python

import httk, httk.db
from httk.atomistic import Structure, UnitcellStructure

# Note, we use a UnitcellStructure here so that no external symmetry finder is needed to derive the Wyckoff sequences,
# with a symmetry finder, changing it to Structure is fine.
class StructureIsEdible(httk.HttkObject):
    @httk.httk_typed_init({'uc_structure':UnitcellStructure,'is_edible':bool})
    def __init__ (self,uc_structure,is_edible):
        self.uc_structure = uc_structure
        self.is_edible = is_edible

backend = httk.db.backend.Sqlite('example.sqlite')
store = httk.db.store.SqlStore(backend)
tablesalt = httk.load('../../Tutorial/Step7/NaCl.cif')
tablesalt.add_tag('common name','salt')
arsenic = httk.load('../../Tutorial/Step7/As.cif')
edible = StructureIsEdible(tablesalt,True)
store.save(edible)
edible = StructureIsEdible(arsenic,False)
store.save(edible)

