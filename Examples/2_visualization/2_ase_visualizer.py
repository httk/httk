#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)

# This is a simple program that shows some interaction with ase using the ase_glue package

import httk
from httk.atomistic import *
import httk.external.ase_glue
import ase
import ase.visualize

# By loading the httk.external.ase_glue package *before* 'import ase' you will load the ASE version specified in your httk configuration files.
# The below two version are going to be the same.
print("ASE version loaded by httk:", httk.external.ase_ext.ase_major_version, ".", httk.external.ase_ext.ase_minor_version)
print("ASE version loaded in this script", ase.__version__)

# First we create a structure object where we know the full set of coordinates.

cell = [[5.0, 0.0, 0.0],
        [0.0, 5.0, 0.0],
        [0.0, 0.0, 5.0]]

coordgroups = [[
               [0.5, 0.5, 0.5]
               ], [
               [0.0, 0.0, 0.0]
               ], [
               [0.5, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.5]
               ]]

assignments = ['Pb', 'Ti', 'O']

# To create a structure, the primary thing to keep track of is what coordinate representation is used (and what its name is in
# the Structure.create constructor
struct = Structure.create(uc_cell=cell, uc_reduced_coordgroups=coordgroups, assignments=assignments, uc_volume=62.79)

print("Structure data: formula:", struct.formula+" ("+struct.anonymous_formula+")", ", volume:", float(struct.uc_volume), ", basis:", struct.uc_basis.to_floats())

ase_atoms = struct.ase.to_Atoms()
ase.visualize.view(ase_atoms)
