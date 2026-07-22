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

from httk.atomistic import Structure
from httk.core.vectors import FracVector
from httk.atomistic.data.periodictable import atomic_symbol


def spglib_out_to_struct(out, hall_symbol=None):
    """Convert spglib output to httk Structure"""
    cell = FracVector.from_floats(out[0].tolist())
    coords = FracVector.from_floats(out[1].tolist())
    symbols_int = out[2]
    atomic_symbols = []
    for i in range(len(coords)):
        atomic_symbols.append(atomic_symbol(int(symbols_int[i])))

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
