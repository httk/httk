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

from htdata import spacegroups
from fracvector import FracVector
from structureutils import *
from httk.crypto import tuple_to_hexhash
from httk.utils import is_unary, flatten
import htdata
      
class Prototype(object):
    """
    A basis and a list of atomic positions in that basis. 
    
    'Users' will normally not create prototype objects, but rather get them created via Structure.create(...)
    """   
    def __init__(self, hall_symbol, cell, coordgroups, counts, periodicity=0, individual_data=None):
        """
        (Private constructor, use Prototype.create instead)
        
        hall_symbol:   Hall symbol (string) for the space group and setting of the prototype, should be 'P1' if all atoms in the unit cell are present.
        cell:          FracVector 3x3 matrix of the cell vectors (as rows).
        coordgroups:   FracVector, list of lists of coordinates where each group of coordinates is one "slot" in the prototype, e.g.,
                          [ [ [x11,y11,z11],[x12,y12,z12],[x13,y13,z13] ] , [ [x21,y21,z21],[x22,y22,z22] ] , ... ]
                       all the x,y,z are the *reduced* coordinates of each atom.
        periodicity:   0 for a fully periodic structure, 111: non-periodic structure; 001, 010, 011, 100, 101 non-periodic along (xyz) axis.
        individual_data: a list of the same structure as coordgroups, with an entry of optional data type of each atom
        """
        self.hall_symbol = hall_symbol
        self.cell = cell
        self.coordgroups = coordgroups
        self.counts = counts
        self.periodicity = periodicity
        self._hexhash = None
        self.individual_data = individual_data

        self.coords, self.counts = coordgroups_to_coords(coordgroups)
        self.N = len(self.coords)

        # Helpful conversions
        self.niggli_matrix, self.orientation = cell_to_niggli(cell)
        self.basis_lengths, self.basis_angles = niggli_to_lengths_angles(self.niggli_matrix)
        self.a, self.b, self.c = self.basis_lengths
        self.alpha, self.beta, self.gamma = self.basis_angles

    @classmethod
    def use(cls,old):
        if isinstance(old,Prototype):
            return old
        else:
            try:
                return old.to_Prototype()
            except Exception as e:                
                raise Exception("Prototype.use: unknown input.")

    @classmethod
    def create(cls, cell=None, niggli_matrix=None, orientation = 1, a=None, b=None, c=None, lengths=None, 
               alpha=None, beta=None, gamma=None, angles=None,
               coords=None, coordgroups=None, cart_coords=None, cart_coordgroups=None, counts = None, 
               periodicity=0, spacegroup='P1', hall_symbol=None, individual_data=None, normalize=False): 
        """
        Create a new prototype from any sensible subset of the following parameters
        
        cell:          cell vectors (e.g., FracVector 3x3 matrix with cell vectors as rows)
        niggli_matrix: cell given via the niggli_matrix
        orientation:   +1 for right handed cell, -1 for left handed cell
        a, b, c:       separate cell vectors
        lengths:       list of length of cell vectors
        angles:        list of cell angles
        alpha, beta, gamma: cell angles
        coords:        list of coordinate triples in reduced cordinates (must also specify counts)
        coordgroups:   list of lists of reduced coordinates where each group of coordinates is one "slot" in the prototype
        cart_coords:   list of coordinate triples in cartesian coordinates
        cart_coordgroups: list of lists of cartesian coordinates where each group of coordinates is one "slot" in the prototype
        counts:        if coords specified, divides the coord list into "slots" in the prototype according to this list, e.g.
                           [5,7,3] means the first 5 coordinates are for slot1, the next 7 for slot2 and the last 3 for slot3.
        periodicity:   0 for a fully periodic structure, 111: non-periodic structure; 001, 010, 011, 100, 101 non-periodic along (xyz) axis.
        spacegroup:    a hall_symbol, spacegroup number or similar designation of the spacegroup.
        individual_data: a list of the same structure as coordgroups, with an entry of optional data type of each atom
        normalize:     set to False to not "mess" with the structue. Otherwise coordinates are sorted, etc., for a cheap effort to normalize structures
                       by sorting coordinates, etc.

        """

        if (cell == None and niggli_matrix == None and (a==None or b==None or c==None or alpha==None or beta==None or gamma==None) and (lengths==None or angles==None)):
            raise Exception("Structure.create: must give one of cell, niggli_matrix, (a,b,c,alpha,beta,gamma) or (lengths, angles).")

        if coordgroups == None and coords == None and cart_coords == None and counts==None and cart_coordgroups == None:
            raise Exception("Structure.create: must give one of coords, coordgroups, cart_coords, or cart_coordgroups.")
       
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

        if normalize:
            # A prototype does *not* include a volume, we always use the normalization where the largest one element
            # in the cell = 1, this way we avoid floating point operations for prototypes created from cells vectors
            # (prototypes created from lengths and angles is another matter)        
            c = cell
            maxele = max(c[0,0],c[0,1],c[0,2],c[1,0],c[1,1],c[1,2],c[2,0],c[2,1],c[2,2])
            cell = (c/maxele).simplify()
    
            ### Within each group, sort based on atomic coordinates
            coordgroups, individual_data = sort_coordgroups(coordgroups, individual_data) 
                  
        if hall_symbol == None:
            hall_symbol = htdata.spacegroups.spacegroup_get_hall(spacegroup)
            
        return Prototype(hall_symbol, cell, coordgroups, periodicity)

    def __rep__(self):
        return "<Structure: "+str(self.cell)+">"

    def to_tuple(self):
        proto = self                    
        return (proto.hall_symbol,proto.cell.to_tuple(), proto.coordgroups.to_tuple(),proto.periodicity)
    
    def __hash__(self):
        return self.to_tuple().__hash__()

    @property
    def hexhash(self):
        if self._hexhash == None:
            self._hexhash = tuple_to_hexhash(self.tidy().to_tuple())
        return self._hexhash

    def __eq__(self,other):
        if other == None:
            return False
        else:
            if self.cell == other.cell and self.coordgroups == other.coordgroups and self.volume == other.volume:
                return True
            return False
        
    def __neq__(self,other):
        if other == None:
            return True
        else:
            return not self.__eq__(other)

    def round(self,cell_resolution=10**8,coord_resolution=10**8):
        cell = self.cell.limit_resolution(cell_resolution).simplify()
        newcoordgroups = self.coordgroups.limit_resolution(coord_resolution).simplify()
        struct = Prototype(self.hall_symbol, cell, newcoordgroups, self.periodicity, self.individual_data)
        return struct

    def tidy(self):
        c2 = self.round()
        return c2

    @property
    def spacegroup_number(self):
        hall_symbol = self.hall_symbol
        return spacegroups.spacegroup_get_number(hall_symbol)

    @property
    def spacegroup_number_and_setting(self):
        hall_symbol = self.hall_symbol
        return spacegroups.spacegroup_get_number_and_setting(hall_symbol)

    @property
    def mh_symbol(self):
        hall_symbol = self.hall_symbol
        return spacegroups.spacegroup_get_hm(hall_symbol)

    @property
    def prototype_formula(self):
        return prototype_formula(self)    
