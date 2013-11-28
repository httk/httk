# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2013 Rickard Armiento
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

from prototype import Prototype
from htdata import spacegroups
from fracvector import FracVector
from structureutils import *
from httk.crypto import tuple_to_hexhash
from httk.utils import is_unary, flatten
import htdata
      
class Structure(object):
    """
    Periodic or Non-periodic arrangement of atoms in space, only tracking the non-equivalent atom + the spacegroup information.
    
    The httk classes divide structural information into three parts, and Structure is the glue that keeps them together
       - A prototype, specifying the geometrical information (where are the atoms located in the cell, and which atoms are the same)
       - An assignment, specifying the type (or types for disordered structures) of each atom
       - A volume, specifying a cell volume
    """   
    def __init__(self, sgprototype, multi_assignments, volume, extended=False, extensions=None, tags=None, refs=None):
        """
        (Private constructor, use Structure.create instead)

        sgprototype:    Prototype object for the geometrical information of this structure ('sg' for spacegroup to emphasis difference to p1prototype)
        multi_assignments: a list with one item per equivalent set of atoms, items can be a list of atoms for disordered-extended structures. (Hence 'multi')
        tags:          tag-formed data (a dict of strings) describing the structure
        extended:      False, unless this is not an ordinary, ordered, structure. (In which case 'extensions' specify what extension/s apply)
        extensions:    A list of extension identifiers used for this structure (e.g., 'disordered', 'isotopes', etc.) 
        refs:          Literary references associated with the structure
        """
        self.multi_assignments = multi_assignments
        self.sgprototype = sgprototype
        self.refs = refs

        self.volume = volume
        self.refs = refs
        self._p1structure = None
        if tags == None:
            self.tags = {}
        else:
            self.tags = tags
        self.extended = extended
        if extensions == None:
            self.extensions = []
        else:
            self.extensions = extensions
              
        self.sgassignments = [a[0][0] for a in multi_assignments]

        self.sgoccupancies = [self.sgassignments[y] for y in range(len(self.sgprototype.coordgroups)) for x in self.sgprototype.coordgroups[y] ]

        self._hexhash = None
        self._scaled_cell = None
        
        if sgprototype.hall_symbol == 'P 1':
            self._p1structure = self
        else:
            self._p1structure = None            
            
    @classmethod
    def use(cls,old):
        if isinstance(old,Structure):
            return old
        else:
            try:
                return old.to_Structure()
            except Exception as e:    
                raise Exception("Structure.use: unknown input:"+str(e)+" object was:"+str(old))

    @classmethod
    def create(cls, cell=None, niggli_matrix=None, orientation = 1, a=None, b=None, c=None, lengths=None, alpha=None, beta=None, gamma=None, angles=None,
                    coordgroups=None, coords=None, cart_coordgroups=None, cart_coords=None, counts = None, 
                    assignments = None, occupancies = None,
                    scale = None, volume = None, 
                    individual_data=None, tags=None, hall_symbol=None,
                    spacegroup='P1', refs=None, periodicity=0, normalize=True):
        """
        Create a new structure from any sensible subset of the following parameters
        
        cell:          cell vectors (e.g., FracVector 3x3 matrix with cell vectors as rows)
        niggli_matrix: cell given via the niggli_matrix
        orientation:   +1 for right handed cell, -1 for left handed cell
        a, b, c:       separate cell vectors
        lengths:       list of length of cell vectors
        angles:        list of the cell angles
        alpha, beta, gamma: cell angles
        coords:        list of coordinate triples in reduced cordinates (must also specify counts)
        coordgroups:   list of lists of reduced coordinates where each group of coordinates is one "slot" in the prototype
        cart_coords:   list of coordinate triples in cartesian coordinates
        cart_coordgroups: list of lists of cartesian coordinates where each group of coordinates is one "slot" in the prototype
        counts:        if coords specified, divides the coord list into "slots" in the prototype according to this list, e.g.
                           [5,7,3] means the first 5 coordinates are for slot1, the next 7 for slot2 and the last 3 for slot3.
        scale:         multiply the cell vector with this factor
        periodicity:   0 for a fully periodic structure, 111: non-periodic structure; 001, 010, 011, 100, 101 non-periodic along (xyz) axis.
        spacegroup:    a hall_symbol, spacegroup number or similar designation of the spacegroup.
        individual_data: a list of the same structure as coordgroups, with an entry of optional data type of each atom
        normalize:     set to False to not "mess" with the structue. Otherwise coordinates are sorted, etc., for a cheap effort to normalize structures
                       by sorting coordinates, etc.
        """

        if assignments == None and occupancies == None:
            raise Exception("Structure.create: must give one of assignments and occupancies.")

        if assignments == None: 
            if coordgroups == None:
                coordgroups, assignments = coords_and_occupancies_to_coordgroups_and_assignments(coords, occupancies)
            else:
                raise Exception("Structure.create: unsupported input: coordgroups + occupancies. Need coords + occupations.")

        if occupancies == None and coords != None:
            if counts == None:
                raise Exception("Structure.create: if giving coords but not occupancies, counts must be provided.")
        elif occupancies == None and cart_coords != None:
            if counts == None:
                raise Exception("Structure.create: if giving cart_coords but not occupancies, counts must be provided.")            
        
        if coordgroups == None:
            if coords != None:
                coords = FracVector.use(coords)
                coordgroups = coords_to_coordgroups(coords, counts)
            elif cart_coordgroups != None:
                coordgroups = cartesian_to_reduced(cell,cart_coordgroups)
            elif cart_coords != None:
                cart_coordgroups = coords_to_coordgroups(cart_coords, counts)
                coordgroups = cartesian_to_reduced(cell,cart_coordgroups)
        coordgroups = FracVector.use(coordgroups).simplify()

        if cell == None:
            if niggli_matrix != None:
                niggli_matrix = FracVector.use(niggli_matrix)
                cell = FracVector.use(niggli_to_cell(niggli_matrix,orientation=orientation))
            elif lengths != None and angles != None:
                niggli_matrix = lengths_angles_to_niggli(lengths,angles)
                niggli_matrix = FracVector.use(niggli_matrix)
                cell = FracVector.use(niggli_to_cell(niggli_matrix,orientation=orientation))
            elif not (a==None or b==None or c==None or alpha==None or beta==None or gamma==None):
                niggli_matrix = lengths_angles_to_niggli([a,b,c],[alpha,beta,gamma])
                niggli_matrix = FracVector.use(niggli_matrix)
                cell = FracVector.use(niggli_to_cell(niggli_matrix,orientation=orientation))                
        cell = FracVector.use(cell).simplify()

        if volume == None and scale != None:
            volume = cell_scale_to_vol(cell,scale)

        if volume == None:
            volume = float(abs(cell_determinant(cell)))

        volume = FracVector.use(volume).simplify()

        extensions = set()
        for assignment in assignments:
            if not is_unary(assignment):
                if len(assignment) > 1 or abs(float(assignment[0][1])-1.0) > 1e-6:
                    extended = True
                    extensions.add('disordered')
                    break
        else:
            extended = False

        multi_assignments = tuple()       
        for assignment in assignments:
            if not is_unary(assignment):
                newsubassignments = tuple()
                for subassignment in assignment:
                    if 'disordered' in extensions:
                            newsubassignments += ((periodictable.atomic_number(subassignment[0]),FracVector.use(subassignment[1])),)
                    else:
                        newsubassignments += ((periodictable.atomic_number(subassignment[0]),FracVector(1,1)),)
            else:
                newsubassignments = ((periodictable.atomic_number(assignment),FracVector(1,1)),)
            multi_assignments += (newsubassignments,)

        if hall_symbol == None:
            hall_symbol = htdata.spacegroups.spacegroup_get_hall(spacegroup)

        # normalize structure
        if normalize:
            counts = [len(x) for x in coordgroups]
            order = sorted(range(len(counts)), key = lambda x: (counts[x],multi_assignments[x]))
            coordgroups = coordgroups[order]
            multi_assignments = [ multi_assignments[i] for i in order]
            if individual_data != None and len(individual_data) > 0:
                individual_data = [ individual_data[i] for i in order]
            else:
                individual_data = None
    
        prototype = Prototype.create(cell=cell, niggli_matrix=niggli_matrix, orientation = orientation, 
                    a=a, b=b, c=c, lengths=lengths, alpha=alpha, beta=beta, gamma=gamma, angles=angles,
                    coordgroups=coordgroups, coords=coords, cart_coords=cart_coords, 
                    counts = counts, spacegroup=spacegroup, hall_symbol=hall_symbol, individual_data = individual_data, normalize=normalize)
        
        if tags == None:
            tags = {}

        if volume == None and scale != None:
            volume = cell_scale_to_vol(cell,scale)

        if volume == None:
            volume = float(abs(cell_determinant(cell)))

        volume = FracVector.use(volume)

        struct = Structure(prototype, multi_assignments, volume, extended=extended, extensions=extensions, tags=tags, refs=refs)
        
        if hall_symbol == 'P 1':
            struct._p1structure = struct

        return struct

    def set_p1structure(self,p1structure):
        """
        To be used during creation of a structure object if extraction from source material already provides a p1 version of the structure.
        (TODO: Remove the need for this method by instead implementing Structure.p1structure) 
        """
        p1structure._p1structure = p1structure
        self._p1structure = p1structure

    @property
    def p1structure(self):
        """
        Return a version of the structure with symmetry information removed, i.e., space group = P1, and all equivalent atoms in the cell present
        """
        if self._p1structure == None:
            #raise Exception("Structure.p1structure: Structure to p1structure not implemented yet, sorry")
            #import traceback
            #for line in traceback.format_stack():
            #    print line.strip()
            sys.stderr.write('WARNING: Structure.p1structure called, currently implemented by using an external program / library. This should be fixed.\n')
            self._p1structure = structure_to_p1structure(self)
        return self._p1structure

    def __copy__(self):
        return Structure(self.spacegroup, self.individual_data, self.nonequiv.copy(),self.refs)
    
    def __rep__(self):
        return "<Structure: "+str(self.nonequiv.cell)+">"

    def to_tuple(self):
        return (self.sgprototype.to_tuple(), self.volume.to_tuple(), self.multi_assignments)
    
    def __hash__(self):
        return self.to_tuple().__hash__()

    def __eq__(self,other):
        if other == None:
            return False
        else:
            if self.cell == other.cell and self.coordgroups == other.coordgroups and self.scale == other.scale and self.assignments == other.assignments and self.spacegroup == other.spacegroup:
                return True
            return False
        
    def __neq__(self,other):
        if other == None:
            return True
        else:
            return not self.__eq__(other)
        
    @property
    def hexhash(self):
        if self._hexhash == None:
            self._hexhash = tuple_to_hexhash(self.to_tuple())
        return self._hexhash

    def round(self,cell_resolution=10**8,coord_resolution=10**8):
        newprototype = self.sgprototype.round(cell_resolution=10**8,coord_resolution=10**8)
        
        return Structure(newprototype, self.multi_assignments, self.volume, extended=self.extended, extensions=self.extensions, tags=self.tags, refs=self.refs)

    def tidy(self):
        c2 = self.round()
        return c2

    # Convinience methods. Many of these just re-directs to the prototype object, but that saves a lot of writing :)

    @property
    def cell(self):
        return self.sgprototype.cell

    # It is highly recommended to use the p1* and sg* methods instead of accessing the prototype directly, because 
    # it makes it clear whether you work with the full set (p1) of atoms or just the equivalent atoms (sg).

    @property
    def p1coords(self):
        return self._p1structure.sgprototype.coords

    @property
    def p1coordgroups(self):
        return self._p1structure.sgprototype.coordgroups
    
    @property
    def p1counts(self):
        return self._p1structure.sgprototype.counts
    
    @property
    def p1assignments(self):
        return self._p1structure.sgassignments

    @property
    def p1occupancies(self):
        return self._p1structure.sgoccupancies

    @property
    def sgcoords(self):
        return self.sgprototype.coords

    @property
    def sgcoordgroups(self):
        return self.sgprototype.coordgroups

    @property
    def sgcounts(self):
        return self.sgprototype.counts

    #@property
    #def sgassignments(self):
    #    return self.sgassignments

    @property
    def hall_symbol(self):
        return self.sgprototype.hall_symbol

    @property
    def spacegroup_number(self):
        return self.sgprototype.spacegroup_number

    @property
    def spacegroup_number_and_setting(self):
        return self.sgprototype.spacegroup_number_and_setting

    @property
    def mh_symbol(self):
        return self.sgprototype.mh_symbol

    @property
    def element_count(self):
        elements = set()
        for e in self.multi_assignments:
            for g in e:
                elements.add(g[0])
        return len(elements)

    @property
    def N(self):
        return self.p1structure.sgprototype.N

    @property
    def formula(self):
        return normalized_formula(self.p1structure)

    @property
    def normalized_formula_parts(self):
        return normalized_formula_parts(self.p1structure.multi_assignments, self.p1structure.sgprototype.counts)

    @property
    def abstract_formula(self):
        return abstract_formula(self.p1structure)
    
    @property
    def prototype_formula(self):
        return self.sgprototype.prototype_formula()

    @property
    def periodicity(self):
        return self.sgprototype.periodicity


    @property
    def scaled_cell(self):
        if self._scaled_cell == None:
            self._scaled_cell = self.cell*((self.volume.to_float())**(1.0/3.0))
        return self._scaled_cell
    
    @property
    def scale(self):
        """
        Return the floating point scale that the present prototype cell must be multiplied with to 
        make the total volume be the correct volume.
        """
        cell = self.sgprototype.cell
        vol = abs(cell.det())
        return ((self.volume/vol).to_floats())**(1.0/3.0)    
    
    @property
    def a(self):
        return sqrt(self.scaled_cell[0].lengthsqr())
    
    @property
    def b(self):
        return sqrt(self.scaled_cell[1].lengthsqr())

    @property
    def c(self):
        return sqrt(self.scaled_cell[2].lengthsqr())
    
    @property
    def alpha(self):
        return self.sgprototype.alpha  
    
    @property
    def beta(self):
        return self.sgprototype.beta  

    @property
    def gamma(self):
        return self.sgprototype.gamma  
    