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

import httk.external.ase_glue

class AseStructureVisualizer(object):

    def __init__(self, struct, params={}):
        self.struct = struct
        self.params = params
         
    def show(self):
        ase_atoms = self.struct.ase.to_Atoms()
        #ase_atoms = httk.iface.ase_if.ase_atoms_to_structure(self.struct)
        ase_glue.ase.visualize.view(ase_atoms)
        
    def wait(self):
        pass

    
