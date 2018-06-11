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
from cellshape import CellShape
from spacegrouputils import crystal_system_from_hall, lattice_system_from_hall

#TODO: Make this inherit CellShape


class Cell(HttkObject):

    """
    Represents a cell (e.g., a unitcell, but also possibly just the basis vectors of a non-periodic system)
    
    (The ability to represent the cell for a non-periodic system is also the reason this class is not called Lattice.)
    """
 
    @httk_typed_init({'basis': (FracVector, 3, 3), 'lattice_system': str, 'orientation': int})       
    def __init__(self, basis, lattice_system, orientation=1):
        """
        Private constructor, as per httk coding guidelines. Use Cell.create instead.
        """    
        self.basis = basis
        self.orientation = orientation
        self.lattice_system = lattice_system
        self.niggli_matrix, self.orientation = basis_to_niggli_and_orientation(basis)
 
        self.det = basis.det()
        self.inv = basis.inv()
        self._volume = abs(self.det)
        self.metric = niggli_to_metric(self.niggli_matrix)

        self.lengths, self.angles = niggli_to_lengths_and_angles(self.niggli_matrix)

        self.lengths = [FracVector.use(x).simplify() for x in self.lengths]
        self.angles = [FracVector.use(x).simplify() for x in self.angles]
        _dummy, self.cosangles, self.sinangles = niggli_to_lengths_and_trigangles(self.niggli_matrix)
        
        self.a, self.b, self.c = self.lengths
        self.alpha, self.beta, self.gamma = self.angles        
        self.cosalpha, self.cosbeta, self.cosgamma = self.cosangles        
        self.sinalpha, self.sinbeta, self.singamma = self.sinangles        
        
    #def create(cls, basis=None, a=None, b=None, c=None, alpha=None, beta=None, gamma=None, volume=None, scale=None, niggli_matrix=None, orientation=1, lengths=None, angles=None, normalize=True):
            
    @classmethod
    def create(cls, cell=None, basis=None, metric=None, niggli_matrix=None, 
               a=None, b=None, c=None, alpha=None, beta=None, gamma=None, 
               lengths=None, angles=None, cosangles=None, scale=None, 
               scaling=None, volume=None, periodicity=None, 
               nonperiodic_vecs=None, orientation=1, hall=None,
               lattice_system=None, eps=0):
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

        hall: giving the hall symbol makes it possible to determine the lattice system without numerical inaccuracy    
        
        lattice_system: any one of: 'cubic', 'hexagonal', 'tetragonal', 'orthorhombic', 'trigonal', 'triclinic', 'monoclinic', 'unknown'  
        """
        #print "Create cell:",cell,basis,angles, lengths,cosangles,a,b,c,alpha,beta,gamma
         
        if cell is not None:
            return Cell.use(cell)

        if basis is not None:
            basis = FracVector.use(basis)

        if angles is None and not (alpha is None or beta is None or gamma is None):
            angles = [alpha, beta, gamma]

        if lengths is None and not (a is None or b is None or c is None):
            lengths = [a, b, c]
        
        if cosangles is None and angles is not None:
            cosangles = angles_to_cosangles(angles)

        if basis is None and lengths is not None and cosangles is not None:
            if hall is not None:
                lattice_system = lattice_system_from_hall(hall)
            else:
                lattice_system = lattice_system_from_lengths_and_cosangles(lengths, cosangles)
            basis = lengths_and_cosangles_to_conventional_basis(lengths, cosangles, lattice_system, orientation=orientation, eps=eps)

        if niggli_matrix is not None:
            niggli_matrix = FracVector.use(niggli_matrix)

        if niggli_matrix is None and basis is not None:
            niggli_matrix, orientation = basis_to_niggli_and_orientation(basis)

        #if niggli_matrix is None and lengths is not None and cosangles is not None:
        #    niggli_matrix = lengths_and_cosangles_to_niggli(lengths, cosangles)
        #    niggli_matrix = FracVector.use(niggli_matrix)

        #if niggli_matrix is None and lengths is not None and angles is not None:
        #    niggli_matrix = lengths_and_angles_to_niggli(lengths, angles)
        #    niggli_matrix = FracVector.use(niggli_matrix)

        #if niggli_matrix is None and not (a is None or b is None or c is None or alpha is None or beta is None or gamma is None):
        #    niggli_matrix = lengths_and_angles_to_niggli([a, b, c], [alpha, beta, gamma])
        #    niggli_matrix = FracVector.use(niggli_matrix)

        if basis is None:
            raise Exception("cell.create: Not enough information to specify a cell given.")
                
        if scaling is None and scale is not None:
            scaling = scale

        if scaling is not None and volume is not None:
            raise Exception("Cell.create: cannot specify both scaling and volume!")
            
        if volume is not None:
            scaling = vol_to_scale(basis, volume)

        if scaling is not None:
            scaling = FracVector.use(scaling)
            basis = (basis*scaling).simplify()

        # Determination of the lattice system can only be made approximately, so it is recommended
        # that it is given to the constructor if possible

        if (lattice_system is None or lattice_system == 'unknown') and hall is not None:
            lattice_system = lattice_system_from_hall(hall)

        if lattice_system is None or lattice_system == 'unknown':
            lattice_system = lattice_system_from_niggli(niggli_matrix)

        if basis is None:
            basis = FracVector.use(niggli_to_conventional_basis(niggli_matrix, lattice_system, orientation=orientation))
            
        return cls(basis, lattice_system, orientation)

    @classmethod
    def use(cls, other):
        if isinstance(other, Cell):
            return other
        else:
            try:
                if len(other) == 3:
                    return cls.create(basis=other)        
                elif len(other) == 2:
                    return cls.create(niggli_matrix=other)
                elif len(other) == 1:
                    return cls.create(a=other[0], b=other[1], c=other[2], alpha=other[3], beta=other[4], gamma=other[5])
            except Exception:
                pass
        raise Exception("Cell.use: do not know how to use an object of class:"+str(other.__class__))

    @httk_typed_property(FracScalar)
    def volume(self):
        return self._volume

    #@httk_typed_property((FracVector, 3, 3))
    #def basis(self):
    #    return self._basis

    #@httk_typed_property((FracVector, 3, 2))
    #def niggli_matrix(self):
    #    return self._niggli_matrix

    def get_axes_standard_order_transform(self):
        return standard_order_axes_transform(self.niggli_matrix, self.lattice_system)

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

#     # Type translators where convenient types and primitive types differ
#     @classmethod
#     def types_from_primitive(cls,data):
#         if 'maxnorm_basis_g' in data:
#             data['maxnorm_basis'] = FracVector(data['maxnorm_basis_g'],1000000000)
#             del(data['maxnorm_basis_g'])
#         if 'volume_g' in data:
#             data['volume'] = FracVector(data['volume_g'],1000000000)
#             del(data['volume_g'])
#         return data
# 
#     @classmethod
#     def types_to_primitive(cls,data):
#         if 'maxnorm_basis' in data:
#             adjustedmatrix = (data['maxnorm_basis_g']*1000000000).to_fractions()
#             data['maxnorm_basis_g'] = [[int(x) for x in y] for y in adjustedmatrix]
#             del(data['maxnorm_basis'])
#         if 'volume_g' in data:
#             data['volume'] = FracVector(data['volume_g'],1000000000)
#             del(data['volume'])
#         return data

    def get_normalized_longestvec(self):
        # Somewhat unusual normalization where the largest one element
        # in the cell = 1, this way we avoid floating point operations for prototypes created from cell vectors
        # (prototypes created from lengths and angles is another matter)
        scale = self.normalization_scale.inv()
        return Cell.create(basis=self.basis*scale.simplify())

    def clean(self):
        newbasis = self.basis.limit_denominator(5000000)
        #new_niggli_matrix = self.niggli_matrix.limit_denominator(5000000)
        return self.__class__(newbasis, lattice_system=self.lattice_system, orientation=self.orientation)

    @property
    def normalization_longestvec_scale(self):
        """
        Get the factor with which a normalized version of this cell needs to be multiplied to reproduce this cell.

        I.e. self = (normalization_scale)*self.get_normalized()
        """
        # We use the somewhat unusual normalization where the largest one element
        # in the cell = 1, this way we avoid floating point operations for prototypes created from cell vectors
        # (prototypes created from lengths and angles is another matter)
        #        
        c = self.basis
        maxele = max(c[0, 0], c[0, 1], c[0, 2], c[1, 0], c[1, 1], c[1, 2], c[2, 0], c[2, 1], c[2, 2])
        maxeleneg = max(-c[0, 0], -c[0, 1], -c[0, 2], -c[1, 0], -c[1, 1], -c[1, 2], -c[2, 0], -c[2, 1], -c[2, 2])
        if maxeleneg > maxele:
            scale = (-maxeleneg).simplify()
        else:
            scale = (maxele).simplify()
        return scale

    @property
    def normalization_scale(self):
        """
        """
        return FracScalar.create(pow(float(self.basis.det()), 0.33333333333333333333333))

    def get_normalized(self):
        scale = self.normalization_scale.inv()
        return Cell.create(basis=self.basis*scale.simplify())

    def __str__(self):
        return "<Cell: %.8f * \n    [" % (self.normalization_scale)+"\n     ".join(["% .8f % .8f % .8f" % (x[0], x[1], x[2]) for x in self.get_normalized().basis.to_floats()])+"]>" 
        

def main():
    pass

if __name__ == "__main__":
    main()
    
    
