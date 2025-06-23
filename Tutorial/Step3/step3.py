#!/usr/bin/env python

try:
    import httk
except Exception:
    import sys, os.path, inspect
    _realpath = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
    sys.path.insert(1, os.path.join(_realpath, '../..'))
    import httk

import httk.atomistic.vis
from httk.atomistic import *
import httk.external.ase_glue
import ase
import ase.lattice.surface

basis = [[1.0, 0.0, 0.0],
         [0.0, 1.0, 0.0],
         [0.0, 0.0, 1.0]]

coordgroups = [[
               [0.5, 0.5, 0.5]
               ], [
               [0.0, 0.0, 0.0]
               ], [
               [0.5, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.5]
               ]]

assignments = ['Pb', 'Ti', 'O']
struct1 = Structure.create(uc_basis=basis, uc_reduced_coordgroups=coordgroups, assignments=assignments, uc_volume=62.79).find_symmetry()

print("Formula:", struct1.formula)
print("Volume", float(struct1.uc_volume))
print("Assignments", struct1.assignments.symbols)
print("Counts:", struct1.uc_counts)
print("Coords", struct1.uc_reduced_coords)
hall_symbol = struct1.spacegroup.hall_symbol
print("Spacegroup info:", hall_symbol, "(#"+str(struct1.spacegroup.number)+")")

slab = ase.lattice.surface.fcc111('Al', size=(2, 2, 10), vacuum=10.0)
struct2 = Structure.ase.from_Atoms(slab)
back_to_ase_atoms = struct2.ase.to_Atoms()

struct2.vis.show()
struct2.vis.wait()




