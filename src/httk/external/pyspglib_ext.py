# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2015 Rickard Armiento
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
  pyspglib external module
"""

import os, sys

from httk.core import citation
citation.add_ext_citation('spglib / pyspglib', "(Author list to be added)")

from httk import config
from command import Command
from subimport import submodule_import_external
import httk

try:
    pyspglib_path = config.get('paths', 'pyspglib')
except Exception:
    pyspglib_path = None

try:
    spglib_path = config.get('paths', 'spglib')
except Exception:
    spglib_path = None

pyspg_major_verion = None
pyspg_minor_verion = None
    
def ensure_pyspg_is_imported():
    if pyspglib_path == "False" and spglib_path == "False":
        raise Exception("httk.external.ase_glue: module ase_glue imported, but ase is disabled in configuration file.")
    if pyspg_major_version is None:
        raise Exception("httk.external.pyspglib_ext imported, but could not access pyspg.")

try:    
    if pyspglib_path is not None and spglib_path is not None:
        # Import spglib from pyspglib, with some magic to enable use of pyspglib.Atoms for the pyspglib ASE atoms emulation class
        pyspglib = submodule_import_external(os.path.join(pyspglib_path, 'lib', 'python'), 'pyspglib')
        from pyspglib import spglib
        atoms = submodule_import_external(os.path.join(spglib_path, 'python', 'ase', 'test'), 'atoms')
        spglib.Atoms = atoms.Atoms
        del atoms  # Lets not pollute the namespace
        pyspg_major_version = spglib.__version__.split('.')[0]
        pyspg_minor_version = spglib.__version__.split('.')[1]     
    else:
        try:
            external = config.get('general', 'allow_system_libs')
        except Exception:
            external = 'yes'
        if external == 'yes':
            # Note: this type of import will miss the spglib 'fake' atom object which is a problem. Probably should
            # not use this type of import
            from pyspglib import spglib
            sys.stderr.write('WARNING: spglib imported in httk.external without any path given in httk.cfg, this means no spglib.Atoms object exists.\n')
            pyspg_major_version = spglib.__version__.split('.')[0]
            pyspg_minor_version = spglib.__version__.split('.')[1]     
        else:
            pass
except Exception:
    pass
    
def structure_to_spglib_atoms(struct):
    ensure_pyspg_is_imported()

    symbols = []
    for i in range(len(struct.coordgroups)):
        name = httk.htdata.periodictable.atomic_symbol(struct.assignments[i])
        symbols += [name]*struct.counts[i]

    print "SYMBOLS", symbols, struct.N

    cell = struct.cell.to_floats()

    scaled_positions = struct.coords
    
    atoms = spglib.Atoms(symbols=symbols,
                         cell=cell,
                         scaled_positions=scaled_positions,
                         pbc=True)

    return atoms


def analysis(struct, symprec=1e-5):
    ensure_pyspg_is_imported()

    atoms = structure_to_spglib_atoms(struct)
    val = spglib.get_spacegroup(atoms)
    print "Spacegroup is:", val 
    val = spglib.refine_cell(atoms, symprec=symprec)
    print "Primitive", val


def primitive(struct, symprec=1e-5):
    ensure_pyspg_is_imported()
    
    atoms = structure_to_spglib_atoms(struct)
    prim = spglib.refine_cell(atoms, symprec=symprec)
    sg = spglib.get_spacegroup(atoms)
    struct = httk.iface.spglib_if.spglib_out_to_struct(prim)
    struct.comment = "Spacegroup: "+sg
    return struct

    
    
