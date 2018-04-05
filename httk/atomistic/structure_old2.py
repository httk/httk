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
import math

from httk.core.httkobject import HttkObject, HttkPluginPlaceholder, httk_typed_property, httk_typed_property_resolve, httk_typed_property_delayed, httk_typed_init
from httk.core.reference import Reference
from httk.core import FracScalar
from httk.core.basic import breath_first_idxs
from cell import Cell
from assignments import Assignments
from sites import Sites
from unitcellsites import UnitcellSites
from representativesites import RepresentativeSites
from data import spacegroups
from structureutils import *
from spacegroup import Spacegroup
from scalelessstructure import ScalelessStructure


class Structure(HttkObject):

    """
    There is not really any Structure object in httk.atomistic. This is just a convinience wrapper to create 
    RepresentativeStructure or UnitcellStructur objects via a .create constructor.
    """
    
    def __init__(self):
        raise Exception("Direct call to Structure.__init__, need to call .create instead, or __init__ on RepresentativeStructure or UnitcellStructure.")
        
    @classmethod
    def create(cls,
               structure=None,

               uc_cell=None, uc_basis=None, uc_lengths=None, 
               uc_angles=None, uc_niggli_matrix=None, uc_metric=None,
               uc_a=None, uc_b=None, uc_c=None, 
               uc_alpha=None, uc_beta=None, uc_gamma=None,
               uc_sites=None, 
               uc_reduced_coordgroups=None, uc_cartesian_coordgroups=None,
               uc_reduced_coords=None, uc_cartesian_coords=None,  
               uc_reduced_occupationscoords=None, uc_cartesian_occupationscoords=None,
               uc_occupancies=None, uc_counts=None,
               uc_scale=None, uc_scaling=None, uc_volume=None, volume_per_atom=None,
               uc_is_primitive_cell=False, uc_is_conventional_cell=False,

               rc_cell=None, rc_basis=None, rc_lengths=None, 
               rc_angles=None, rc_niggli_matrix=None, rc_metric=None, 
               rc_a=None, rc_b=None, rc_c=None, 
               rc_alpha=None, rc_beta=None, rc_gamma=None,
               rc_sites=None, 
               rc_reduced_coordgroups=None, rc_cartesian_coordgroups=None,
               rc_reduced_coords=None, rc_cartesian_coords=None,  
               rc_reduced_occupationscoords=None, rc_cartesian_occupationscoords=None,
               rc_occupancies=None, rc_counts=None, 
               wyckoff_symbols=None, multiplicities=None,
               spacegroup=None, hall_symbol=None, spacegroupnumber=None, setting=None,
               rc_scale=None, rc_scaling=None, rc_volume=None, 
               
               assignments=None, 
               
               periodicity=None, nonperiodic_vecs=None,
               refs=None, tags=None):
        """
        A Structure represents N sites of, e.g., atoms or ions, in any periodic or non-periodic arrangement. 

        This is a swiss-army-type constructor that allows a selection between a large number of optional arguments.    

        To create a new structure, three primary components are:
           - cell: defines the basis vectors in which reduced coordinates are expressed, and the 
                   unit of repetition (*if* the structure has any periodicity - see the 'periodicity' parameter)
           - assignments: a list of 'things' (atoms, ions, etc.) that goes on the sites in the structure
           - sites: a sensible representation of location / coordinates of the sites.
           
           However, two options exists for representing the sites; either as only giving the representative sites, which when the 
           symmetry operations of the spacegroup are applied generates all sites, or, simply giving the primcell set of sites.
           Since conversion between these are computationally expensive and only strictly 'approximate'. Hence, sites is divided
           accordingly into rc_sites and uc_sites keeping track of the two representations.

         Input:

           - ONE OF: 'cell'; 'basis', 'length_and_angles'; 'niggli_matrix'; 'metric'; all of: a,b,c, alpha, beta, gamma. 
             (cell requires a Cell object or a very specific format, so unless you know what you are doing, use one of the others.)

           - ONE OF: 'assignments', 'atomic_numbers', 'occupancies'
             (assignments requires an Assignments object or a sequence.), occupations repeats similar site assignments as needed
           
           - ONE OF: 'rc_sites', 'uc_sites', 'rc_coords' (IF rc_occupations OR rc_counts are also given), 
             'uc_coords' (IF uc_occupations OR uc_counts are also given)
             'A_B_C', where A=representative or primcell, B=reduced or cartesian, C=coordgroups, coords, or occupationscoords
             
             Notes: 

                  - occupationscoords may differ to coords by *order*, since giving occupations as, e.g., ['H','O','H'] requires
                    a re-ordering of coordinates to the format of counts+coords as (2,1), ['H','O']. 

                  - rc_sites and uc_sites requires a Sites object or a very specific format, so unless you know what you are doing, 
                    use one of the others.)
           
           - ONE OF: 'spacegroup' or 'hall_symbol', or neither (in which case spacegroup is regarded as unknown)                

           - ONE OF: scale or volume: 
             scale = multiply the basis vectors with this scaling factor, 
             volume = rescale the cell into this volume (overrides 'scale' if both are given)

           - ONE OF periodicity or nonperiodic_vecs
           
        See help(Structure) for more information on the data format of all these data representations.
        """                  
        #TODO: Create either representativestruct or unitcellstruct depending on input, if both given,
        #return representativestruct with other_reps given
        return new


class StructureTag(HttkObject):                               

    @httk_typed_init({'structure': Structure, 'tag': str, 'value': str},
                     index=['structure', 'tag', ('tag', 'value'), ('structure', 'tag', 'value')], skip=['hexhash'])    
    def __init__(self, structure, tag, value):
        super(StructureTag, self).__init__()
        self.tag = tag
        self.structure = structure
        self.value = value

    def __str__(self):
        return "(Tag) "+self.tag+": "+self.value+""


class StructureRef(HttkObject):

    @httk_typed_init({'structure': Structure, 'reference': Reference},
                     index=['structure', 'reference'], skip=['hexhash'])        
    def __init__(self, structure, reference):
        super(StructureRef, self).__init__()
        self.structure = structure
        self.reference = reference

    def __str__(self):
        return str(self.reference.ref)


def main():
    print "Test"
        
if __name__ == "__main__":
    main()
    
