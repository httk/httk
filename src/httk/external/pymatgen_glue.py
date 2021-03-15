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
from httk.atomistic import Structure, UnitcellSites
import httk.iface
from httk.external.subimport import submodule_import_external
try:
    pymatgen_path = config.get('paths', 'pymatgen')
except Exception:
    pymatgen_path = None

pymatgen_major_version = None
pymatgen_minor_version = None

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

    try:
        import pymatgen

        try:
            pymatgen_major_version = pymatgen.__version__.split('.')[0]
            pymatgen_minor_version = pymatgen.__version__.split('.')[1]
        # New 2022.X.X version have moved the __version__ attribute:
        except AttributeError:
            import pymatgen.core
            pymatgen_major_version = pymatgen.core.__version__.split('.')[0]
            pymatgen_minor_version = pymatgen.core.__version__.split('.')[1]


    except ImportError:
        pass

mp_key = ""


def set_mp_key(key):
    global mp_key
    mp_key = key


def structure_to_pmg_struct(struct):
    """Converts httk structures to Pymatgen structures."""
    basis = struct.pc.uc_basis.to_floats()
    coords = struct.pc.uc_reduced_coords.to_floats()
    counts = struct.pc.uc_counts

    species = []
    for a, count in zip(struct.assignments, counts):
        for _ in range(count):
            species.append(a.symbols[0])

    try:
        return pymatgen.Structure(basis, species, coords)
    except AttributeError:
        return pymatgen.core.Structure(basis, species, coords)


def pmg_struct_to_structure(pmg_struct, hall_symbol=None):
    """Converts Pymatgen structures to httk structures."""
    cell = pmg_struct.lattice.matrix.tolist()
    coords = pmg_struct.frac_coords.tolist()
    # There is no direct method to get a list of symbols?
    atomic_symbols = []
    for s in pmg_struct.species:
        atomic_symbols.append(s.value)

    if hall_symbol is None:
        struct = Structure.create(uc_basis=cell, uc_occupancies=atomic_symbols,
                                  uc_reduced_occupationscoords=coords,
                                  periodicity=[1,1,1])
    else:
        struct = Structure.create(rc_basis=cell, rc_occupancies=atomic_symbols,
                                  rc_reduced_occupationscoords=coords,
                                  periodicity=[1,1,1],
                                  hall_symbol=hall_symbol)
    return struct
