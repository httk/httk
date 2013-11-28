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

from httk.core.htdata import periodictable
from httk.core import *

def structure_to_symbols_and_scaled_positions(struct):

    symbols = []
    for i in range(len(struct.sgcoordgroups)):
        name = htdata.periodictable.atomic_symbol(struct.sgassignments[i])
        symbols += [name]*struct.sgcounts[i]

    scaled_positions = struct.sgcoords

    return symbols, scaled_positions
        
def ase_atoms_to_structure(atoms,hall_symbol=None):
    occupancies = [periodictable.atomic_number(x) for x in atoms.get_chemical_symbols()]
    coords = atoms.get_scaled_positions()
    cell = atoms.get_cell()
    struct = Structure.create(cell=cell, coords=coords, occupancies=occupancies, hall_symbol=hall_symbol)
    return struct


