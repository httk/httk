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
import sys
from structure import Structure
from httk.core import FracScalar, httk_typed_init
from httk.core.httkobject import HttkObject
from httk.analysis.matsci.phasediagram import PhaseDiagram 


class StructurePhaseDiagramCompetingIndicies(HttkObject):

    @httk_typed_init({'indices': [int]})
    def __init__(self, indices):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """    
        self.indices = indices

    @classmethod
    def create(cls, indices):
        return cls(indices)


class StructurePhaseDiagram(HttkObject):

    """
    Represents a phase diagram of structures
    """
 
    @httk_typed_init({'structures': [Structure], 'energies': [FracScalar],
                      'hull_indices': [int],
                      'competing_indices': [StructurePhaseDiagramCompetingIndicies],
                      'hull_competing_indices': [StructurePhaseDiagramCompetingIndicies],
                      'hull_distances': [FracScalar],
                      'coord_system': [str],
                      'phase_lines': [int, int]},
                     index=['structures'])   
    def __init__(self, structures, energies, hull_indices, competing_indices,
                 hull_competing_indices,
                 hull_distances, coord_system, phase_lines):
        """
        Private constructor, as per httk coding guidelines. Use Cell.create instead.
        """    
        self.structures = structures
        self.energies = energies
        self.hull_indices = hull_indices
        self.competing_indices = competing_indices
        self.hull_competing_indices = hull_competing_indices
        self.hull_distances = hull_distances
        self.coord_system = coord_system
        self.phase_lines = phase_lines

    #def create(cls, basis=None, a=None, b=None, c=None, alpha=None, beta=None, gamma=None, volume=None, scale=None, niggli_matrix=None, orientation=1, lengths=None, angles=None, normalize=True):
            
    @classmethod
    def create(cls, structures, energies):
        """        
        """      
        pd = setup_phasediagram(structures, energies)

        competing_indices = [StructurePhaseDiagramCompetingIndicies.create(x) for x in pd.competing_indices]
        hull_competing_indices = [StructurePhaseDiagramCompetingIndicies.create(x) for x in pd.hull_competing_indices]
        
        return cls(structures, energies, pd.hull_indices, competing_indices,
                   hull_competing_indices,
                   pd.hull_distances, pd.coord_system, pd.phase_lines)

    def get_phasediagram(self):        
        competing_indices = [x.indices for x in self.competing_indices]
        hull_competing_indices = [x.indices for x in self.hull_competing_indices]

        pd = setup_phasediagram(self.structures, self.energies)
        pd.set_hull_data(self.hull_indices, competing_indices,
                         hull_competing_indices,
                         self.hull_distances, self.coord_system, self.phase_lines)

        return pd

from httk.core import FracVector


def setup_phasediagram(structures, energies):
    pd = PhaseDiagram() 
    for i in range(len(structures)):
        struct = structures[i]
        energy = energies[i]
        formula = struct.uc_formula
        uc_formula_symbols = struct.uc_formula_symbols
        uc_formula_counts = struct.uc_formula_counts
        pd.add_phase(uc_formula_symbols, uc_formula_counts, formula, energy)        

    return pd

       
def main():
    pass

if __name__ == "__main__":
    main()
    
    
