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
citation.add_ext_citation('Numpy', "(Author list to be added)")

from httk import config
from command import Command
from subimport import submodule_import_external
import httk
try:   
    path = config.get('paths', 'numpy')
except Exception:
    path = None

if path is not None:    
    numpy = submodule_import_external(os.path.join(path), 'numpy')
else:
    try:
        external = config.get('general', 'allow_system_libs')
    except Exception:
        external = 'yes'
    if external == 'yes':
        import numpy
    else:
        raise Exception("httk.external.numpy_ext imported, but could not access numpy.")
    
