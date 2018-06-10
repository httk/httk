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
from cellutils import get_primitive_to_conventional_basis_transform
from assignments import Assignments
from sites import Sites
from unitcellsites import UnitcellSites
from representativesites import RepresentativeSites
from data import spacegroups
from structureutils import *
from spacegroup import Spacegroup
from unitcellstructure import UnitcellStructure
from representativestructure import RepresentativeStructure
from spacegrouputils import spacegroup_get_number_and_setting


class Structure(HttkObject):  

    """
    A Structure represents N sites of, e.g., atoms or ions, in any periodic or non-periodic arrangement. 
    The structure object is meant to be immutable and assumes that no internal variables are changed after its creation. 
    All methods that 'changes' the object creates and returns a new, updated, structure object.

    This is the general heavy weight structure object. For lightweight structure objects, use UnitcellStructure or 
    RepresentativeStructure.
    
    Naming conventions in httk.atomistic:

    Structure cell type abbreviations:
        rc = Representative cell: only representative atoms are given inside the conventional cell.
             they need to be replicated by the symmetry elements.

        uc = Unit cell: any (imprecisely defined) unit cell (usually the unit cell used to define the structure
             if it was not done via a representative cell.) with all atoms inside.
             
        pc = Primitive unit cell: a smallest possible unit cell (the standard one) with all atoms inside.
        
        cc = Conventional unit cell: the high symmetry unit cell (rc) with all atoms inside.

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
    @httk_typed_init({'assignments': Assignments, 'rc_sites': RepresentativeSites, 
                      'rc_cell': Cell},
                     index=['assignments', 'rc_sites', 'rc_cell'])    
    def __init__(self, assignments, rc_sites=None, rc_cell=None, other_reps=None):
        """
        Private constructor, as per httk coding guidelines. Use ReducedCellStructure.create instead.
        """
        self.assignments = assignments
        self.rc_cell = rc_cell
        self.rc_sites = rc_sites
        if other_reps is None:
            other_reps = {}
        self._other_reps = other_reps

        self._tags = None
        self._refs = None
        self._spacegroup = None

        self._codependent_callbacks = []
        self._codependent_data = []
        self._codependent_info = [{'class': StructureTag, 'column': 'structure', 'add_method': 'add_tags'},
                                  {'class': StructureRef, 'column': 'structure', 'add_method': 'add_refs'}]
        
    @classmethod
    def create(cls,
               structure=None,

               assignments=None, 
                              
               rc_cell=None, rc_basis=None, rc_lengths=None, 
               rc_angles=None, rc_cosangles=None, rc_niggli_matrix=None, rc_metric=None, 
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

               uc_cell=None, uc_basis=None, uc_lengths=None, 
               uc_angles=None, uc_cosangles=None, uc_niggli_matrix=None, uc_metric=None,
               uc_a=None, uc_b=None, uc_c=None, 
               uc_alpha=None, uc_beta=None, uc_gamma=None,
               uc_sites=None, 
               uc_reduced_coordgroups=None, uc_cartesian_coordgroups=None,
               uc_reduced_coords=None, uc_cartesian_coords=None,  
               uc_reduced_occupationscoords=None, uc_cartesian_occupationscoords=None,
               uc_occupancies=None, uc_counts=None,
               uc_scale=None, uc_scaling=None, uc_volume=None, 
               uc_is_primitive_cell=False, uc_is_conventional_cell=False,
               
               volume_per_atom=None, periodicity=None, nonperiodic_vecs=None, 
               refs=None, tags=None):
        """
        A Structure represents N sites of, e.g., atoms or ions, in any periodic or non-periodic arrangement. 

        This is a swiss-army-type constructor that allows a selection between a large number of optional arguments.    

        Note: if redundant and non-compatible information is given, the behavior is undefined. E.g., don't try to call this
        with a structure + a volume in hopes to get a copy with rescaled volume.

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
        rc_cell_exception = None
        uc_cell_exception = None
        rc_sites_exception = None
        uc_sites_exception = None
        spacegroup_exception = None

        #print "NEW STRUCTURE",rc_angles, rc_cosangles, rc_lengths

        if structure is not None:
            return cls.use(structure)

        if isinstance(spacegroup, Spacegroup):
            hall_symbol = spacegroup.hall_symbol
        else:
            try:
                spacegroupobj = Spacegroup.create(spacegroup=spacegroup, hall_symbol=hall_symbol, spacegroupnumber=spacegroupnumber, setting=setting) 
                hall_symbol = spacegroupobj.hall_symbol
            except Exception as e:                                
                spacegroup_exception = (e, None, sys.exc_info()[2])
                spacegroupobj = None                
                hall_symbol = None

        #TODO: Handle that vollume_per_atom is given instead, move this block below sorting out sites and if uc_volume is not set,
        #calculate a new volume
        if uc_cell is not None:
            uc_cell = Cell.use(uc_cell)
        else:
            try:                        
                uc_cell = Cell.create(basis=uc_basis, metric=uc_metric, 
                                      niggli_matrix=uc_niggli_matrix, 
                                      a=uc_a, b=uc_b, c=uc_c, 
                                      alpha=uc_alpha, beta=uc_beta, gamma=uc_gamma,
                                      lengths=uc_lengths, angles=uc_angles, cosangles=uc_cosangles,
                                      scale=uc_scale, scaling=uc_scaling, volume=uc_volume)
            except Exception as e:
                uc_cell_exception = (e, None, sys.exc_info()[2])
                uc_cell = None

        if rc_cell is not None:
            rc_cell = Cell.use(rc_cell)
        else:
            try:                        
                rc_cell = Cell.create(cell=rc_cell, basis=rc_basis, metric=rc_metric, 
                                      niggli_matrix=rc_niggli_matrix, 
                                      a=rc_a, b=rc_b, c=rc_c, 
                                      alpha=rc_alpha, beta=rc_beta, gamma=rc_gamma,
                                      lengths=rc_lengths, angles=rc_angles, cosangles=rc_cosangles,
                                      scale=rc_scale, scaling=rc_scaling, volume=rc_volume)
            except Exception as e:
                rc_cell_exception = (e, None, sys.exc_info()[2])
                rc_cell = None

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
                except Exception as e:
                    uc_sites_exception = (e, None, sys.exc_info()[2])
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

        if isinstance(rc_sites, RepresentativeSites):
            rc_sites = rc_sites
        if isinstance(rc_sites, Sites):
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
                    if spacegroup is None:
                        rc_sites = RepresentativeSites.create(reduced_coordgroups=rc_reduced_coordgroups, 
                                                              reduced_coords=rc_reduced_coords, 
                                                              counts=rc_counts,
                                                              hall_symbol=hall_symbol, periodicity=periodicity, wyckoff_symbols=wyckoff_symbols,
                                                              multiplicities=multiplicities, occupancies=rc_occupancies)
                    else:
                        rc_sites = RepresentativeSites.create(reduced_coordgroups=rc_reduced_coordgroups, 
                                                              reduced_coords=rc_reduced_coords, 
                                                              counts=rc_counts,
                                                              spacegroup=spacegroup, periodicity=periodicity, wyckoff_symbols=wyckoff_symbols,
                                                              multiplicities=multiplicities, occupancies=rc_occupancies)
                        
                except Exception as e:
                    rc_sites_exception = (e, None, sys.exc_info()[2])
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
            
        if rc_sites is None and uc_sites is None:
            raise Exception("Structure.create: representative and unitcell sites specifications both invalid.")

        if assignments is not None:
            if isinstance(assignments, Assignments):
                assignments = assignments
            else:
                assignments = Assignments.create(assignments=assignments)

        if assignments is None or ((uc_sites is None or uc_cell is None) and (rc_sites is None or rc_cell is None or hall_symbol is None)):
            if rc_cell_exception is not None:
                raise rc_cell_exception[0], rc_cell_exception[1], rc_cell_exception[2]
            if rc_sites_exception is not None:
                raise rc_sites_exception[0], rc_sites_exception[1], rc_sites_exception[2]
            if rc_cell is not None and rc_sites is not None and hall_symbol is None:
                raise spacegroup_exception[0], spacegroup_exception[1], spacegroup_exception[2]
            if uc_cell_exception is not None:
                raise uc_cell_exception[0], uc_cell_exception[1], uc_cell_exception[2]
            if uc_sites_exception is not None:
                raise uc_sites_exception[0], uc_sites_exception[1], uc_sites_exception[2]
            raise Exception("Structure.create: not enough information given to create a structure object.")

        if uc_sites is not None and uc_cell is not None:
            uc_rep = UnitcellStructure.create(assignments=assignments, uc_cell=uc_cell, uc_sites=uc_sites)
            other_reps = {'uc': uc_rep}
        else:
            other_reps = {} 
                                            
        if (rc_sites is None or rc_cell is None or hall_symbol is None):
            new = cls.use(uc_rep)
            new._other_reps = other_reps
        else:                                       
            new = cls(assignments=assignments, rc_sites=rc_sites, rc_cell=rc_cell, other_reps=other_reps)

        if tags is not None:
            new.add_tags(tags)
        if refs is not None:
            new.add_refs(refs)               
        return new

    @classmethod
    def use(cls, other):
        if isinstance(other, Structure):
            return other
        if isinstance(other, UnitcellStructure):
            transform = get_primitive_to_conventional_basis_transform(other.uc_basis)
            newuc = other.transform(transform)
            rc_reduced_coordgroups, hall_symbol, wyckoff_symbols, multiplicities = spacegrouputils.trivial_symmetry_reduce(newuc.uc_reduced_coordgroups)
            return cls.create(assignments=newuc.assignments, rc_cell=newuc.uc_cell, 
                              rc_reduced_coordgroups=rc_reduced_coordgroups, 
                              wyckoff_symbols=wyckoff_symbols, 
                              multiplicities=multiplicities,
                              hall_symbol=hall_symbol)
            #return cls.create(assignments=other.assignments, rc_cell=other.uc_cell, 
            #                  rc_reduced_coordgroups=other.uc_reduced_coordgroups, 
            #                  wyckoff_symbols=['a']*sum([len(x) for x in other.uc_reduced_coordgroups]), 
            #                  multiplicities=[1]*sum([len(x) for x in other.uc_reduced_coordgroups]),
            #                  hall_symbol='P 1')
        if isinstance(other, RepresentativeStructure):
            #TODO: Implement simple symmetry finder that is better than this 
            return cls.create(assignments=other.assignments, rc_cell=other.rc_cell, 
                              rc_reduced_coordgroups=other.rc_reduced_coordgroups, 
                              wyckoff_symbols=other.wyckoff_symbols, 
                              multiplicities=other.multiplicities,
                              hall_symbol=other.hall_symbol)
                
        raise Exception("Structure.use: do not know how to use object of class:"+str(other.__class__))

    @property
    def uc(self):
        if 'uc' not in self._other_reps:            
            cc_struct = UnitcellStructure.create(assignments=self.assignments, uc_cell=self.rc_cell, uc_sites=self.rc_sites.get_uc_sites())
            self._other_reps['uc'] = cc_struct
            self._other_reps['cc'] = cc_struct
        return self._other_reps['uc']

    @property
    def pc(self):
        if 'pc' not in self._other_reps:
            prim_t = get_primitive_basis_transform(self.rc_sites.hall_symbol)            
            #print "PRIM TRANSFORM",prim_t.to_floats(),self.rc_cell.basis.to_floats()
            asotf = self.rc_cell.get_axes_standard_order_transform()
            if asotf is not None:
                self._other_reps['pc'] = self.cc.transform(prim_t*asotf)            
            else:
                self._other_reps['pc'] = self.cc.transform(prim_t)            
            if 'uc' not in self._other_reps:
                self._other_reps['uc'] = self._other_reps['pc']
            #print "RESULT",self._other_reps['pc'].uc_basis.to_floats(), self._other_reps['pc'].uc_sites.reduced_coordgroups.to_floats()
        return self._other_reps['pc']

    @property
    def cc(self):
        if 'cc' not in self._other_reps:
            cc_struct = UnitcellStructure.create(assignments=self.assignments, uc_sites=self.rc_sites.get_uc_sites(), uc_cell=self.rc_cell)
            self._other_reps['uc'] = cc_struct
            self._other_reps['cc'] = cc_struct
        return self._other_reps['cc']

    @property
    def rc(self):
        if 'rc' not in self._other_reps:
            rc_struct = RepresentativeStructure.create(assignments=self.assignments, rc_sites=self.rc_sites, rc_cell=self.rc_cell, hall_symbol=self.hall_symbol)
            self._other_reps['rc'] = rc_struct
        return self._other_reps['rc']

    def transform(self, matrix, max_search_cells=20, max_atoms=1000):
        return transform(self, matrix, max_search_cells=max_search_cells, max_atoms=max_atoms)

    @httk_typed_property(str)
    def hall_symbol(self):
        return self.rc_sites.hall_symbol

    @property
    def spacegroup(self):
        if self._spacegroup is None:
            self._spacegroup = Spacegroup.create(self.rc_sites.hall_symbol)
        return self._spacegroup

    @httk_typed_property(Cell)
    def uc_cell(self):
        return self.uc.uc_cell

    @httk_typed_property(UnitcellSites)
    def uc_sites(self):
        return self.uc.uc_sites
        
    @property
    def has_rc_repr(self):
        """
        Returns True if the structure already contains the representative coordinates + spacegroup, and thus can be queried for this data
        without launching an expensive symmetry finder operation. 
        """
        return True
           
    @property
    def has_uc_repr(self):
        """
        Returns True if the structure contains any unit cell-type coordinate representation, and thus can be queried for this data
        without launching a somewhat expensive cell filling operation. 
        """
        if 'uc' in self._other_reps:
            return True
        else:
            return False

    @property
    def rc_cartesian_occupationscoords(self):
        raise Exception("Structure.rc_cartesian_occupationscoords: not implemented")
        return 

    @property
    def rc_cartesian_coordgroups(self):
        return self.rc_sites.get_cartesian_coordgroups(self.rc_cell)

    @property
    def rc_reduced_coordgroups(self):
        return self.rc_sites.reduced_coordgroups

    @property
    def rc_reduced_coords(self):
        return self.rc_sites.reduced_coords

    @httk_typed_property([int])
    def rc_counts(self):
        return self.rc_sites.counts

    @httk_typed_property(int)
    def rc_nbr_atoms(self):
        return sum(self.rc_counts)

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

    @property
    def spacegroup_number_and_setting(self):
        return spacegroup_get_number_and_setting(self.rc_sites.hall_symbol)

    @httk_typed_property(int)
    def spacegroup_number(self):
        return int(spacegroup_get_number_and_setting(self.rc_sites.hall_symbol)[0])
    
    @property
    def uc_cartesian_occupationscoords(self):
        raise Exception("UnitcellStructure.uc_cartesian_occupationscoords: not implemented")
        return 

    def find_symmetry(self):
        return structure_reduced_uc_to_representative(self)

    @property
    def uc_cartesian_coordgroups(self):
        return self.uc.get_cartesian_coordgroups

    @property
    def uc_cartesian_coords(self):
        return self.uc.get_cartesian_coords

    @property
    def uc_lengths_and_angles(self):
        return [self.uc.uc_a, self.uc.uc_b, self.uc.uc_c, self.uc.uc_alpha, self.uc.uc_beta, self.uc.uc_gamma]

    @property
    def uc_a(self):
        return self.uc.uc_cell.a

    @property
    def uc_b(self):
        return self.uc.uc_cell.b

    @property
    def uc_c(self):
        return self.uc.uc_cell.c

    @property
    def uc_alpha(self):
        return self.uc.uc_cell.alpha

    @property
    def uc_beta(self):
        return self.uc.uc_cell.beta

    @property
    def uc_gamma(self):
        return self.uc.uc_cell.gamma

    @property
    def uc_basis(self):
        return self.uc.uc_cell.basis

    @property
    def uc_volume(self):
        return self.uc.uc_cell.volume

    @httk_typed_property(float)
    def volume_per_atom(self):
        return self.uc.uc_cell.volume/self.uc_sites.total_number_of_atoms

    @property
    def uc_cell_orientation(self):
        return self.uc.uc_cell.orientation
    
    @property
    def uc_reduced_coordgroups(self):
        return self.uc.uc_sites.reduced_coordgroups

    @property
    def uc_reduced_coords(self):
        return self.uc.uc_sites.reduced_coords

    @property
    def uc_counts(self):
        return self.uc.uc_sites.counts

    @property
    def uc_occupationssymbols(self):
        return coordgroups_and_assignments_to_symbols(self.uc_sites.reduced_coordgroups, self.assignments)

    @property
    def rc_occupationssymbols(self):
        return coordgroups_and_assignments_to_symbols(self.rc_sites.reduced_coordgroups, self.assignments)

    @property
    def uc_reduced_occupationscoords(self):
        raise Exception("Structure.uc_reduced_occupationscoords: not implemented")
        return 

    @property
    def rc_occupancies(self):
        coords, occupancies = coordgroups_and_assignments_to_coords_and_occupancies(self.rc_coordgroups, self.assignments)
        return occupancies

    @property
    def uc_occupancies(self):
        coords, occupancies = coordgroups_and_assignments_to_coords_and_occupancies(self.uc_reduced_coordgroups, self.assignments)
        return occupancies

    @httk_typed_property(bool)
    def extended(self):
        return self.assignments.extended

    @httk_typed_property([str])
    def extensions(self):
        return self.assignments.extensions

    def tidy(self):
        return structure_tidy(self).clean()

    @httk_typed_property(float)
    def pc_a(self):
        return self.pc.uc_cell.a

    @httk_typed_property(float)
    def pc_b(self):
        return self.pc.uc_cell.b

    @httk_typed_property(float)
    def pc_c(self):
        return self.pc.uc_cell.c

    @httk_typed_property(float)
    def pc_alpha(self):
        return self.pc.uc_cell.alpha

    @httk_typed_property(float)
    def pc_beta(self):
        return self.pc.uc_cell.beta

    @httk_typed_property(float)
    def pc_gamma(self):
        return self.pc.uc_cell.gamma

    @httk_typed_property(float)
    def pc_volume(self):
        return self.pc.uc_cell.volume

    @httk_typed_property([int])
    def pc_counts(self):
        return self.pc.uc_sites.counts

    @httk_typed_property(int)
    def pc_nbr_atoms(self):
        return sum(self.pc_counts)

    @httk_typed_property(int)
    def number_of_elements(self):
        seen = {}
        for symbol in self.formula_symbols:
            seen[symbol] = True
        return len(seen)
    
    @httk_typed_property((bool, 1, 3))
    #TODO: Do we need to rethink the pbc specifier, when cc and pc can have basis vectors in other directions...
    def pbc(self):
        return self.rc_sites.pbc

    def clean(self):        
        rc_sites = self.rc_sites.clean()
        rc_cell = self.rc_cell.clean()

        new = self.__class__(self.assignments, rc_sites, rc_cell)
        new.add_tags(self.get_tags())
        new.add_refs(self.get_refs())               
        return new

    @httk_typed_property(str)
    def formula(self):
        #TODO: Implement more efficient version if multiplicities are known
        return normalized_formula(self.uc.assignments.symbollists, self.uc.assignments.ratioslist, self.uc.uc_counts)

    #TODO: Add more advanced formula builders in a plugin instead, Structure.formulas. ...
    @property
    def cc_formula_parts(self):         
        symbols = self.assignments.symbols 
        ratios = self.assignments.ratios 
        counts = self.cc.uc_sites.counts

        formdict = {}
        for i in range(len(symbols)):
            symbol = symbols[i]
            if symbol in formdict:
                formdict[symbol] += ratios[i]*counts[i]
            else:
                formdict[symbol] = ratios[i]*counts[i]

        symbols = formdict.keys()        
        rearrange = sorted(range(len(symbols)), key=lambda k: symbols[k])
        formparts = [(symbols[i], formdict[symbols[i]]) for i in rearrange]
        return formparts

    @property
    def pc_formula_parts(self):         
        symbols = self.assignments.symbols 
        ratios = self.assignments.ratios 
        counts = self.pc.uc_sites.counts

        formdict = {}
        for i in range(len(symbols)):
            symbol = symbols[i]
            if symbol in formdict:
                formdict[symbol] += ratios[i]*counts[i]
            else:
                formdict[symbol] = ratios[i]*counts[i]

        symbols = formdict.keys()        
        rearrange = sorted(range(len(symbols)), key=lambda k: symbols[k])
        formparts = [(symbols[i], formdict[symbols[i]]) for i in rearrange]
        return formparts

    @property
    def uc_formula_parts(self):         
        symbols = self.assignments.symbols 
        ratios = self.assignments.ratios 
        counts = self.uc.uc_sites.counts

        formdict = {}
        for i in range(len(symbols)):
            symbol = symbols[i]
            if symbol in formdict:
                formdict[symbol] += ratios[i]*counts[i]
            else:
                formdict[symbol] = ratios[i]*counts[i]

        symbols = formdict.keys()        
        rearrange = sorted(range(len(symbols)), key=lambda k: symbols[k])
        formparts = [(symbols[i], formdict[symbols[i]]) for i in rearrange]
        return formparts
    
    @httk_typed_property([str])
    def uc_formula_symbols(self):
        parts = self.uc_formula_parts
        return [symbol for symbol, count in parts]

    @httk_typed_property([FracScalar])
    def uc_formula_counts(self):
        parts = self.uc_formula_parts
        return [count for symbol, count in parts]

    @property
    def formula_spaceseparated(self):
        parts = self.pc_formula_parts        
        formula = ''
        for symbol, count in parts:
            count = FracScalar.use(count).set_denominator(100).simplify()
            if count == 1:
                formula += symbol+" "
            elif count.denom == 1:
                formula += symbol+"%d " % (count,)
            else:
                formula += symbol+"%.2f " % (count,)
        return formula[:-1]

    @httk_typed_property(str)
    def anonymous_formula(self):
        return self.uc_sites.anonymous_formula

    @httk_typed_property([str])     
    def symbols(self):
        return self.assignments.symbols

    @httk_typed_property(str)
    def element_wyckoff_sequence(self):        
        if self.rc_sites.wyckoff_symbols is None:
            return None        
        symbols = []
        for a in self.assignments:
            if is_sequence(a):
                if len(a) == 1:
                    if a[0].ratio == 1:
                        symbols += [a[0].symbol]
                    else:
                        symbols += ["("+a[0].symbol + "%d.%02d" % (a[0].ratio.floor(), ((a[0].ratio-a[0].ratio.floor())*100).floor())+")"]
                else:
                    def checkratio(symbol, ratio):
                        if ratio == 1:
                            return symbol
                        else:
                            return "%s%d.%02d" % (symbol, ratio.floor(), ((ratio-ratio.floor())*100).floor())
                    symbols += ["("+"".join([checkratio(x.symbol, x.ratio) for x in a])+")"]
            else:
                if a.ratio == 1:
                    symbols += [a.symbol]
                else:
                    symbols += ["("+a.symbol + "%d.%02d" % (a.ratio.floor(), ((a.ratio-a.ratio.floor())*100).floor())+")"]
        
        data = {}
        idx = 0
        for i in range(len(self.rc_sites.counts)):
            for j in range(self.rc_sites.counts[i]):
                wsymb = self.rc_sites.wyckoff_symbols[idx]
                if wsymb == '&':
                    wsymb = 'zz'
                # Note the extra self.assignments[i].to_tuple() that makes sure we are not mixing non-equivalent sites
                # even if they are non-equivalent in something that isn't readily visible in the symbol (!)
                key = (wsymb, symbols[i], self.assignments[i].to_tuple())
                if key in data:
                    data[key] = (wsymb, data[key][1]+1, symbols[i])
                else:
                    data[key] = (wsymb, 1, symbols[i])
                idx += 1
        sortedcounts = sorted(data.values())
        symbol = ""
        for i in range(len(sortedcounts)):
            wsymb = sortedcounts[i][0]
            if wsymb == 'zz':
                wsymb = '&'            
            symbol += str(sortedcounts[i][1])+wsymb+sortedcounts[i][2]
        return symbol
                
    @httk_typed_property(str)
    def anonymous_wyckoff_sequence(self):
        return self.rc_sites.anonymous_wyckoff_sequence

    @httk_typed_property(str)
    def wyckoff_sequence(self):
        return self.rc_sites.wyckoff_sequence

    @httk_typed_property([str])
    def formula_symbols(self):
        symbols = []
        formula = normalized_formula_parts(self.assignments.symbollists, self.assignments.ratioslist, self.uc_sites.counts)
        for key in sorted(formula.iterkeys()):            
            if is_sequence(key):
                key = "".join([str(x[0])+str(("%.2f" % x[1])) for x in key])
            symbols += [key]
        return symbols

    @httk_typed_property([FracScalar])     
    def formula_counts(self):
        counts = []
        formula = normalized_formula_parts(self.assignments.symbollists, self.assignments.ratioslist, self.uc_sites.counts)
        for key in sorted(formula.iterkeys()):
            if is_sequence(formula[key]):
                totval = sum(formula[key])
            else:
                totval = formula[key]
            counts += [totval]
        return counts

    @httk_typed_property(int)
    def uc_nbr_atoms(self):
        return sum(self.uc_counts)

    #TODO: Create some kind of automatic setup for Tags and Refs rather than copying the below code everywhere.
    def _fill_codependent_data(self):
        self._tags = {}
        self._refs = []
        for x in self._codependent_callbacks:
            x(self)            

    def add_tag(self, tag, val):
        if self._tags is None:
            self._fill_codependent_data()
        new = StructureTag(self, tag, val)
        self._tags[tag] = new
        self._codependent_data += [new]

    def add_tags(self, tags):
        for tag in tags:
            if isinstance(tags, dict):
                tagdata = tags[tag]
            else:
                tagdata = tag
            if isinstance(tagdata, StructureTag):
                self.add_tag(tagdata.tag, tagdata.value)
            else:
                self.add_tag(tag, tagdata)

    def get_tags(self):
        if self._tags is None:
            self._fill_codependent_data()
        return self._tags

    def get_tag(self, tag):
        if self._tags is None:
            self._fill_codependent_data()
        return self._tags[tag]

    def get_refs(self):
        if self._refs is None:
            self._fill_codependent_data()
        return self._refs

    def add_ref(self, ref):        
        if self._refs is None:
            self._fill_codependent_data()
        if isinstance(ref, StructureRef):
            refobj = ref.reference
        else:
            refobj = Reference.use(ref)
        new = StructureRef(self, refobj)
        self._refs += [new]
        self._codependent_data += [new]

    def add_refs(self, refs):
        for ref in refs:
            self.add_ref(ref)

    def __str__(self):
        return "<httk Structure object:\n  "+str(self.rc_cell)+"\n  "+str(self.assignments)+"\n  "+str(self.rc_sites)+"\n  Tags:"+str([str(self.get_tags()[tag]) for tag in self.get_tags()])+"\n  Refs:"+str([str(ref) for ref in self.get_refs()])+"\n>" 


class StructureTag(HttkObject):                               

    @httk_typed_init({'structure': Structure, 'tag': str, 'value': str}, index=['structure', 'tag', ('tag', 'value'), ('structure', 'tag', 'value')], skip=['hexhash'])    
    def __init__(self, structure, tag, value):
        super(StructureTag, self).__init__()
        self.tag = tag
        self.structure = structure
        self.value = value

    def __str__(self):
        return "(Tag) "+self.tag+": "+self.value+""


class StructureRef(HttkObject):

    @httk_typed_init({'structure': Structure, 'reference': Reference}, index=['structure', 'reference'], skip=['hexhash'])        
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
    
