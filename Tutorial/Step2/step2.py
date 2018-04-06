#!/usr/bin/env python
from __future__ import print_function, division

try:
    import httk
except Exception:
    import sys, os.path, inspect
    _realpath = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
    sys.path.insert(1, os.path.join(_realpath, '../..'))
    import httk

import httk.atomistic.vis 
from httk.atomistic import Structure

### Example 1

struct = Structure.io.load("POSCAR")
print(struct)
struct.vis.show({'bonds': True, 'extbonds': False, 'polyhedra': False})
struct.vis.wait()

symstruct = struct.find_symmetry()

symstruct.vis.show({'bonds': True, 'extbonds': False, 'polyhedra': False})
# This below allows you to see the primitive cell
#struct.vis.show({'bonds':True, 'extbonds':False, 'polyhedra':False, 'unitcell':struct.uc_cell.basis, 'show_supercell':True})
symstruct.vis.wait()

### Example 2

struct = Structure.io.load("POSCAR2")

struct.vis.show(debug=True)
struct.vis.wait()

struct = struct.pc.supercell.orthogonal(tolerance=15)
struct.vis.show()
struct.vis.wait()

struct = struct.pc.supercell.cubic(tolerance=15)
struct.vis.show({'extbonds': False})
struct.vis.wait()





