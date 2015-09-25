#!/usr/bin/env python

import httk.db, httk.atomistic.vis
from httk.atomistic import UnitcellStructure, StructurePhaseDiagram 
 
class TotalEnergyResult(httk.Result):
    @httk.httk_typed_init({'computation':httk.Computation, 'structure':UnitcellStructure, 'total_energy':float})
    def __init__(self, computation, structure, total_energy):
        self.computation = computation
        self.structure = structure
        self.total_energy = total_energy

backend = httk.db.backend.Sqlite('example.sqlite')
store = httk.db.store.SqlStore(backend)

search = store.searcher()
search_total_energy = search.variable(TotalEnergyResult)
search_struct = search.variable(UnitcellStructure)
search.add(search_total_energy.structure == search_struct)
search.add_all(search_struct.formula_symbols.is_in('O','Ca','Ti'))

#search.output(search_struct,'structure')
search.output(search_total_energy,'total_energy_result')

structures = []
energies = []

for match, header in search:
    total_energy_result = match[0]
    structures += [total_energy_result.structure]
    energies += [total_energy_result.total_energy]

pd = StructurePhaseDiagram.create(structures,energies)
pd.vis.show(debug=True)

