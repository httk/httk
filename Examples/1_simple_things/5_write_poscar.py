#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)
# This program saves a structure object

import httk
from httk.core import *
from httk.atomistic import Structure

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

struct = Structure.create(uc_basis=basis, uc_reduced_coordgroups=coordgroups, assignments=assignments, uc_volume=62.79)

# One alternative
struct.io.save("PbTiO3.vasp")
print ("PbTiO3.vasp saved (POSCAR format)")

# Another alternative
httk.save(struct, "PbTiO3_alt.vasp")
print ("PbTiO3_alt.vasp saved (POSCAR format)")


basis = [[1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]]

coordgroups = [[
               [0.5, 0.5, 0.5]
               ], [
               [0.0, 0.0, 0.0]
               ], [
               [0.5, 0.0, 0.0]
               ]]

assignments = ['Pb', 'Ti', 'O']

spacegroup = 'P m -3 m'

struct = Structure.create(rc_basis=basis, rc_reduced_coordgroups=coordgroups, assignments=assignments, rc_volume=62.79, spacegroup=spacegroup)

struct.io.save("PbTiO3_alt2.vasp")
print ("PbTiO3_alt2.vasp saved (POSCAR format)")


