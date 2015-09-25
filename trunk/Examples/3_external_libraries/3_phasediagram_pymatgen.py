#!/usr/bin/env python
import httk, httk.db
from httk.atomistic import Structure
from httk.external import pymatgen_glue

import pymatgen, pymatgen.phasediagram.plotter, pymatgen.phasediagram.pdmaker, pymatgen.phasediagram.pdanalyzer
from pymatgen.entries.computed_entries import ComputedEntry
from pymatgen.matproj.rest import MPRester

class TotalEnergyResult(httk.Result):
    @httk.httk_typed_init({'computation':httk.Computation, 'structure':Structure, 'total_energy':float})
    def __init__(self, computation, structure, total_energy):
        self.computation = computation
        self.structure = structure
        self.total_energy = total_energy
        
# This reads the tutorial example database from step6
backend = httk.db.backend.Sqlite('../../Tutorial/Step6/example.sqlite')
store = httk.db.store.SqlStore(backend)

search = store.searcher()
search_total_energy = search.variable(TotalEnergyResult)
search_struct = search.variable(Structure)
search.add(search_total_energy.structure == search_struct)
search.add_all(search_struct.formula_symbols.is_in('O','Ca','Ti'))
search.output(search_total_energy, 'total_energy_result')

entries = []

#a = MPRester(mp_key)
#entries = a.get_entries_in_chemsys(['Ca', 'Ti', 'O'])

for match, header in search:
    total_energy_result = match[0]
    print("Total energy for: "+str(total_energy_result.structure.formula)+" ("+total_energy_result.structure.uc_formula+") "+" is "+str(total_energy_result.total_energy))
    entries += [ComputedEntry(str(total_energy_result.structure.uc_formula), float(total_energy_result.total_energy))]

# import random
# for i in range(100):
#     ca=random.choice(range(10))
#     ti=random.choice(range(10))
#     o=random.choice(range(10))
#     s=ca+ti+o
#     form = 'Ca'+str(ca)+'Ti'+str(ti)+'O'+str(o)
#     entries += [ComputedEntry(form, random.randrange(-10,0)*s)]
    
pd = pymatgen.phasediagram.pdmaker.PhaseDiagram(entries)
plotter = pymatgen.phasediagram.plotter.PDPlotter(pd,show_unstable=False)
plotter.show() 
