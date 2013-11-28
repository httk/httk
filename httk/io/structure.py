# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2013 Rickard Armiento
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

import hashlib
import httk

def cif_to_struct(ioa,backends=['ase','platon','cif2cell']):
    for backend in backends:
        if backend == 'ase':
            try:
                from httk.external import ase_ext
                return ase_ext.ase_read(ioa)
            except ImportError:
                pass
        if backend == 'platon':
            try:
                from httk.external import platon_ext
                sgstruct = platon_ext.cif_to_sgstructure(ioa)
                return sgstruct.to_structure()
                #return platon_if.cif_to_structure(ioa)
            except ImportError:
                pass
        if backend == 'cif2cell':
            try:
                from httk.external import cif2cell_ext
                return cif2cell_ext.cif_to_structure(ioa)
            except ImportError:
                pass
    raise Exception("structure_to_sgstructure: None of the requested / available backends available, tried:"+str(backends))

