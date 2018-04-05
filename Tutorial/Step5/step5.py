#!/usr/bin/env python

from httk.atomistic import Structure
import httk.iface.vasp_if

# Must be updated to your path to poscars, OR, set to None if you have 
# VASP_IF_POSCARPATH configured in httk.cfg
poscarspath = None

struct = Structure.io.load("example.cif")
httk.iface.vasp_if.prepare_single_run("Run", struct, template='template', poscarspath=poscarspath, overwrite=True)            

# Note: one can also use, e.g., t:/vasp/single/static as template. The 't:' prefix indicates subdirectories to Execution/tasks-templates in 
# the httk main directory.
