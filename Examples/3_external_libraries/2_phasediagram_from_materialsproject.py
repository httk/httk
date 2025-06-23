#!/usr/bin/env python

from __future__ import print_function
import os

import httk, httk.db, httk.atomistic
from httk.core import IoAdapterString
from httk.atomistic import Structure, StructurePhaseDiagram
from httk.analysis.matsci import PhaseDiagram
import httk.analysis.matsci.vis
from httk.external import pymatgen_glue

import pymatgen
# import pymatgen.phasediagram.plotter, pymatgen.phasediagram.pdmaker, pymatgen.phasediagram.pdanalyzer
from pymatgen.entries.computed_entries import ComputedEntry
from pymatgen import MPRester

# Set the environment variable MATPROJ_API_KEY with your materials project API key
# (Or edit the line below to be set to the string)
mp_key = os.environ["MATPROJ_API_KEY"]
a = MPRester(mp_key)
entries = a.get_entries_in_chemsys(['Ca', 'Ti', 'F'],
        property_data=['material_id','pretty_formula','unit_cell_formula'])

# for i, entry in enumerate(entries):
    # print(entry.data.keys())

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
