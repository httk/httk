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
from httk.core.geometry import is_point_inside_cell
from httk.core import HttkObject, httk_typed_init, httk_typed_property
from httk.core import FracVector, FracScalar
from httk.core.basic import is_sequence
from cellutils import *


class CellShape(HttkObject):

    """
    Represents a cell (e.g., a unitcell, but also possibly just the basis vectors of a non-periodic system)
    """
 
    @httk_typed_init({'niggli_matrix': (FracVector, 3, 2), 'orientation': int})       
    def __init__(self, niggli_matrix, orientation=1, basis=None):
        """
        Private constructor, as per httk coding guidelines. Use Cell.create instead.
        """
        self.niggli_matrix = niggli_matrix
        self.orientation = orientation
        if basis is None:
            basis = FracVector.use(niggli_to_basis(niggli_matrix, orientation=orientation))
            c = basis
            maxele = max(c[0, 0], c[0, 1], c[0, 2], c[1, 0], c[1, 1], c[1, 2], c[2, 0], c[2, 1], c[2, 2])
            maxeleneg = max(-c[0, 0], -c[0, 1], -c[0, 2], -c[1, 0], -c[1, 1], -c[1, 2], -c[2, 0], -c[2, 1], -c[2, 2])
            if maxeleneg > maxele:
                scale = (-maxeleneg).simplify()
            else:
                scale = (maxele).simplify()
            basis = (basis * scale.inv()).simplify()
        
        self._basis = basis
 
        self.det = basis.det()
        self.inv = basis.inv()
        self.volume = abs(self.det)
        self.metric = niggli_to_metric(self.niggli_matrix)

        self.lengths, self.angles = niggli_to_lengths_angles(self.niggli_matrix)

        self.lengths = [FracVector.use(x).simplify() for x in self.lengths]
        self.angles = [FracVector.use(x).simplify() for x in self.angles]
        
        self.a, self.b, self.c = self.lengths
        self.alpha, self.beta, self.gamma = self.angles        

    #def create(cls, basis=None, a=None, b=None, c=None, alpha=None, beta=None, gamma=None, volume=None, scale=None, niggli_matrix=None, orientation=1, lengths=None, angles=None, normalize=True):
            
    @classmethod
    def create(cls, cellshape=None, basis=None, metric=None, niggli_matrix=None, a=None, b=None, c=None, alpha=None, beta=None, gamma=None,
               lengths=None, angles=None, scale=None, scaling=None, volume=None, periodicity=None, nonperiodic_vecs=None, orientation=1):
        """
        Create a new cell object, 
        
        cell: any one of the following: 

          - a 3x3 array with (in rows) the three basis vectors of the cell (a non-periodic system should conventionally use an identity matrix)

          - a dict with a single key 'niggli_matrix' with a 3x2 array with the Niggli Matrix representation of the cell

          - a dict with 6 keys, 'a', 'b', 'c', 'alpha', 'beta', 'gamma' giving the cell parameters as floats

        scaling: free form input parsed for a scale.
            positive value = multiply basis vectors by this value
            negative value = rescale basis vectors so that cell volume becomes abs(value).

        scale: set to non-None to multiply all cell vectors with this factor

        volume: set to non-None if the basis vectors only give directions, and the volume of the cell should be this value (overrides scale)

        periodicity: free form input parsed for periodicity
            sequence: True/False for each basis vector being periodic
            integer: number of non-periodic basis vectors 
        
        """
        if isinstance(cellshape, CellShape):
            basis = cellshape.basis
        elif cellshape is not None:
            basis = cell_to_basis(cellshape)

        if basis is not None:
            basis = FracVector.use(basis)

        if niggli_matrix is not None:
            niggli_matrix = FracVector.use(niggli_matrix)
            basis = FracVector.use(niggli_to_basis(niggli_matrix, orientation=orientation))

        if niggli_matrix is None and basis is not None:
            niggli_matrix, orientation = basis_to_niggli(basis)

        if niggli_matrix is None and lengths is not None and angles is not None:
            niggli_matrix = lengths_angles_to_niggli(lengths, angles)
            niggli_matrix = FracVector.use(niggli_matrix)
            if basis is None:
                basis = FracVector.use(niggli_to_basis(niggli_matrix, orientation=1))

        if niggli_matrix is None and not (a is None or b is None or c is None or alpha is None or beta is None or gamma is None):
            niggli_matrix = lengths_angles_to_niggli([a, b, c], [alpha, beta, gamma])
            niggli_matrix = FracVector.use(niggli_matrix)
            if basis is None:
                basis = FracVector.use(niggli_to_basis(niggli_matrix, orientation=1))

        if niggli_matrix is None:
            raise Exception("CellShape.create: Not enough information to specify a cell given.")
                
        if scaling is None and scale is not None:
            scaling = scale

        if scaling is not None and volume is not None:
            raise Exception("CellShape.create: cannot specify both scaling and volume!")
            
        if volume is not None:
            scaling = vol_to_scale(basis, volume)

        if scaling is not None:
            scaling = FracVector.use(scaling)
            niggli_matrix = (basis*scaling*scaling).simplify()
            if basis is not None:
                basis = (basis*scaling).simplify()

        # For the basis we use a somewhat unusual normalization where the largest one element
        # in the cell = 1, this way we avoid floating point operations for prototypes created 
        # from cell vector (prototypes created from lengths and angles is another matter)

        if basis is not None:
            c = basis
            maxele = max(c[0, 0], c[0, 1], c[0, 2], c[1, 0], c[1, 1], c[1, 2], c[2, 0], c[2, 1], c[2, 2])
            maxeleneg = max(-c[0, 0], -c[0, 1], -c[0, 2], -c[1, 0], -c[1, 1], -c[1, 2], -c[2, 0], -c[2, 1], -c[2, 2])
            if maxeleneg > maxele:
                scale = (-maxeleneg).simplify()
            else:
                scale = (maxele).simplify()
            basis = (basis * scale.inv()).simplify()

        c = niggli_matrix
        maxele = max(c[0, 0], c[0, 1], c[0, 2])
        niggli_matrix = (niggli_matrix * maxele.inv()).simplify()
      
        return cls(niggli_matrix, orientation, basis)

    @httk_typed_property((FracVector, 3, 3))
    def basis(self):
        return self._basis

    def scaling(self):
        return -self.volume

    def coords_reduced_to_cartesian(self, coords):
        coords = FracVector.use(coords)
        return coords*self.basis

    def coordgroups_reduced_to_cartesian(self, coordgroups):    
        newcoordgroups = []    
        for coordgroup in coordgroups:
            newcoordgroups += [self.coords_reduced_to_cartesian(coordgroup)]    
        return FracVector.stack(newcoordgroups)

    def coords_cartesian_to_reduced(self, coords):
        coords = FracVector.use(coords)
        return coords*self.inv

    def coordgroups_cartesian_to_reduced(self, coordgroups):    
        newcoordgroups = []    
        for coordgroup in coordgroups:
            newcoordgroups += [self.coords_cartesian_to_reduced(coordgroup)]    
        return FracVector.stack(newcoordgroups)

    def is_point_inside(self, cartesian_coord):
        is_point_inside_cell(self.basis, cartesian_coord)

    def clean(self):
        newbasis = self.basis.limit_denominator(5000000)
        new_niggli = self.niggli_matrix.limit_denominator(5000000)
        return self.__class__(niggli_matrix=new_niggli, basis=newbasis)
        

def main():
    pass

if __name__ == "__main__":
    main()
    
    
