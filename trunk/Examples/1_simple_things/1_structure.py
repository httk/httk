#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)

# This is a simple program that just shows some basic functionality using the httk Structure object

from httk import *
from httk.atomistic import *

# First we create a structure object where we know the full set of coordinates. 

cell = [[1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]]

coordgroups = [[
               [0.5, 0.5, 0.5]
            ],[
               [0.0, 0.0, 0.0]
            ],[
               [0.5, 0.0, 0.0],[0.0, 0.5, 0.0],[0.0, 0.0, 0.5]
            ]]

assignments = ['Pb','Ti','O']

# To create a structure, the primary thing to keep track of is what coordinate representation is used (and what its name is in 
# the Structure.create constructor
struct = Structure.create(uc_cell=cell,uc_reduced_coordgroups=coordgroups,assignments=assignments,uc_volume=62.79)
uc_struct = UnitcellStructure.create(uc_cell=cell,uc_reduced_coordgroups=coordgroups,assignments=assignments,uc_volume=62.79)

print "The formula is:",struct.formula+" ("+struct.anonymous_formula+")"
print "Again, the formula is:",uc_struct.formula+" ("+uc_struct.anonymous_formula+")"

# Now we create the same structure based only the represenative coordinates + the hall symbol of the group, which is 'P m -3 m'

cell = [[1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]]

coordgroups = [[
               [0.5, 0.5, 0.5]
            ],[
               [0.0, 0.0, 0.0]
            ],[
               [0.5, 0.0, 0.0]
            ]]

assignments = ['Pb','Ti','O']

spacegroup = 'P m -3 m'

struct = Structure.create(rc_cell=cell,rc_reduced_coordgroups=coordgroups,assignments=assignments,rc_volume=62.79,spacegroup=spacegroup)

print "The formula is:",struct.formula+" ("+struct.anonymous_formula+")"


