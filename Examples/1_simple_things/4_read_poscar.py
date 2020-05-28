#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)
# This program just loads a structure object

from httk.core import *
import httk.httkio
import httk.iface.vasp_if
import httk.atomistic.atomisticio

files = ["../../Tutorial/Step2/POSCAR2"]

for i in range(len(files)):
    filename = files[i]
    # Simple way
    struct = httk.load(filename)
    # More 'sophisticated' way (though, here there are no settings, so it does not matter)
    struct = httk.iface.vasp_if.poscar_to_structure(filename)
    print("The formula is:", struct.formula+" ("+struct.anonymous_formula+")")
    print("Tags:", [str(struct.get_tag(x)) for x in struct.get_tags()])
    print("Refs:", [str(x) for x in struct.get_refs()])
    #struct.vis.show()

