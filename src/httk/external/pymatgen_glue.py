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
from subimport import submodule_import_external
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

        pymatgen_major_version = pymatgen.__version__.split('.')[0]
        pymatgen_minor_version = pymatgen.__version__.split('.')[1]
        
    except ImportError:
        pass

mp_key = ""


def set_mp_key(key):
    global mp_key
    mp_key = key

