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
The httk.atomistic package

Classes and utilities for dealing with high-throughput calculations of atomistic systems.

"""

import httk

#from httk.core import *
from httk.atomistic.structure import Structure, StructureRef, StructureTag
from httk.atomistic.unitcellstructure import UnitcellStructure
from httk.atomistic.representativestructure import RepresentativeStructure
from httk.atomistic.representativesites import RepresentativeSites
from httk.atomistic.unitcellsites import UnitcellSites
from httk.atomistic import formulautils
from httk.atomistic import supercellutils
from httk.atomistic.cell import Cell
#from representativesitesstructure import RepresentativeSitesStructure
from httk.atomistic.assignments import Assignments
from httk.atomistic.spacegroup import Spacegroup
from httk.atomistic.compound import Compound, CompoundStructure, CompoundRef, CompoundTag, ComputationRelatedCompound
from httk.atomistic.structurephasediagram import StructurePhaseDiagram

import io as _atomistic_io

__all__ = ["Structure", "Cell", "RepresentativeSites", "UnitcellSites", "Assignments",
           "Compound", "CompoundStructure", "StructurePhaseDiagram", "StructureRef", "StructureTag",
           "CompoundTag", "CompoundRef", "UnitcellStructure", "RepresentativeStructure"]

from httk.atomistic import atomisticio
