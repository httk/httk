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

import httk
from httk.atomistic import Structure, Cell, Compound


class Result_RelaxedCellResult(httk.Result):

    @httk.httk_typed_init({'computation': httk.Computation, 'compound': Compound, 'relaxed_structure': Structure, 'primitive_cell': Cell, 'volume_per_atom': float, 'minimum_energy': float})
    def __init__(self, computation, compound, relaxed_structure, primitive_cell, volume_per_atom, minimum_energy):
        self.computation = computation
        self.compound = compound
        self.relaxed_structure = relaxed_structure
        self.volume_per_atom = volume_per_atom
        self.primitive_cell = primitive_cell
        self.minimum_energy = minimum_energy
