#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2022 Rickard Armiento
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
citation.add_ext_citation("Pymatgen",
                          "Shyue Ping Ong, William Davidson Richards, Anubhav Jain, Geoffroy Hautier, Michael Kocher, \
Shreyas Cholia, Dan Gunter, Vincent Chevrier, Kristin A. Persson, Gerbrand Ceder. \
Python Materials Genomics (pymatgen) : A Robust, Open-Source Python Library for Materials Analysis. \
Computational Materials Science, 2013, 68, 314-319. \
doi:10.1016/j.commatsci.2012.10.028; and others")

major_version = None
minor_version = None

from httk import config
from httk.external.command import Command
from httk.external.subimport import submodule_import_external

try:
    path = config.get('paths', 'pymatgen')
except Exception:
    path = None

if path == "False":
    raise Exception("httk.external.pymatgen_ext imported, but pymatgen is disabled in configuration file.")

if path is not None and path != "":
    pymatgen = submodule_import_external(os.path.join(path), 'pymatgen')
else:
    try:
        external = config.get('general', 'allow_system_libs')
    except Exception:
        external = 'yes'
    if external == 'yes':
        import pymatgen
    else:
        raise Exception("httk.external.pymatgen_ext imported, but pymatgen module not found.")

try:
    major_version = pymatgen.__version__.split('.')[0]
    minor_version = pymatgen.__version__.split('.')[1]
except AttributeError:
    # New 2022.X.X version have moved the __version__ attribute:
    import pymatgen.core
    major_version = pymatgen.core.__version__.split('.')[0]
    minor_version = pymatgen.core.__version__.split('.')[1]
