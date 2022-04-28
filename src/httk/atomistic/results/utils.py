#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2022 Henrik Levämäki
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

import copy
import math
from httk.core.httkobject import HttkObject, httk_typed_init
from httk.core import Computation
from httk.core.reference import Reference
from httk.core import FracVector
from httk.atomistic import Structure, Spacegroup
from httk.atomistic.assignments import Assignments
from httk.atomistic.sites import Sites
from httk.atomistic.cell import Cell
from httk.atomistic.representativesites import RepresentativeSites

# Store initial_structure (the input file POSCAR) as a new class,
# so that the Structure table in the SQLite file does not get
# polluted with initial structures.
class InitialStructure(Structure):

    @classmethod
    def create(cls, assignments=None, rc_sites=None, rc_cell=None):
        return InitialStructure(assignments, rc_sites, rc_cell)

    @classmethod
    def use(cls, other):
        if isinstance(other, InitialStructure):
            return other
        elif isinstance(other, Structure):
            return InitialStructure(other.assignments, other.rc_sites,
                                    other.rc_cell)
        else:
            raise Exception("InitialStructure.use: do not know how to use object of class:"+str(other.__class__))

    def __str__(self):
        return "<httk InitialStructure object:\n  "+str(self.rc_cell)+"\n  "+\
               str(self.assignments)+"\n  "+str(self.rc_sites)+"\n  Tags:"+\
               str([str(self.get_tags()[tag]) for tag in self.get_tags()])+\
               "\n  Refs:"+str([str(ref) for ref in self.get_refs()])+"\n>"


class ElasticTensor(HttkObject):
    @httk_typed_init({'_matrix': (FracVector, 6, 6), '_nan_mask': (int, 6, 6)})
    def __init__(self, _matrix, _nan_mask):
        """
        Private constructor, as per httk coding guidelines. Use ElasticTensor.create instead.
        """
        self._matrix = _matrix.set_denominator(5000000)
        self._nan_mask = tuple(_nan_mask)

    @classmethod
    def create(cls, matrix=None):
        """
        matrix = A 6x6 array that represent the elastic constants.
        """
        denom = 5000000
        nan_mask = []
        if matrix is None:
            raise Exception("ElasticTensor.create: The elastic constants matrix must be given as a 6x6 array.")
        for i in range(6):
            tmp = []
            for j in range(6):
                if not math.isnan(matrix[i][j]):
                    matrix[i][j] = int(round(matrix[i][j]*denom, 0))
                    tmp.append(0)
                else:
                    # Store NaNs as zero in the array and flag them as NaN
                    # in the mask.
                    matrix[i][j] = 0
                    tmp.append(1)
            nan_mask.append(tuple(tmp))
        nan_mask = tuple(nan_mask)
        matrix = FracVector(noms=matrix, denom=denom)
        return cls(matrix, nan_mask)

    @property
    def matrix(self):
        noms = self._matrix.noms
        new_noms = []
        for i in range(6):
            tmp = []
            for j in range(6):
                if self._nan_mask[i][j]:
                    tmp.append(math.nan)
                    # tmp.append(None)
                else:
                    tmp.append(noms[i][j])
            new_noms.append(tmp)
        return FracVector(noms=new_noms, denom=5000000)


class ThirdOrderElasticTensor(HttkObject):
    @httk_typed_init({'_matrix': (FracVector, 6*6, 6), '_nan_mask': (int, 6*6, 6), '_shape': (int, 1, 3)})
    def __init__(self, _matrix, _nan_mask, _shape):
        """
        Private constructor, as per httk coding guidelines. Use ThirdOrderElasticTensor.create instead.
        """
        self._matrix = _matrix.set_denominator(5000000)
        # # Make sure that _matrix is always in the 2D 6x36 format.
        # if len(self._matrix[0]) == 6:
        #     tmp1 = []
        #     for i in range(6):
        #         tmp2 = []
        #         for j in range(6):
        #             for k in range(6):
        #                 tmp2.append(self._matrix[i][j][k])
        #         tmp1.append(tmp2)
        #     self._matrix = tmp1
        self._nan_mask = tuple(_nan_mask)
        self._shape = tuple(_shape)

    @classmethod
    def create(cls, matrix=None, shape=(6,6,6)):
        """
        matrix = A 6x6x6 array that represent the third order elastic constants.
        """
        denom = 5000000
        nan_mask = []
        matrix_flat = []
        if matrix is None:
            raise Exception("ThirdOrderElasticTensor.create: The elastic constants matrix must be given as a 6x6x6 array.")

        for i in range(shape[0]):
            mask_tmp = []
            matrix_tmp = []
            index_flat = 0
            for j in range(shape[1]):
                for k in range(shape[2]):
                    if not math.isnan(matrix[i][j][k]):
                        matrix_tmp.append(int(round(matrix[i][j][k]*denom, 0)))
                        mask_tmp.append(0)
                    else:
                        # Store NaNs as zero in the array and flag them as NaN
                        # in the mask.
                        matrix_tmp.append(0)
                        mask_tmp.append(1)
                    index_flat += 1
            matrix_flat.append(matrix_tmp)
            nan_mask.append(tuple(mask_tmp))
        nan_mask = tuple(nan_mask)
        matrix = FracVector(noms=matrix_flat, denom=denom)
        return cls(matrix, nan_mask, shape)

    def matrix(self, flatten=False, include_indices=False):
        """If flatten=False, re-create the third dimension from the flattened 2D _matrix.
        If flatten=True, return a flattened 1D array.
        """
        shape = self.shape
        noms = self._matrix.noms
        new_noms = []
        indices = []
        if flatten:
            for i in range(shape[0]):
                index_flat = 0
                for j in range(shape[1]):
                    for k in range(shape[2]):
                        if self._nan_mask[i][index_flat]:
                            new_noms.append(math.nan)
                            # new_noms.append(None)
                        else:
                            new_noms.append(noms[i][index_flat])
                        if include_indices:
                            indices.append((i+1, j+1, k+1))
                        index_flat += 1
        else:
            for i in range(shape[0]):
                index_flat = 0
                tmp1 = []
                for j in range(shape[1]):
                    tmp2 = []
                    for k in range(shape[2]):
                        if self._nan_mask[i][index_flat]:
                            tmp2.append(math.nan)
                            # tmp2.append(None)
                        else:
                            tmp2.append(noms[i][index_flat])
                        index_flat += 1
                    tmp1.append(tmp2)
                new_noms.append(tmp1)
        if flatten and include_indices:
            return FracVector(noms=new_noms, denom=5000000), tuple(indices)
        else:
            return FracVector(noms=new_noms, denom=5000000)

    @property
    def shape(self):
        # When returned from SQLite, each integer is wrapped in a tuple,
        # so we check for it here.
        if hasattr(self._shape[0], "__iter__"):
            return [x[0] for x in self._shape]
        else:
            return self._shape

Nmax = 2
class PlaneDependentTensor(HttkObject):
    """Generic class for a crystal plane direction dependent quantities.
    Goes from plane [000] up to [Nmax,Nmax,Nmax].
    """
    @httk_typed_init({'_matrix': (FracVector, (Nmax+1)*(Nmax+1), Nmax+1),
                      '_nan_mask': (int, (Nmax+1)*(Nmax+1), Nmax+1),
                      '_shape': (int, 1, Nmax+1)})
    def __init__(self, _matrix, _nan_mask, _shape):
        """
        Private constructor, as per httk coding guidelines. Use PlaneDependentTensor.create instead.
        """
        self._matrix = _matrix.set_denominator(5000000)
        self._nan_mask = tuple(_nan_mask)
        self._shape = tuple(_shape)

    @classmethod
    def create(cls, matrix=None, shape=(Nmax+1,Nmax+1,Nmax+1)):
        """
        matrix = A Nmax*Nmax*Nmax array that represent plane dependent quantities.
        """
        denom = 5000000
        nan_mask = []
        matrix_flat = []
        if matrix is None:
            raise Exception("PlaneDependentTensor.create: The plane dependent matrix must be given as a Nmax*Nmax*Nmax array.")

        for i in range(shape[0]):
            mask_tmp = []
            matrix_tmp = []
            index_flat = 0
            for j in range(shape[1]):
                for k in range(shape[2]):
                    if not math.isnan(matrix[i][j][k]):
                        matrix_tmp.append(int(round(matrix[i][j][k]*denom, 0)))
                        mask_tmp.append(0)
                    else:
                        # Store NaNs as zero in the array and flag them as NaN
                        # in the mask.
                        matrix_tmp.append(0)
                        mask_tmp.append(1)
                    index_flat += 1
            matrix_flat.append(matrix_tmp)
            nan_mask.append(tuple(mask_tmp))
        nan_mask = tuple(nan_mask)
        matrix = FracVector(noms=matrix_flat, denom=denom)
        return cls(matrix, nan_mask, shape)

    def matrix(self, flatten=False, include_indices=False):
        """If flatten=False, re-create the third dimension from the flattened 2D _matrix.
        If flatten=True, return a flattened 1D array.
        """
        shape = self.shape
        noms = self._matrix.noms
        new_noms = []
        indices = []
        if flatten:
            for i in range(shape[0]):
                index_flat = 0
                for j in range(shape[1]):
                    for k in range(shape[2]):
                        if self._nan_mask[i][index_flat]:
                            new_noms.append(math.nan)
                            # new_noms.append(None)
                        else:
                            new_noms.append(noms[i][index_flat])
                        if include_indices:
                            indices.append((i+1, j+1, k+1))
                        index_flat += 1
        else:
            for i in range(shape[0]):
                index_flat = 0
                tmp1 = []
                for j in range(shape[1]):
                    tmp2 = []
                    for k in range(shape[2]):
                        if self._nan_mask[i][index_flat]:
                            tmp2.append(math.nan)
                            # tmp2.append(None)
                        else:
                            tmp2.append(noms[i][index_flat])
                        index_flat += 1
                    tmp1.append(tmp2)
                new_noms.append(tmp1)
        if flatten and include_indices:
            return FracVector(noms=new_noms, denom=5000000), tuple(indices)
        else:
            return FracVector(noms=new_noms, denom=5000000)

    @property
    def shape(self):
        # When returned from SQLite, each integer is wrapped in a tuple,
        # so we check for it here.
        if hasattr(self._shape[0], "__iter__"):
            return [x[0] for x in self._shape]
        else:
            return self._shape

class MaterialId(HttkObject):
    @httk_typed_init({'manifest_hash': str})
    def __init__(self, manifest_hash):
        """
        Private constructor, as per httk coding guidelines. Use ElasticTensor.create instead.
        """
        self.manifest_hash = manifest_hash

    @property
    def material_id(self):
        return self.db.sid

class Method(HttkObject):
    @httk_typed_init({'name': str, 'description': str, 'references': [Reference]},
                     index=['name', 'description', 'references'])
    def __init__(self, name, description, references):
        self.name = name
        self.description = description
        self.references = references

class MethodDescriptions(HttkObject):
    @httk_typed_init({'methods': [Method]}, index=['methods'])
    def __init__(self, methods=[]):
        # super(MethodDescriptions, self).__init__()
        self.methods = methods

    # These add_method* functions do not work as expected, because for some reason
    # they cause every Method added in the database to appear in the self.methods
    # list of every MethodDescription instance.
    # Adding the list of methods using __init__ seems to work as expected.
    # def add_method(self, method):
    #     self.methods.append(method)

    # def add_methods(self, methods):
    #     for m in methods:
    #         self.add_method(m)
