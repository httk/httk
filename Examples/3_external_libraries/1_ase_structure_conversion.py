#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)

# This is a simple program that shows some interaction with ase using the ase_glue package

import httk
from httk.atomistic import *
import httk.external.ase_glue
import ase
import ase.lattice
import ase.lattice.surface
import ase.lattice.cubic

# By loading the httk.external.ase_glue package *before* 'import ase' you will load the ASE version specified in your httk configuration files.
# The below two version are going to be the same.
print("ASE version loaded by httk:", httk.external.ase_glue.ase_major_version, ".", httk.external.ase_glue.ase_minor_version)
print("ASE version loaded in this script", ase.version.version)

# First we create a structure object where we know the full set of coordinates.

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

print()
print("==== Simple conversion")

print("== httk to ASE:")

print("httk structure: formula:", struct.formula+" ("+struct.anonymous_formula+")", ", volume:", float(struct.uc_volume), ", basis:",
        struct.uc_basis.to_floats())

ase_atoms = struct.ase.to_Atoms()

print("ASE structure:", ase_atoms)

print("== From ASE to httk")

struct2 = struct.ase.from_Atoms(ase_atoms)

print("httk structure: formula:", struct2.formula+" ("+struct2.anonymous_formula+")", ", volume:", float(struct2.uc_volume), ", basis:",
        struct2.uc_basis.to_floats())

print()
print("==== Creating a slab system in ASE and converting it to httk")

print("== Au surface using ase.Atoms")
d = 2.9
L = 10.0
ase_atoms3 = ase.Atoms('Au',
                       positions=[(0, L / 2, L / 2)],
                       cell=(d, L, L),
                       pbc=(1, 0, 0))

struct3 = struct.ase.from_Atoms(ase_atoms3)

print("== FCC111 surface using ase.lattice.surface.fcc111")

slab = ase.lattice.surface.fcc111('Al', size=(2, 2, 3), vacuum=10.0)
struct5 = struct.ase.from_Atoms(slab)

print("httk structure: formula:", struct5.formula+" ("+struct5.anonymous_formula+")", ", volume:", float(struct5.uc_volume), ", basis:",
        struct5.uc_basis.to_floats(), "pbc=", struct5.uc_sites.pbc)

print()
print("==== Creating systems using ASE, converting it to httk, and find its spacegroup")

print("== FCC Cu")
ase_atoms4 = ase.lattice.bulk('Cu', 'fcc', a=3.6)

struct4 = struct.ase.from_Atoms(ase_atoms4)

print("== AuCu3")


class AuCu3Factory(ase.lattice.cubic.SimpleCubicFactory):

    "A factory for creating AuCu3 (L1_2) lattices."
    bravais_basis = [[0, 0, 0], [0, 0.5, 0.5], [0.5, 0, 0.5], [0.5, 0.5, 0]]
    element_basis = (0, 1, 1, 1)

AuCu3factory = AuCu3Factory()
AuCu3struct = AuCu3factory(symbol=('Au', 'Cu'), latticeconstant=3.6)
struct5 = struct.ase.from_Atoms(AuCu3struct)

# This needs to run a symmetry finder
print("Spacegroup:", struct5.spacegroup.number)
