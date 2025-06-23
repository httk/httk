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

from httk.core.httkobject import HttkPlugin, HttkPluginWrapper
from httk.atomistic.representativestructure import RepresentativeStructure
from httk.atomistic.unitcellstructure import UnitcellStructure


class StructureFormulaPlugin(HttkPlugin):

    def plugin_init(self, struct):
        self.struct = struct

RepresentativeStructure.formula_builder = HttkPluginWrapper(StructureFormulaPlugin)
UnitcellStructure.formula_builder = HttkPluginWrapper(StructureFormulaPlugin)
