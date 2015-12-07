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
from httk.atomistic.structurephasediagram import StructurePhaseDiagram
import httk.analysis.matsci.vis


class StructurePhaseDiagramVisualizerPlugin(HttkPlugin):
            
    def plugin_init(self, structurephasediagram):
        print "PhaseDiagramVisualizerPlugin called"
        self.structurephasediagram = structurephasediagram

    def show(self, **params):        
        self.structurephasediagram.get_phasediagram().vis.show(**params)

StructurePhaseDiagram.vis = HttkPluginWrapper(StructurePhaseDiagramVisualizerPlugin)
