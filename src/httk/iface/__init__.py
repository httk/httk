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
httk Interface module

  - The interface between httk and other software. Note: the idea is that this module should be useable without
    the other software installed. E.g., generation of input files to gulp shouldn't require gulp installed.
    
"""

from httk.core import citation
citation.add_src_citation("httk", "Rickard Armiento")

import ase_if, cif2cell_if, gulp_if, isotropy_if, jmol_if, spglib_if, vasp_if, platon_if
