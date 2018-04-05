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
from structure import Structure, StructureTag, StructureRef


class UnitcellStructure(HttkObject):

    """
    FullSitesStructure essentially just wraps Structure, and provides a strict subset of the functionality therein. This is needed, 
    because in interaction with, e.g., databases, we sometimes need to restrict the available fields to those properties
    accessible via this object.
    
    """

    @httk_typed_init({'assignments': Assignments, 'uc_sites': UnitcellSites, 'uc_cell': Cell},
                     index=['assignments', 'uc_sites', 'uc_cell'])    
    def __init__(self, cell=None, assignments=None, rc_sites=None, uc_sites=None, struct=None, uc_cell=None):
        """
        Private constructor, as per httk coding guidelines. Use Structure.create instead.
        """
        if rc_sites is not None:
            raise Exception("FullSitesStructure.__init__: Trying to create a FullSitesStructure with a non-None unique_sites.")

        if struct is not None:
            self._struct = struct
        else:
            self._struct = Structure(assignments, rc_sites=None, uc_sites=uc_sites, rc_cell=None, uc_cell=uc_cell)

        self.assignments = self._struct.assignments

        self._tags = None
        self._refs = None

        self._codependent_callbacks = []
        self._codependent_data = []
        self._codependent_info = [{'class': UCStructureTag, 'column': 'structure', 'add_method': 'add_tags'},
                                  {'class': UCStructureRef, 'column': 'structure', 'add_method': 'add_refs'}]

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
               uc_scale=None, uc_scaling=None, uc_volume=None, 
                   
               assignments=None, 
               
               periodicity=None, nonperiodic_vecs=None, 
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
        allow for painless change between the various structure-type objects.
      
        Note: see help(Structure) for parameter naming conventions, i.e., what type of object is expected given a parameter name.      
           
        Input parameters:

           - ONE OF: 'cell'; 'basis', 'length_and_angles'; 'niggli_matrix'; 'metric'; all of: a,b,c, alpha, beta, gamma. 
             (cell requires a Cell object or a very specific format, so unless you know what you are doing, use one of the others.)

           - ONE OF: 'assignments', 'atomic_numbers', 'occupations'
             (assignments requires an Assignments object or a sequence.), occupations repeats similar site assignments as needed
           
           - ONE OF: 'uc_sites', 'uc_coords' (IF uc_occupations OR uc_counts are also given), or
             'uc_B_C', where B=reduced or cartesian, C=coordgroups, coords, or occupationscoords

             Notes: 

                  - occupationscoords may differ by coords by *order*, since giving occupations as, e.g., ['H','O','H'] does not necessarily
                    have the same order of the coordinates as the format of counts+coords as (2,1), ['H','O'], and we cannot just re-order
                    the coordinates at creation time (since presevation of the order is sometimes important.)

                  - uc_sites requires a Sites object or a python list on a very specific format, (so unless you know what you are doing, 
                    use one of the others.)
                           
           - ONE OF: 'spacegroup' or 'hall_symbol', OR NEITHER (in which case the spacegroup is regarded as unknown)                

           - ONE OF: scale or volume: 
                scale = multiply the basis vectors with this scaling factor, 
                volume = rescale the cell into this volume (overrides 'scale' if both are given)

           - ONE OF periodicity or nonperiodic_vecs
           
        """          
        if isinstance(structure, Structure):
            new = cls(struct=structure)
            new.add_tags(structure.get_tags())
            new.add_refs(structure.get_refs())
            return new
        
        args = locals()  
        del(args['cls'])
        struct = Structure.create(**args)
        return cls(struct=struct)

    @property
    def uc_sites(self):
        return self._struct.uc_sites

    @property
    def uc_cell(self):
        return self._struct.uc_cell
            
    @property
    def has_rc_repr(self):
        """
        Returns True if the structure already contains the representative coordinates + spacegroup, and thus can be queried for this data
        without launching an expensive symmetry finder operation. 
        """
        return False
           
    @property
    def has_uc_repr(self):
        """
        Returns True if the structure contains the primcell coordinate representation, and thus can be queried for this data
        without launching a somewhat expensive cell filling operation. 
        """
        return True
    
    @property
    def uc_reduced_coordgroups(self):
        return self._struct.uc_reduced_coordgroups

    @property
    def uc_cartesian_coordgroups(self):
        return self._struct.uc_cartesian_coordgroups

    @property
    def uc_counts(self):
        return self._struct.uc_counts

    @property
    def uc_nbr_atoms(self):
        return self._struct.uc_nbr_atoms

    @property
    def uc_reduced_coords(self):
        return self._struct.uc_reduced_coords

    @property
    def uc_cartesian_coords(self):
        return self._struct.uc_cartesian_coords

    @httk_typed_property(str)
    def formula(self):
        return self._struct.formula

    @httk_typed_property(str)
    def anonymous_formula(self):
        return self._struct.anonymous_formula

    @property
    def uc_a(self):
        return self._struct.uc_a

    @property
    def uc_b(self):
        return self._struct.uc_b

    @property
    def uc_c(self):
        return self._struct.uc_c

    @property
    def uc_alpha(self):
        return self._struct.uc_alpha

    @property
    def uc_beta(self):
        return self._struct.uc_beta

    @property
    def uc_gamma(self):
        return self._struct.uc_gamma

    @property
    def uc_cell_orientation(self):
        return self._struct.cell_orientation

    @property
    def uc_basis(self):
        return self._struct.uc_basis

    @property
    def uc_volume(self):
        return self._struct.uc_volume

    @property
    def uc_symbols(self):
        return self._struct.uc_symbols

    @property
    def uc_reduced_occupationscoords(self):
        return self._struct.uc_reduced_occupationscoords

    @property
    def uc_cartesian_occupationscoords(self):
        return self._struct.uc_cartesian_occupationscoords

    @property
    def uc_occupancies(self):
        return self._struct.uc_occupancies

    def get_normalized(self):
        newstruct = self._struct.get_normalized()
        return self.__class__(struct=newstruct)

    def _fill_codependent_data(self):
        self._tags = {}
        self._refs = []
        for x in self._codependent_callbacks:
            x(self)            

    def add_tag(self, tag, val):
        if self._tags is None:
            self._fill_codependent_data()
        new = UCStructureTag(self, tag, val)
        self._tags[tag] = new
        self._codependent_data += [new]

    def add_tags(self, tags):
        for tag in tags:
            if isinstance(tags, dict):
                tagdata = tags[tag]
            else:
                tagdata = tag
            if isinstance(tagdata, UCStructureTag):
                self.add_tag(tagdata.tag, tagdata.value)
            elif isinstance(tagdata, StructureTag):
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
        if isinstance(ref, UCStructureRef):
            refobj = ref.reference
        elif isinstance(ref, StructureRef):
            refobj = ref.reference
        else:
            refobj = Reference.use(ref)
        new = UCStructureRef(self, refobj)
        self._refs += [new]
        self._codependent_data += [new]

    def add_refs(self, refs):
        for ref in refs:
            self.add_ref(ref)

    @httk_typed_property(bool)
    def extended(self):
        return self._struct.extended

    @httk_typed_property([str])
    def extensions(self):
        return self._struct.extensions

    @httk_typed_property([str])
    def formula_symbols(self):
        return self._struct.formula_symbols
    
    @property
    def uc_formula(self):
        return self._struct.uc_formula

    @property
    def uc_formula_symbols(self):
        return self._struct.uc_formula_symbols
     
    @property
    def uc_formula_counts(self):
        return self._struct.uc_formula_counts
        

class UCStructureTag(HttkObject):                               

    @httk_typed_init({'structure': UnitcellStructure, 'tag': str, 'value': str}, index=['structure', 'tag', 'value'], skip=['hexhash'])    
    def __init__(self, structure, tag, value):
        self.tag = tag
        self.structure = structure
        self.value = value

    def __str__(self):
        return "(Tag) "+self.tag+": "+self.value+""


class UCStructureRef(HttkObject):

    @httk_typed_init({'structure': UnitcellStructure, 'reference': Reference}, index=['structure', 'reference'], skip=['hexhash'])        
    def __init__(self, structure, reference):
        self.structure = structure
        self.reference = reference

    def __str__(self):
        return str(self.reference)


