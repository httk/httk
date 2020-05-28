#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)
# This program saves a structure object

import httk
from httk.core import *
from httk.atomistic import Structure

cell = [[1.0, 0.0, 0.0],
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

struct = Structure.create(uc_cell=cell, uc_reduced_coordgroups=coordgroups, assignments=assignments, uc_volume=62.79)

struct.io.save("PbTiO3.cif")
print("PbTiO3.cif saved")

symmetric_struct = struct.find_symmetry()

symmetric_struct.io.save("PbTiO3_alt.cif")
print("PbTiO3_alt.cif saved")

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

struct.io.save("PbTiO3_alt2.cif")
print ("PbTiO3_alt2.cif saved")

