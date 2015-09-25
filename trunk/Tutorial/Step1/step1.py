#!/usr/bin/env python
#
# Simplest possible httk program. Loads a structure and prints out some information on the console.

import httk

struct = httk.load("example.cif")

print("Formula:", struct.formula)
print("Volume:", float(struct.uc_volume))
print("Assignments", struct.uc_formula_symbols)
print("Counts:", struct.uc_counts)
print("Coords", struct.uc_reduced_coords)
