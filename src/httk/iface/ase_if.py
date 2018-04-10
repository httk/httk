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

#from httk.core.htdata import periodictable
from httk.atomistic.data import periodictable
from httk.core import *


def rc_structure_to_symbols_and_scaled_positions(struct):

    symbols = []
    for i in range(len(struct.rc_reduced_coordgroups)):
        name = struct.assignments.symbols[i]
        symbols += [name]*struct.rc_counts[i]

    scaled_positions = struct.rc_reduced_coords

    return symbols, scaled_positions


def uc_structure_to_symbols_and_scaled_positions(struct):

    symbols = []
    for i in range(len(struct.uc_reduced_coordgroups)):
        name = struct.assignments.symbols[i]
        symbols += [name]*struct.uc_counts[i]

    scaled_positions = struct.uc_reduced_coords

    return symbols, scaled_positions
        


