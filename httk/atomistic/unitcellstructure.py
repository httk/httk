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
from unitcellsites import UnitcellSites
from data import spacegroups
from structureutils import *
from spacegroup import Spacegroup


class UnitcellStructure(HttkObject):

    """
    A UnitcellStructure represents N sites of, e.g., atoms or ions, in any periodic or non-periodic arrangement. 
    It keeps track of all the copies of the atoms within a unitcell.
    
    The structure object is meant to be immutable and assumes that no internal variables are changed after its creation. 
    All methods that 'changes' the object creates and returns a new, updated, structure object.
    
    Naming conventions in httk.atomistic:

    For cells:
        cell = an abstract name for any reasonable representation of a 'cell' that defines 
               the basis vectors used for representing the structure. When a 'cell' is returned,
               it is an object of type Cell

        basis = a 3x3 sequence-type with (in rows) the three basis vectors (for a periodic system, defining the unit cell, and defines the unit of repetition for the periodic dimensions)

        lengths_and_angles = (a,b,c,alpha,beta,gamma): the basis vector lengths and angles

        niggli_matrix = ((v1*v1, v2*v2, v3*v3),(2*v2*v3, 2*v1*v3, 2*v2*v3)) where v1, v2, v3 are the vectors forming the basis

        metric = ((v1*v1,v1*v2,v1*v3),(v2*v1,v2*v2,v2*v3),(v3*v1,v3*v2,v3*v3))

    For sites:
        These following prefixes are used to describe types of site specifications:
            representative cell/rc = only representative atoms are given, which are then to be 
            repeated by structure symmetry group to give all sites

            unit cell/uc = all atoms in unitcell
            
            reduced = coordinates given in cell vectors
            
            cartesian = coordinates given as direct cartesian coordinates

        sites = used as an abstract name for any sensible representation of a list of coordinates and a cell,
                when a 'sites' is returned, it is an object of type Sites 
                  
        counts = number of atoms of each type (one per entry in assignments)
      
        coordgroups = coordinates represented as a 3-level-list of coordinates, e.g. 
        [[[0,0,0],[0.5,0.5,0.5]],[[0.25,0.25,0.25]]] where level-1 list = groups: one group for each equivalent atom

        counts and coords = one list with the number of atoms of each type (one per entry in assignments)
        and a 2-level list of coordinates.

    For assignments of atoms, etc. to sites:
        assignments = abstract name for any representation of assignment of atoms.
        When returned, will be object of type Assignment.

        atomic_numbers = a sequence of integers for the atomic number of each species

        occupations = a sequence where the assignments are *repeated* for each coordinate as needed 
        (prefixed with uc or rc depending on which coordinates)

    For cell scaling:
        scaling = abstract name for any representation of cell scaling
        
        scale = multiply all basis vectors with this number

        volume = rescaling the cell such that it takes this volume

    For periodicity:
        periodicity = abstract name of a representation of periodicity

        pbc = 'periodic boundary conditions' = sequence of True and False for which basis vectors are periodic / non-periodic

        nonperiodic_vecs = integer, number of basis vectors, counted from the first, which are non-periodic

    For spacegroup:
        spacegroup = abstract name for any spacegroup representation. When returned, is of type Spacegroup.

        hall_symbol = specifically the hall_symbol string representation of the spacegroup      
   
    """
    @httk_typed_init({'assignments': Assignments, 'uc_sites': UnitcellSites, 'uc_cell': Cell},
                     index=['assignments', 'uc_sites', 'uc_cell'])    
    def __init__(self, assignments=None, uc_sites=None, uc_cell=None):
        """
        Private constructor, as per httk coding guidelines. Use Structure.create instead.
        """
        self.assignments = assignments
        self.uc_cell = uc_cell
        self.uc_sites = uc_sites

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
                   
               assignments=None, 
               
               periodicity=None, nonperiodic_vecs=None, 

               other_reps=None,
               
               refs=None, tags=None):
        """
        A FullStructure represents N sites of, e.g., atoms or ions, in any periodic or non-periodic arrangement, where the positions
        of all cites are given (as opposed to a set of unique sites + symmetry operations). 

        This is a swiss-army-type constructor that allows several different ways to create a FullStructure object.    

        To create a new structure, three primary components are:

           - cell: defines the basis vectors in which reduced coordinates are expressed, and the 
             unit of repetition (*if* the structure has any periodicity - see the 'periodicity' parameter)

           - assignments: a list of 'things' (atoms, ions, etc.) that goes on the sites in the structure

           - sites: a sensible representation of location / coordinates of the sites.

        Note: `uc_`-prefixes are consistently enforced for any quantity that would be different in a UniqueSitesStructure. This is to 
        allow for painless change between the various structure-type objects without worrying about accidently using
        the wrong type of sites object.  
      
        Note: see help(Structure) for parameter naming conventions, i.e., what type of object is expected given a parameter name.      
           
        Input parameters:

           - ONE OF: 'uc_cell'; 'uc_basis', 'uc_length_and_angles'; 'uc_niggli_matrix'; 'uc_metric'; 
             all of: uc_a,uc_b,uc_c, uc_alpha, uc_beta, uc_gamma. 
             (cell requires a Cell object or a very specific format, so unless you know what you are doing, use one of the others.)

           - ONE OF: 'uc_assignments', 'uc_atomic_numbers', 'uc_occupations'
             (uc_assignments requires an Assignments object or a sequence.), uc_occupations repeats similar site assignments as needed
           
           - ONE OF: 'uc_sites', 'uc_coords' (IF uc_occupations OR uc_counts are also given), or
             'uc_B_C', where B=reduced or cartesian, C=coordgroups, coords, or occupationscoords

             Notes: 

                  - occupationscoords may differ from coords by *order*, since giving occupations as, e.g., ['H','O','H'] does not necessarily
                    have the same order of the coordinates as the format of counts+coords as (2,1), ['H','O'].

                  - uc_sites requires a Sites object or a python list on a very specific format, (so unless you know what you are doing, 
                    use one of the others.)
                           
           - ONE OF: uc_scale, uc_volume, or volume_per_atom: 
                scale = multiply the basis vectors with this scaling factor, 
                volume = the unit cell volume (overrides 'scale' if both are given)
                volume_per_atom = cell volume / number of atoms

           - ONE OF periodicity or nonperiodic_vecs
           
        """          
        if structure is not None:
            UnitcellStructure.use(structure)

        #TODO: Handle that vollume_per_atom is given instead, move this block below sorting out sites and if uc_volume is not set,
        #calculate a new volume
        if uc_cell is not None:
            Cell.use(uc_cell)
        else:
            uc_cell = Cell.create(cell=uc_cell, basis=uc_basis, metric=uc_metric, 
                                  niggli_matrix=uc_niggli_matrix, 
                                  a=uc_a, b=uc_b, c=uc_c, 
                                  alpha=uc_alpha, beta=uc_beta, gamma=uc_gamma,
                                  lengths=uc_lengths, angles=uc_angles,
                                  scale=uc_scale, scaling=uc_scaling, volume=uc_volume)
        
        if uc_sites is not None:
            uc_sites = UnitcellSites.use(uc_sites)
        else:
            if uc_reduced_coordgroups is None and \
                    uc_reduced_coords is None and \
                    uc_occupancies is not None:
                    # Structure created by occupationscoords and occupations, this is a slightly tricky representation
                if uc_reduced_occupationscoords is not None:
                    assignments, uc_reduced_coordgroups = occupations_and_coords_to_assignments_and_coordgroups(uc_reduced_occupationscoords, uc_occupancies)
            
            if uc_reduced_coordgroups is not None or \
                    uc_reduced_coords is not None:

                try:
                    uc_sites = UnitcellSites.create(reduced_coordgroups=uc_reduced_coordgroups, 
                                                    reduced_coords=uc_reduced_coords, 
                                                    counts=uc_counts, 
                                                    periodicity=periodicity, occupancies=uc_occupancies)
                except Exception:
                    uc_sites = None
            
            else:
                uc_sites = None

        if uc_sites is None and uc_reduced_coordgroups is None and \
                uc_reduced_coords is None and uc_reduced_occupationscoords is None:
            # Cartesian coordinate input must be handled here in structure since scalelessstructure knows nothing about cartesian coordinates...
            if uc_cartesian_coordgroups is None and uc_cartesian_coords is None and \
                    uc_occupancies is not None and uc_cartesian_occupationscoords is not None:
                assignments, uc_cartesian_coordgroups = occupations_and_coords_to_assignments_and_coordgroups(uc_cartesian_occupationscoords, uc_occupancies)
             
            if uc_cartesian_coords is not None and uc_cartesian_coordgroups is None:
                uc_cartesian_coordgroups = coords_and_counts_to_coordgroups(uc_cartesian_coords, uc_counts)

            if uc_cell is not None: 
                uc_reduced_coordgroups = coordgroups_cartesian_to_reduced(uc_cartesian_coordgroups, uc_cell)

        if assignments is not None:
            assignments = Assignments.use(assignments)

        if uc_sites is None:
            raise Exception("Structure.create: not enough information for information about sites.")

        new = cls(assignments=assignments, uc_sites=uc_sites, uc_cell=uc_cell)

        return new
        
    @classmethod
    def use(cls, other):
        from structure import Structure
        from representativestructure import RepresentativeStructure
        if isinstance(other, UnitcellStructure):
            return other
        elif isinstance(other, Structure):
            return UnitcellStructure(other.assignments, other.uc_sites, other.uc_cell)
        elif isinstance(other, RepresentativeStructure):
            return cls.use(Structure.use(other))
        raise Exception("RepresentativeStructure.use: do not know how to use object of class:"+str(other.__class__))
           
    @property
    def uc_cartesian_occupationscoords(self):
        raise Exception("UnitcellStructure.uc_cartesian_occupationscoords: not implemented")
        return 

    @property
    def uc_cartesian_coordgroups(self):
        return self.uc_sites.get_cartesian_coordgroups(self.uc_cell)

    @property
    def uc_cartesian_coords(self):
        return self.uc_sites.get_cartesian_coords(self.uc_cell)

    @property
    def uc_reduced_coords(self):
        return self.uc_sites.reduced_coords

    @property
    def uc_lengths_and_angles(self):
        return [self.uc_a, self.uc_b, self.uc_c, self.uc_alpha, self.uc_beta, self.uc_gamma]

    @httk_typed_property(float)
    def uc_a(self):
        return self.uc_cell.a

    @httk_typed_property(float)
    def uc_b(self):
        return self.uc_cell.b

    @httk_typed_property(float)
    def uc_c(self):
        return self.uc_cell.c

    @httk_typed_property(float)
    def uc_alpha(self):
        return self.uc_cell.alpha

    @httk_typed_property(float)
    def uc_beta(self):
        return self.uc_cell.beta

    @httk_typed_property(float)
    def uc_gamma(self):
        return self.uc_cell.gamma

    @property
    def uc_basis(self):
        return self.uc_cell.basis

    @httk_typed_property(float)
    def uc_volume(self):
        return self.uc_cell.volume

    @httk_typed_property(float)
    def uc_volume_per_atom(self):
        return self.uc_cell.volume/self.uc_sites.total_number_of_atoms

    @httk_typed_property(int)
    def uc_cell_orientation(self):
        return self.uc_cell.orientation
    
    @httk_typed_property((bool, 1, 3))
    def pbc(self):
        return self.uc_sites.pbc

    @property
    def uc_reduced_coordgroups(self):
        return self.uc_sites.reduced_coordgroups

    @httk_typed_property([int])
    def uc_counts(self):
        return self.uc_sites.counts

    def transform(self, matrix, max_search_cells=20, max_atoms=1000):
        return transform(self, matrix, max_search_cells=max_search_cells, max_atoms=max_atoms)

    def __str__(self):
        return "<httk UnitcellStructure object:\n  "+str(self.uc_cell)+"\n  "+str(self.assignments)+"\n  "+str(self.uc_sites)+"\n>" 

