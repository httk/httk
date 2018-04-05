#!/usr/bin/env python
# input arguments: structure = structure to run

from httk.iface.vasp_if import structure_to_poscar

comment = [str(structure.get_tags()[x]) for x in structure.get_tags()]
structure_to_poscar('POSCAR', structure,
                    fix_negative_determinant=True, comment=comment)
