#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)
# This program just loads a structure object

from httk.core import *
import httk.io
import httk.atomistic.io

files = ["../../Tutorial/tutorial_data/all_spacegroups/cifs/53.cif"]

for i in range(len(files)):
    filename = files[i]
    # Simple way
    struct = httk.load(filename)
    # More sophisticated way that allows choosing a backend
    struct = httk.atomistic.io.cif_to_struct(filename, backends=['cif2cell'])
    print "The formula is:", struct.formula+" ("+struct.anonymous_formula+")"
    print "Tags:", [str(struct.get_tag(x)) for x in struct.get_tags()]
    print "Refs:", [str(x) for x in struct.get_refs()]
    #struct.vis.show()

