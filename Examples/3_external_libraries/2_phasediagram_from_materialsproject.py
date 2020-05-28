#!/usr/bin/env python

import httk, httk.db, httk.atomistic
from httk.core import IoAdapterString
from httk.atomistic import Structure, StructurePhaseDiagram
from httk.analysis.matsci import PhaseDiagram
import httk.analysis.matsci.vis
from httk.external import pymatgen_glue

import pymatgen, pymatgen.phasediagram.plotter, pymatgen.phasediagram.pdmaker, pymatgen.phasediagram.pdanalyzer
from pymatgen.entries.computed_entries import ComputedEntry
from pymatgen.matproj.rest import MPRester

# Fill in your materials project API key here
mp_key = 'xxxxxx'
a = MPRester(mp_key)
entries = a.get_entries_in_chemsys(['Ca', 'Ti', 'F'])

structures = []
energies = []

# You can do it this way via structures, but it is quite slow
#
#for i, entry in enumerate(entries):
#    print("Entry",i+1,"/",len(entries))
#    cifstr = entry.data['cif']
#    energy = entry.energy
#    ioa = IoAdapterString(cifstr)
#    struct = httk.atomistic.Structure.io.load(ioa,ext='.cif')
#    energies += [energy]
#    structures += [struct]
#
#pd = StructurePhaseDiagram.create(structures,energies)
#pd.vis.show(debug=True)

# Or, we just construct the phase diagram directly
#
pd = PhaseDiagram.create()
for i, entry in enumerate(entries):
    energy = entry.energy
    id = entry.data['pretty_formula']+":"+entry.data['material_id']
    symbols = entry.data['unit_cell_formula'].keys()
    counts = entry.data['unit_cell_formula'].values()
    pd.add_phase(symbols, counts, id, energy)
    print("Entry", i+1, "/", len(entries), ":", id)

pd.vis.show(debug=True)

