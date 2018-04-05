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


class ScalelessStructure(HttkObject):

    """
    A ScalelessStructure is the same as a Structre object, only that it does NOT carry information
    about the cell (no rc_cell or uc_cell).
    """
    
    #TODO: When httk internally handles symmetry replication, consider removing UnitcellSites from here    
    @httk_typed_init({'assignments': Assignments, 'rc_sites': RepresentativeSites},
                     index=['assignments', 'rc_sites'])    
    def __init__(self, assignments, rc_sites=None, uc_sites=None):
        """
        Private constructor, as per httk coding guidelines. Use Structure.create instead.
        """        
        super(ScalelessStructure, self).__init__()

        self.assignments = assignments
        self._rc_sites = rc_sites
        self._uc_sites = uc_sites
        
        self._tags = None
        self._refs = None
        self._rc_cells = None

        self._codependent_callbacks = []
        self._codependent_data = []
        self._codependent_info = [{'class': SlStructureCell, 'column': 'structure', 'add_method': 'add_rc_cells'},
                                  {'class': SlStructureTag, 'column': 'structure', 'add_method': 'add_tags'},
                                  {'class': SlStructureRef, 'column': 'structure', 'add_method': 'add_refs'}]

        self._rc_cell = None
        self._uc_cell = None

    @classmethod
    def create(cls,
               structure=None,

               uc_cellshape=None, uc_basis=None, uc_lengths=None, 
               uc_angles=None, uc_niggli_matrix=None, uc_metric=None, 
               uc_a=None, uc_b=None, uc_c=None, 
               uc_alpha=None, uc_beta=None, uc_gamma=None,
               uc_sites=None, 
               uc_reduced_coordgroups=None, 
               uc_reduced_coords=None, 
               uc_reduced_occupationscoords=None,  
               uc_occupancies=None, uc_counts=None,

               rc_cellshape=None, rc_basis=None, rc_lengths=None, 
               rc_angles=None, rc_niggli_matrix=None, rc_metric=None, 
               rc_a=None, rc_b=None, rc_c=None, 
               rc_alpha=None, rc_beta=None, rc_gamma=None,
               rc_sites=None, 
               rc_reduced_coordgroups=None, 
               rc_reduced_coords=None, 
               rc_reduced_occupationscoords=None,
               rc_occupancies=None, rc_counts=None, 
               wyckoff_symbols=None,
               spacegroup=None, hall_symbol=None, spacegroupnumber=None, setting=None,
               
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
       
        if isinstance(structure, ScalelessStructure):
            rc_sites = None
            uc_sites = None
            if structure.has_rc_repr:
                rc_sites = structure.rc_sites
            if structure.has_uc_repr:
                uc_sites = structure.uc_sites
            return cls(structure.assignments, rc_sites=rc_sites, uc_sites=uc_sites)
        
        if isinstance(spacegroup, Spacegroup):
            hall_symbol = spacegroup.hall_symbol
        else:
            try:
                spacegroupobj = Spacegroup.create(spacegroup=spacegroup, hall_symbol=hall_symbol, spacegroupnumber=spacegroupnumber, setting=setting) 
                hall_symbol = spacegroupobj.hall_symbol
            except Exception as spacegroup_exception:
                spacegroupobj = None                
                hall_symbol = None

        if isinstance(uc_sites, UnitcellSites):
            uc_sites = uc_sites
        if isinstance(uc_sites, Sites):
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

#                 if isinstance(uc_cellshape,CellShape):
#                     uc_cellshapeobj = uc_cellshape
#                 else:                        
#                     try:
#                         uc_cellshapeobj = CellShape.create(cellshape=uc_cellshape, basis=uc_basis, metric=uc_metric, 
#                                               niggli_matrix=uc_niggli_matrix, 
#                                               a=uc_a, b=uc_b, c=uc_c, 
#                                               alpha=uc_alpha, beta=uc_beta, gamma=uc_gamma,
#                                               lengths = uc_lengths, angles=uc_angles)
#                                                     
#                     except Exception:
#                         uc_cellshapeobj = None

                try:
                    uc_sites = UnitcellSites.create(reduced_coordgroups=uc_reduced_coordgroups, 
                                                    reduced_coords=uc_reduced_coords, 
                                                    counts=uc_counts, 
                                                    periodicity=periodicity, occupancies=uc_occupancies)
                except Exception:
                    uc_sites = None
            
            else:
                uc_sites = None

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
                
#                 if isinstance(rc_cellshape,CellShape):
#                     rc_cellshapeobj = rc_cellshape
#                 else:
#                     try:                        
#                         rc_cellshapeobj = CellShape.create(cellshape=rc_cellshape, basis=rc_basis, metric=rc_metric, 
#                                               niggli_matrix=rc_niggli_matrix, 
#                                               a=rc_a, b=rc_b, c=rc_c, 
#                                               alpha=rc_alpha, beta=rc_beta, gamma=rc_gamma,
#                                               lengths = rc_lengths, angles=rc_angles)
#                     except Exception:
#                         rc_cellshapeobj = None
                                                                    
                try:
                    rc_sites = RepresentativeSites.create(reduced_coordgroups=rc_reduced_coordgroups, 
                                                          reduced_coords=rc_reduced_coords, 
                                                          counts=rc_counts,
                                                          hall_symbol=hall_symbol, periodicity=periodicity, wyckoff_symbols=wyckoff_symbols,
                                                          occupancies=rc_occupancies)
                except Exception:
                    rc_sites = None
            else:
                rc_sites = None
            
        if rc_sites is None and uc_sites is None:
            raise Exception("Structure.create: neither representative, nor primcell, sites specification valid.")

        if assignments is not None:
            if isinstance(assignments, Assignments):
                assignments = assignments
            else:
                assignments = Assignments.create(assignments=assignments)

        if uc_sites is None and hall_symbol is None:
            raise Exception("Structure.create: cannot create structure from only representative sites with no spacegroup information. Error was:"+str(spacegroup_exception))

        new = cls(assignments, rc_sites, uc_sites)
        if tags is not None:
            new.add_tags(tags)
        if refs is not None:
            new.add_refs(refs)               
        return new

    @httk_typed_property(str)
    def hall_symbol(self):
        return self.rc_sites.hall_symbol

    @httk_typed_property(UnitcellSites)
    def uc_sites(self):
        if self._uc_sites is None:
            self._uc_sites, cell = coordgroups_reduced_rc_to_unitcellsites(self.rc_sites.reduced_coordgroups, self.rc_sites.cellshape.basis, self.hall_symbol)
        return self._uc_sites
            
    @property
    def rc_sites(self):
        if self._rc_sites is None:
            newstructure = structure_reduced_uc_to_representative(self)
            self._rc_sites = newstructure.rc_sites
        return self._rc_sites

    def find_symetry(self):
        """
        Make sure this structure has a representative cell representation. I.e., run an algorithm to find symmetries.

        (This method exists as a user friendly name for simply asking for the property self.rc_sites, which does the same.
        i.e. finds the crystal symmetries if this representation is not yet known.)
        """
        self.rc_sites

    def fill_cell(self):
        """
        Make sure this structure has a unitcell representation. I.e., run an algorithm to copy the representative
        atoms throughout the unitcell. 
        
        (This method exists as a user friendly name for simply asking for the property self.uc_sites, which does the same;
        i.e. fills the cell if this representation is not yet known.)
        """
        self.uc_sites
        
    @property
    def has_rc_repr(self):
        """
        Returns True if the structure already contains the representative coordinates + spacegroup, and thus can be queried for this data
        without launching an expensive symmetry finder operation. 
        """
        return self._rc_sites is not None 
           
    @property
    def has_uc_repr(self):
        """
        Returns True if the structure contains the primcell coordinate representation, and thus can be queried for this data
        without launching a somewhat expensive cell filling operation. 
        """
        return self._uc_sites is not None

    @property
    def uc_reduced_coordgroups(self):
        return self.uc_sites.reduced_coordgroups

    @property
    def rc_reduced_coordgroups(self):
        return self.rc_sites.reduced_coordgroups

    @httk_typed_property([int])
    def rc_counts(self):
        return self.rc_sites.counts

    @httk_typed_property(int)
    def rc_nbr_atoms(self):
        return sum(self.rc_counts)

    @httk_typed_property([int])
    def uc_counts(self):
        return self.uc_sites.counts

    @httk_typed_property(int)
    def uc_nbr_atoms(self):
        return sum(self.uc_counts)

    @property
    def rc_reduced_coords(self):
        return self.rc_sites.reduced_coords

    @property
    def uc_reduced_coords(self):
        return self.uc_sites.reduced_coords

    @httk_typed_property(int)
    def number_of_elements(self):
        seen = {}
        for symbol in self.formula_symbols:
            seen[symbol] = True
        return len(seen)

    @httk_typed_property(str)
    def formula(self):
        return normalized_formula(self.assignments.symbollists, self.assignments.ratioslist, self.uc_sites.counts)

    @property
    def uc_formula_parts(self):         
        symbols = self.assignments.symbols 
        ratios = self.assignments.ratios 
        counts = self.uc_sites.counts

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

    @httk_typed_property(str)
    def uc_formula(self):
        parts = self.uc_formula_parts        
        formula = ''
        for symbol, count in parts:            
            count = FracScalar.use(count).set_denominator(100).simplify()
            if count == 1:
                formula += symbol
            elif count.denom == 1:
                formula += symbol+"%d" % (count,)
            else:
                formula += symbol+"%.2f" % (count,)
        return formula

    @httk_typed_property([str])
    def uc_formula_symbols(self):
        parts = self.uc_formula_parts
        return [symbol for symbol, count in parts]

    @httk_typed_property([FracScalar])
    def uc_formula_counts(self):
        parts = self.uc_formula_parts
        return [count for symbol, count in parts]

    @httk_typed_property(str)
    def rc_formula(self):
        symbols = self.assignments.symbols 
        ratios = self.assignments.ratios 
        counts = self.rc_sites.counts
        formula = ""

        rearrange = sorted(range(len(symbols)), key=lambda k: symbols[k])
        
        for i in rearrange:            
            count = FracScalar.use((ratios[i]*counts[i])).set_denominator(100).simplify()
            if count == 1:
                formula += symbols[i]
            elif count.denom == 1:
                formula += symbols[i]+"%d" % (counts[i]*ratios[i],)
            else:
                formula += symbols[i]+"%.2f" % (counts[i]*ratios[i],)
            formula += "".join([symbols[i]])
        return formula

    @httk_typed_property(str)
    def anonymous_formula(self):
        return self.uc_sites.anonymous_formula

    @httk_typed_property([str])     
    def symbols(self):
        return self.assignments.symbols

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

    @property
    def spacegroup_number_and_setting(self):
        return self.spacegroupobj.spacegroup_number_and_setting
    
    #@property
    #def rc_symbols(self):
    #    return coordgroups_and_assignments_to_symbols(self.rc_sites.reduced_coordgroups, self.assignments)

    #@property
    #def uc_symbols(self):
    #    return coordgroups_and_assignments_to_symbols(self.uc_sites.reduced_coordgroups, self.assignments)

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

    @property
    def spacegroupobj(self):
        return Spacegroup.create(hall_symbol=self.hall_symbol)

    @httk_typed_property(int)
    def spacegroup_number(self):
        return self.spacegroupobj.spacegroup_number_and_setting[0]

    def _fill_codependent_data(self):
        self._tags = {}
        self._refs = []
        self._rc_cells = []
        for x in self._codependent_callbacks:
            x(self)            

    def add_tag(self, tag, val):
        if self._tags is None:
            self._fill_codependent_data()
        new = SlStructureTag(self, tag, val)
        self._tags[tag] = new
        self._codependent_data += [new]

    def add_tags(self, tags):
        for tag in tags:
            if isinstance(tags, dict):
                tagdata = tags[tag]
            else:
                tagdata = tag
            if isinstance(tagdata, SlStructureTag):
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
        if isinstance(ref, SlStructureRef):
            refobj = ref.reference
        else:
            refobj = Reference.use(ref)
        new = SlStructureRef(self, refobj)
        self._refs += [new]
        self._codependent_data += [new]

    def add_refs(self, refs):
        for ref in refs:
            self.add_ref(ref)
            
    def get_rc_cells(self):
        if self._rc_cells is None:
            self._fill_codependent_data()
        return self._rc_cells

    def add_rc_cell(self, cell):        
        if self._rc_cells is None:
            self._fill_codependent_data()
        if isinstance(cell, SlStructureCell):
            cell = cell.cell
        new = SlStructureCell(self, cell)
        self._rc_cells += [new]
        self._codependent_data += [new]

    def add_rc_cells(self, cells):
        for cell in cells:
            self.add_rc_cell(cell)

    @httk_typed_property(bool)
    def extended(self):
        return self.assignments.extended

    @httk_typed_property([str])
    def extensions(self):
        return self.assignments.extensions

    def clean(self):        
        rc_sites = self.rc_sites.clean()
        uc_sites = self.uc_sites.clean()

        new = self.__class__(self.assignments, rc_sites, uc_sites)
        new.add_tags(self.get_tags())
        new.add_refs(self.get_refs())               
        new.add_rc_scales(self.get_rc_scales())
        return new

    def tidy(self):
        return structure_tidy(self).clean()
        #tidyrcsites, rescale = self.rc_sites.tidy()
        #newscale = (self.rc_scale * rescale).limit_resolution(10000)
        #return self.__class__(self.assignments, tidyrcsites, rc_scale=newscale)

    # Make some code-completion tools happy and provide sane error messages when plugin has not been loaded
    # (Plugins does not *need* placeholders, they are just here to be helpful.)
    io = HttkPluginPlaceholder("import httk.atomistic.io")
    vis = HttkPluginPlaceholder("import httk.atomistic.vis")


class SlStructureTag(HttkObject):                               

    @httk_typed_init({'structure': ScalelessStructure, 'tag': str, 'value': str}, index=['structure', 'tag', 'value'], skip=['hexhash'])    
    def __init__(self, structure, tag, value):
        super(SlStructureTag, self).__init__()
        self.tag = tag
        self.structure = structure
        self.value = value

    def __str__(self):
        return "(Tag) "+self.tag+": "+self.value+""


class SlStructureRef(HttkObject):

    @httk_typed_init({'structure': ScalelessStructure, 'reference': Reference}, index=['structure', 'reference'], skip=['hexhash'])        
    def __init__(self, structure, reference):
        super(SlStructureRef, self).__init__()
        self.structure = structure
        self.reference = reference

    def __str__(self):
        return str(self.reference)


class SlStructureCell(HttkObject):

    @httk_typed_init({'structure': ScalelessStructure, 'cell': Cell}, index=['structure', 'cell'], skip=['hexhash'])
    def __init__(self, structure, cell):
        super(SlStructureCell, self).__init__()
        self.structure = structure
        self.cell = cell

    @classmethod
    def create(cls, cell, structure=None):
        if isinstance(cell, SlStructureCell):
            return cell

        return cls(structure, cell)

    def __str__(self):
        return str(self.reference)


def main():
    print "Test"

#     def httk_typed_property(t):
#         def wrapfactory(func):
#             func.property_type = lambda: t
#             return property(func)
#         return wrapfactory
# 
#     def httk_typed_property_delayed(t):
#         def wrapfactory(func):
#             func.property_type = t
#             return property(func)
#         return wrapfactory
# 
#     def check_returntype(obj,propname):
#         for obj in [obj]+obj.__class__.mro():
#             if propname in obj.__dict__:
#                 return obj.__dict__[propname].fget.property_type()
#         raise AttributeError

#     class Horse:
#         pass
# 
#     class Gurk(object):
#         @httk_typed_property(Horse)
#         def number_seven(self):        
#             return 7
# 
#     test = Gurk()
#     print test.number_seven
#     print httk_typed_property_resolve(test,'number_seven')()
    
    #from httk.core.fracvector import FracVector

    #class StructureGurkPlugin(object):

    #    name = 'gurk'
                
    #    def __init__(self, struct):
    #        self.struct = struct

    #    def print_gurk(self):
    #        print "HERE:",self.struct

    #Structure.add_plugin(StructureGurkPlugin)
    
    #coords = FracVector.create([[2,3,5],[3,5,4],[4,6,7]])
    #cell = FracVector.create([[1,1,0],[1,0,1],[0,1,1]])
    #assignments = [2,5]
    #counts = [2,1]
    #a = Structure.create_from_counts_coords(cell, assignments, counts, coords)
    
    #print(a)
    #a.gurk.print_gurk()    

    #easya = a.to_EasyStructure()
    #print(easya)

        
if __name__ == "__main__":
    main()
    
    
