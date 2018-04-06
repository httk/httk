#!/usr/bin/env python
#
# Simplest possible httk program. Loads a structure and prints out some information on the console.
from __future__ import print_function

import httk

struct = httk.load("example.cif")

print("Formula:", struct.formula)

print("Primitive cell info:")
print("Volume:", float(struct.pc.uc_volume))
print("Assignments", struct.assignments.symbols)
print("Counts:", struct.pc.uc_counts)
print("Coords", struct.pc.uc_reduced_coords.to_floats())

print()

print("Conventional cell info:")
print("Volume:", float(struct.cc.uc_volume))
print("Assignments", struct.assignments.symbols)
print("Counts:", struct.cc.uc_counts)
print("Coords", struct.cc.uc_reduced_coords.to_floats())

httk.save(struct, 'test.vasp')
