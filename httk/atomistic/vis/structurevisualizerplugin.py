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
from httk.atomistic import Structure, UnitcellStructure


class StructureVisualizerPlugin(HttkPlugin):
            
    def plugin_init(self, struct):
        #print "StructureVisualizerPlugin called",struct
        self.struct = struct
        self.visualizer = None

    def wait(self):
        if self.visualizer is not None:
            self.visualizer.wait()

    def params(self):
        return self.visualizer.params

    def show(self, params={}, backends=['jmol', 'ase'], debug=False):
        for backend in backends:
            if backend == 'jmol':
                try:
                    from jmolstructurevisualizer import JmolStructureVisualizer
                    self.visualizer = JmolStructureVisualizer(self.struct, params)
                    self.visualizer.show()
                    #self.visualizer.rotate()
                    return
                except ImportError:
                    if debug:
                        raise
                    pass
            if backend == 'ase':
                try:
                    from asestructurevisualizer import AseStructureVisualizer
                    self.visualizer = AseStructureVisualizer(self.struct, params)
                    self.visualizer.show()
                    return
                except ImportError:
                    if debug:
                        raise
                    pass
        raise Exception("StructureVisualizerPlugin.show: None of the requested / available backends available, tried:"+str(backends))

Structure.vis = HttkPluginWrapper(StructureVisualizerPlugin)
UnitcellStructure.vis = HttkPluginWrapper(StructureVisualizerPlugin)
