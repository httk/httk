#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)

# This is a simple program that just shows some basic functionality using the httk Structure object

from httk import *
from httk.atomistic import *
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

print "==== Building simple supercell 1x2x3"

struct = Structure.create(uc_cell=cell, uc_reduced_coordgroups=coordgroups, assignments=assignments, uc_volume=62.79)
print "The formula is:", struct.formula+" ("+struct.anonymous_formula+")", " vol=", float(struct.uc_volume)

supercell = struct.build_supercell([[1, 0, 0], [0, 2, 0], [0, 0, 3]])
print supercell.uc_reduced_coordgroups.to_floats()

print "The formula is:", supercell.formula+" ("+supercell.anonymous_formula+")", " vol=", float(supercell.uc_volume)

# Read a more complicated structure
struct = httk.load("../../Tutorial/Step2/POSCAR2")
try:
    struct.vis.show()
    struct.vis.wait()
except Exception:
    print "(Skipping structure visualization due to missing external program (usually jmol).)"

supercell = struct.build_supercell([[2, 0, 0], [0, 2, 0], [0, 0, 1]])
try:
    supercell.vis.show()
    supercell.vis.wait()
except Exception:
    print "(Skipping structure visualization due to missing external program (usually jmol).)"

print
print "==== Building orthogonal supercells"

print "== Exact supercell (works):"
try:
    supercell = struct.build_orthogonal_supercell(tolerance=None)
    print supercell.uc_nbr_atoms, [supercell.uc_alpha, supercell.uc_beta, supercell.uc_gamma], [float(supercell.uc_a), float(supercell.uc_b), float(supercell.uc_c)]
except Exception as e:
    print e

supercell = struct.build_orthogonal_supercell(tolerance=20)
print supercell.uc_nbr_atoms, [supercell.uc_alpha, supercell.uc_beta, supercell.uc_gamma], [float(supercell.uc_a), float(supercell.uc_b), float(supercell.uc_c)]

try:
    supercell.vis.show()
    supercell.vis.wait()
except Exception:
    print "(Skipping structure visualization due to missing external program (usually jmol).)"

print "==== Building cubic supercells"

print "== Original cell:"
print struct.uc_nbr_atoms, [struct.uc_alpha, struct.uc_beta, struct.uc_gamma], [float(struct.uc_a), float(struct.uc_b), float(struct.uc_c)]

print "== Exact supercell (fails):"
try:
    supercell = struct.build_cubic_supercell(tolerance=None)
    print struct.uc_nbr_atoms, [struct.uc_alpha, struct.uc_beta, struct.uc_gamma], [float(struct.uc_a), float(struct.uc_b), float(struct.uc_c)]
except Exception as e:
    print e

print "== Approx supercells:"    
supercell = struct.build_cubic_supercell(tolerance=7)
print struct.uc_nbr_atoms, [struct.uc_alpha, struct.uc_beta, struct.uc_gamma], [float(struct.uc_a), float(struct.uc_b), float(struct.uc_c)]
supercell = struct.build_cubic_supercell(tolerance=10)
print struct.uc_nbr_atoms, [struct.uc_alpha, struct.uc_beta, struct.uc_gamma], [float(struct.uc_a), float(struct.uc_b), float(struct.uc_c)]
supercell = struct.build_cubic_supercell(tolerance=15)

try:
    supercell.vis.show()
    supercell.vis.wait()
except Exception:
    print "(Skipping structure visualization due to missing external program (usually jmol).)"

print struct.uc_nbr_atoms, [struct.uc_alpha, struct.uc_beta, struct.uc_gamma], [float(struct.uc_a), float(struct.uc_b), float(struct.uc_c)]
supercell = struct.build_cubic_supercell(tolerance=25)
print struct.uc_nbr_atoms, [struct.uc_alpha, struct.uc_beta, struct.uc_gamma], [float(struct.uc_a), float(struct.uc_b), float(struct.uc_c)]
#supercell = struct.build_cubic_supercell(tolerance=70,max_search_cells=10000)
#print supercell.full_nbr_atoms,[supercell.alpha, supercell.beta, supercell.gamma], [float(supercell.a), float(supercell.b), float(supercell.c)]
#supercell.vis.show()



