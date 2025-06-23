#!/usr/bin/env python

from httk.atomistic import Structure
import httk.iface.vasp_if

# Must be updated to your path to VASP poscar files (e.g., '/path/to/.../POT_GGA_PAW_PBE'), OR, set to None if you have
# 'vasp_pseudolib' configured in httk.cfg or the VASP_PSEUDOLIB environment variable set.
poscarspath = None

struct = Structure.io.load("example.cif")
httk.iface.vasp_if.prepare_single_run("Run", struct, template='t:vasp/single/static', poscarspath=poscarspath, overwrite=True)
