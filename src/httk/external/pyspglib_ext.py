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
from httk.external.command import Command
from httk.external.subimport import submodule_import_external
from httk.core.vectors import FracVector
from httk.atomistic import Structure, Spacegroup
from httk.atomistic.data.periodictable import atomic_symbol
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
            # not use this type of import.
            # NOTE: The 'fake' spglib Atoms object has become obsolete, so I have disabled
            # the warning below, because the warning causes tests to fail.
            import spglib
            # sys.stderr.write('WARNING: spglib imported in httk.external without any path given in httk.cfg, this means no spglib.Atoms object exists.\n')
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

    print("SYMBOLS", symbols, struct.N)

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
    print("Spacegroup is:", val)
    val = spglib.refine_cell(atoms, symprec=symprec)
    print("Primitive", val)


def primitive(struct, symprec=1e-5):
    ensure_pyspg_is_imported()

    atoms = structure_to_spglib_atoms(struct)
    prim = spglib.refine_cell(atoms, symprec=symprec)
    sg = spglib.get_spacegroup(atoms)
    struct = httk.iface.spglib_if.spglib_out_to_struct(prim)
    struct.comment = "Spacegroup: "+sg
    return struct


def struct_process_with_spglig(struct, symprec=1e-5):
    from httk.external.numpy_ext import numpy as np

    ensure_pyspg_is_imported()

    basis = struct.uc_basis.to_floats()
    coords = struct.uc_reduced_coords.to_floats()
    counts = struct.uc_counts

    symbols_int = []
    index = 0
    for a, count in zip(struct.assignments, counts):
        symbols_int += [a.atomic_number]*count
        index += 1

    cell = (basis, coords, symbols_int)
    dataset = spglib.get_symmetry_dataset(cell, symprec=symprec)
    # print(dataset)

    hall_symbol = dataset['hall']
    spacegroupnumber = dataset['number']
    spacegroup = Spacegroup.create(hall_symbol=hall_symbol,
                                   spacegroupnumber=spacegroupnumber)

    rc_basis = dataset['std_lattice'].tolist()
    rc_pos = dataset['std_positions'].tolist()

    rc_reduced_occupationscoords = []
    rc_occupancies = []
    multiplicities = []
    wyckoff_symbols = []
    for ind in set(dataset['equivalent_atoms']):
        atom = symbols_int[ind]
        equiv_orbs_where = np.argwhere(dataset['equivalent_atoms'] == ind).flatten()
        prim_index = dataset['mapping_to_primitive'][ind]
        std_index = int(np.argwhere(dataset['std_mapping_to_primitive'] == prim_index).flatten()[0])
        rc_reduced_occupationscoords.append(rc_pos[std_index])
        rc_occupancies.append({'atom': atom, 'ratio': FracVector(1,1)})
        multiplicities.append(len(equiv_orbs_where))
        wyckoff_symbols.append(dataset['wyckoffs'][ind])
    # Multiplicities have to be "normalized" if the input cell was a supercell
    # containing multiple primitive/standard conventional cells, or if
    # the input cell was the primitive unit cell, i.e. smaller than the
    # conventional cell.
    if sum(multiplicities) > len(dataset['std_mapping_to_primitive']):
        assert sum(multiplicities) % len(dataset['std_mapping_to_primitive']) == 0
        multiplier = sum(multiplicities) // len(dataset['std_mapping_to_primitive'])
        for i in range(len(multiplicities)):
            multiplicities[i] //= multiplier
    elif sum(multiplicities) < len(dataset['std_mapping_to_primitive']):
        assert len(dataset['std_mapping_to_primitive']) % sum(multiplicities) == 0
        multiplier = len(dataset['std_mapping_to_primitive']) // sum(multiplicities)
        for i in range(len(multiplicities)):
            multiplicities[i] *= multiplier
    assert sum(multiplicities) == len(dataset['std_mapping_to_primitive'])

    newstruct = Structure.create(
        spacegroup=spacegroup,
        rc_basis=rc_basis,
        rc_reduced_occupationscoords=rc_reduced_occupationscoords,
        rc_occupancies=rc_occupancies,
        wyckoff_symbols=wyckoff_symbols,
        multiplicities=multiplicities,
        )

    newstruct.add_tags(struct.get_tags())
    newstruct.add_refs(struct.get_refs())

    return newstruct

def uc_reduced_coordgroups_process_with_spglib_TODO(coordgroup, cell, get_wyckoff=False):
    """
    siteutils.py calls this function as
        uc_reduced_coordgroups_process_with_isotropy(coordgroups, cell, spacegroup, get_wyckoff=True),
    while structureutils.py calls it as
        uc_reduced_coordgroups_process_with_isotropy(coordgroups, basis).
    Mismatch between number of required arguments, not sure what to do.
    """
    pass
