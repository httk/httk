#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)

# This is a simple program that shows the httks visualization package

# First we create a structure object where we know the full set of coordinates. 

import httk
from httk.atomistic import Structure
import httk.atomistic.vis


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

print "Structure data: formula:", struct.formula+" ("+struct.anonymous_formula+")", ", volume:", float(struct.uc_volume), ", basis:", struct.uc_basis.to_floats()

struct.vis.show()
struct.vis.wait()

cell = [[1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]]

coordgroups = [[
               [0.5, 0.5, 0.5]
               ], [
               [0.0, 0.0, 0.0]
               ], [
               [0.5, 0.0, 0.0]
               ]]

assignments = ['Pb', 'Zr', 'O']

spacegroup = 'P m -3 m'

struct = Structure.create(rc_cell=cell, rc_reduced_coordgroups=coordgroups, assignments=assignments, rc_volume=62.79, spacegroup=spacegroup)

# The visualizer handles both structures given via the representative cell (seen here) and the unit cell (above)
struct.vis.show()
struct.vis.wait()

