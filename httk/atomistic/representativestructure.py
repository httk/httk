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
from httk.core.httkobject import HttkObject, httk_typed_property, httk_typed_property_resolve, httk_typed_property_delayed, httk_typed_init
from httk.core.reference import Reference
from cell import Cell
from assignments import Assignments
from representativesites import RepresentativeSites
from data import spacegroups
from structureutils import *
from spacegroup import Spacegroup


class RepresentativeStructure(HttkObject):

    """
    A RepresentativeStructure represents N sites of, e.g., atoms or ions, in any periodic or non-periodic arrangement. 
    It keeps track of a set of representative atoms in a unit cell (the conventional cell) and the symmetry group / operations
    that are to be applied to them to get all atoms.

    This is meant to be a light-weight Structure object. For a heavy-weight with more functionality, use Structure.

    The RepresentativeStructure object is meant to be immutable and assumes that no internal variables are changed after its creation. 
    All methods that 'changes' the object creates and returns a new, updated, structure object.
    """
    @httk_typed_init({'assignments': Assignments, 'rc_sites': RepresentativeSites, 
                      'rc_cell': Cell},
                     index=['assignments', 'rc_sites', 'rc_cell'])    
    def __init__(self, assignments, rc_sites=None, rc_cell=None):
        """
        Private constructor, as per httk coding guidelines. Use ReducedCellStructure.create instead.
        """
        self.assignments = assignments
        self.rc_cell = rc_cell
        self.rc_sites = rc_sites
        
    @classmethod
    def create(cls,
               structure=None,

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
               rc_scale=None, rc_scaling=None, rc_volume=None, vol_per_atom=None,
               
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
           
        Note: `rc_`-prefixes are consistently enforced for any quantity that would be different in a UnitcellStructure. This is to 
        allow for painless change between the various structure-type objects without worrying about accidently using
        the wrong type of sites object.  

        Input parameters:
        
           - ONE OF: 'cell'; 'basis', 'length_and_angles'; 'niggli_matrix'; 'metric'; all of: a,b,c, alpha, beta, gamma. 
             (cell requires a Cell object or a very specific format, so unless you know what you are doing, use one of the others.)

           - ONE OF: 'assignments', 'atomic_numbers', 'occupancies'
             (assignments requires an Assignments object or a sequence.), occupations repeats similar site assignments as needed
           
           - ONE OF: 'rc_sites', 'rc_coords' (IF rc_occupations OR rc_counts are also given), 
             'uc_coords' (IF uc_occupations OR uc_counts are also given)
             'rc_B_C', where B=reduced or cartesian, C=coordgroups, coords, or occupationscoords
             
             Notes: 

                  - occupationscoords may differ from coords by *order*, since giving occupations as, e.g., ['H','O','H'] does not necessarily
                    have the same order of the coordinates as the format of counts+coords as (2,1), ['H','O'].

                  - rc_sites and uc_sites requires a Sites object or a very specific format, so unless you know what you are doing, 
                    use one of the others.)
           
           - ONE OF: scale or volume: 
                scale = multiply the basis vectors with this scaling factor, 
                volume = the representative (conventional) cell volume (overrides 'scale' if both are given)
                volume_per_atom = cell volume / number of atoms

           - ONE OF periodicity or nonperiodic_vecs
           
        See help(Structure) for more information on the data format of all these data representations.
        """   
        if structure is not None:
            return cls.use(structure)

        if isinstance(spacegroup, Spacegroup):
            hall_symbol = spacegroup.hall_symbol
        else:
            try:
                spacegroupobj = Spacegroup.create(spacegroup=spacegroup, hall_symbol=hall_symbol, spacegroupnumber=spacegroupnumber, setting=setting) 
                hall_symbol = spacegroupobj.hall_symbol
            except Exception:                
                spacegroupobj = None                
                hall_symbol = None

        if rc_cell is not None:
            rc_cell = Cell.use(rc_cell)
        else:                        
            try:                        
                rc_cell = Cell.create(cell=rc_cell, basis=rc_basis, metric=rc_metric, 
                                      niggli_matrix=rc_niggli_matrix, 
                                      a=rc_a, b=rc_b, c=rc_c, 
                                      alpha=rc_alpha, beta=rc_beta, gamma=rc_gamma,
                                      lengths=rc_lengths, angles=rc_angles, 
                                      scale=rc_scale, scaling=rc_scaling, volume=rc_volume)
            except Exception:
                rc_cell = None

        if rc_sites is not None:
            rc_sites = RepresentativeSites.use(rc_sites)
        else:
            if rc_reduced_coordgroups is None and \
                    rc_reduced_coords is None and \
                    rc_occupancies is not None:
                    # Structure created by occupationscoords and occupations, this is a slightly tricky representation
                if rc_reduced_occupationscoords is not None:     
                    assignments, rc_reduced_coordgroups = occupations_and_coords_to_assignments_and_coordgroups(rc_reduced_occupationscoords, rc_occupancies)

            if rc_reduced_coordgroups is not None or \
                    rc_reduced_coords is not None:
                                                                                    
                try:
                    rc_sites = RepresentativeSites.create(reduced_coordgroups=rc_reduced_coordgroups, 
                                                          reduced_coords=rc_reduced_coords, 
                                                          counts=rc_counts,
                                                          hall_symbol=hall_symbol, periodicity=periodicity, wyckoff_symbols=wyckoff_symbols,
                                                          multiplicities=multiplicities, occupancies=rc_occupancies)
                except Exception as e:
                    raise
                    #print "Ex",e
                    rc_sites = None
            else:
                rc_sites = None

        if rc_sites is None and rc_reduced_coordgroups is None and \
                rc_reduced_coords is None and rc_reduced_occupationscoords is None:
            # Cartesian coordinate input must be handled here in structure since scalelessstructure knows nothing about cartesian coordinates...
            if rc_cartesian_coordgroups is None and rc_cartesian_coords is None and \
                    rc_occupancies is not None and rc_cartesian_occupationscoords is not None:
                assignments, rc_cartesian_coordgroups = occupations_and_coords_to_assignments_and_coordgroups(rc_cartesian_occupationscoords, rc_occupancies)
             
            if rc_cartesian_coords is not None and rc_cartesian_coordgroups is None:
                rc_cartesian_coordgroups = coords_and_counts_to_coordgroups(rc_cartesian_coords, rc_counts)

            if rc_cell is not None:  
                rc_reduced_coordgroups = coordgroups_cartesian_to_reduced(rc_cartesian_coordgroups, rc_cell)
            
        if rc_sites is None:
            raise Exception("Structure.create: representative sites specifications invalid.")

        if assignments is not None:
            assignments = Assignments.use(assignments)

        if assignments is None or (rc_sites is None or rc_cell is None or hall_symbol is None):
            raise Exception("Structure.create: not enough information given to create a structure object.")

        new = cls(assignments=assignments, rc_sites=rc_sites, rc_cell=rc_cell)

        return new

    @classmethod
    def use(cls, other):
        from structure import Structure
        from unitcellstructure import UnitcellStructure
        if isinstance(other, RepresentativeStructure):
            return other
        elif isinstance(other, Structure):
            return RepresentativeStructure(other.assignments, other.rc_sites, other.rc_cell)
        elif isinstance(other, UnitcellStructure):
            return cls.use(Structure.use(other))
        raise Exception("RepresentativeStructure.use: do not know how to use object of class:"+str(other.__class__))

    @property
    def rc_cartesian_occupationscoords(self):
        raise Exception("Structure.rc_cartesian_occupationscoords: not implemented")
        return 

    @property
    def rc_cartesian_coordgroups(self):
        return self.rc_sites.get_cartesian_coordgroups(self.rc_cell)

    @property
    def rc_cartesian_coords(self):
        return self.rc_sites.get_cartesian_coords(self.rc_cell)

    @property
    def rc_lengths_and_angles(self):
        return [self.rc_a, self.rc_b, self.rc_c, self.rc_alpha, self.rc_beta, self.rc_gamma]

    @httk_typed_property(float)
    def rc_a(self):
        return self.rc_cell.a

    @httk_typed_property(float)
    def rc_b(self):
        return self.rc_cell.b

    @httk_typed_property(float)
    def rc_c(self):
        return self.rc_cell.c

    @httk_typed_property(float)
    def rc_alpha(self):
        return self.rc_cell.alpha

    @httk_typed_property(float)
    def rc_beta(self):
        return self.rc_cell.beta

    @httk_typed_property(float)
    def rc_gamma(self):
        return self.rc_cell.gamma

    @property
    def rc_basis(self):
        return self.rc_cell.basis

    @httk_typed_property(float)
    def rc_volume(self):
        return self.rc_cell.volume

    @httk_typed_property(int)
    def rc_cell_orientation(self):
        return self.rc_cell.orientation

    @httk_typed_property((bool, 1, 3))
    def pbc(self):
        return self.rc_sites.pbc

    @httk_typed_property(float)
    def uc_volume_per_atom(self):
        return self.uc_cell.volume/self.uc_sites.total_number_of_atoms

    def clean(self):        
        rc_sites = self.rc_sites.clean()
        rc_cell = self.rc_cell.clean()

        new = self.__class__(self.assignments, rc_sites, rc_cell)
        new.add_tags(self.get_tags())
        new.add_refs(self.get_refs())               
        return new


def main():
    print "Test"
        
if __name__ == "__main__":
    main()
    
