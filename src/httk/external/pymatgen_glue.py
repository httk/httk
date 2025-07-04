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

import os

from httk.core import citation
from httk.core.basic import is_sequence
citation.add_ext_citation("Pymatgen",
                          "Shyue Ping Ong, William Davidson Richards, Anubhav Jain, Geoffroy Hautier, Michael Kocher, \
Shreyas Cholia, Dan Gunter, Vincent Chevrier, Kristin A. Persson, Gerbrand Ceder. \
Python Materials Genomics (pymatgen) : A Robust, Open-Source Python Library for Materials Analysis. \
Computational Materials Science, 2013, 68, 314-319. \
doi:10.1016/j.commatsci.2012.10.028; and others")
import httk.atomistic.data
from httk.core.httkobject import HttkPlugin, HttkPluginWrapper

from httk import config
from httk.atomistic import Structure, UnitcellSites, Spacegroup
from httk.core.vectors import FracVector

from httk.atomistic import Structure, UnitcellSites
import httk.iface
from httk.external.subimport import submodule_import_external

pymatgen_major_version = None
pymatgen_minor_version = None

try:
    pymatgen_path = config.get('paths', 'pymatgen')
except Exception:
    pymatgen_path = None

    try:
        import pymatgen

        try:
            from importlib.metadata import version
            en_major_version = version('pymatgen')
            pymatgen_minor_version = ""
        except AttributeError:
            pymatgen_major_version = pymatgen.__version__.split('.')[0]
            pymatgen_minor_version = pymatgen.__version__.split('.')[1]

    except ImportError:
        pass

mp_key = ""

def set_mp_key(key):
    global mp_key
    mp_key = key

def ensure_pymatgen_is_imported():
    if pymatgen_path == "False":
        raise Exception("httk.external.pymatgen_glue: module pymatgen_glue imported, but pymatgen is disabled in configuration file.")
    if pymatgen_major_version is None:
        raise ImportError("httk.external.pymatgen_glue imported without access to the pymatgen python library.")

if pymatgen_path != "False":
    if pymatgen_path is not None:
        submodule_import_external(os.path.join(pymatgen_path), 'pymatgen')
    else:
        try:
            external = config.get('general', 'allow_system_libs')
        except Exception:
            external = 'yes'


def structure_to_pmg_struct(struct):
    """Converts httk structures to Pymatgen structures."""

    from httk.external.pymatgen_ext import pymatgen

    basis = struct.uc_basis.to_floats()
    coords = struct.uc_reduced_coords.to_floats()
    counts = struct.uc_counts

    species = []
    for a, count in zip(struct.assignments, counts):
        for _ in range(count):
            species.append(a.symbols[0])

    try:
        return pymatgen.Structure(basis, species, coords)
    except AttributeError:
        return pymatgen.core.Structure(basis, species, coords)

def pmg_struct_to_spglib_tuple(pmg_struct, return_atomic_symbols=False):
    cell = pmg_struct.lattice.matrix.tolist()
    coords = pmg_struct.frac_coords.tolist()
    # There is no direct way to get a list of symbols?
    atomic_symbols = []
    symbols_int = []
    for s in pmg_struct.species:
        atomic_symbols.append(s.value)
        symbols_int.append(s.number)
    if return_atomic_symbols:
        return (cell, coords, symbols_int), atomic_symbols
    else:
        return (cell, coords, symbols_int)

def pmg_struct_to_structure(pmg_struct, hall_symbol=None, comment=None,
                            find_primitive=False):
    """Converts Pymatgen structures to httk structures.
    The correct Hall symbol can be optionally determined.
    The POSCAR comment line can also be given.
    Structure can be optionally reduced to the standard conventional
    structure, which also gives the standard primitive structure (struct.pc).
    """

    (cell, coords, symbols_int), atomic_symbols = pmg_struct_to_spglib_tuple(pmg_struct,
            return_atomic_symbols=True)

    if find_primitive:
        from httk.external.numpy_ext import numpy as np
        from httk.external.pyspglib_ext import spglib

        dataset = spglib.get_symmetry_dataset(
            (cell, coords, symbols_int))
        hall_symbol = dataset['hall']
        spacegroupnumber = dataset['number']
        spacegroup = Spacegroup.create(hall_symbol=hall_symbol,
                                       spacegroupnumber=spacegroupnumber)

        rc_reduced_occupationscoords = []
        rc_occupancies = []
        multiplicities = []
        wyckoff_symbols = []

        rc_basis = dataset['std_lattice'].tolist()
        rc_pos = dataset['std_positions'].tolist()

        for ind in set(dataset['equivalent_atoms']):
            atom = symbols_int[ind]
            equiv_orbs_where = np.argwhere(dataset['equivalent_atoms'] == ind).flatten()
            prim_index = dataset['mapping_to_primitive'][ind]
            std_index = int(np.argwhere(dataset['std_mapping_to_primitive'] == prim_index).flatten()[0])
            rc_reduced_occupationscoords.append(rc_pos[std_index])
            rc_occupancies.append({'atom': atom, 'ratio': FracVector(1, 1)})
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

        struct = Structure.create(
            spacegroup=spacegroup,
            rc_basis=rc_basis,
            rc_reduced_occupationscoords=rc_reduced_occupationscoords,
            rc_occupancies=rc_occupancies,
            wyckoff_symbols=wyckoff_symbols,
            multiplicities=multiplicities,
            )

    elif hall_symbol == 'generate':
        from httk.external.pyspglib_ext import spglib
        dataset = spglib.get_symmetry_dataset(
            (cell, coords, symbols_int))
        hall_symbol = dataset['hall']
        spacegroupnumber = dataset['number']
        spacegroup = Spacegroup.create(hall_symbol=hall_symbol,
                                       spacegroupnumber=spacegroupnumber)

        struct = Structure.create(rc_basis=cell, rc_occupancies=atomic_symbols,
                                  rc_reduced_occupationscoords=coords,
                                  periodicity=[1, 1, 1],
                                  spacegroup=spacegroup)

    elif hall_symbol is None:
        spacegroup = Spacegroup.create(hall_symbol="P 1", spacegroupnumber=1)
        struct = Structure.create(rc_basis=cell, rc_occupancies=atomic_symbols,
                    rc_reduced_occupationscoords=coords, periodicity=[1, 1, 1],
                    spacegroup=spacegroup)

    else:
        struct = Structure.create(rc_basis=cell, rc_occupancies=atomic_symbols,
                                  rc_reduced_occupationscoords=coords,
                                  periodicity=[1, 1, 1],
                                  hall_symbol=hall_symbol)

    if comment is not None:
        struct.add_tag('comment', comment)

    return struct
