import copy
from httk.core.httkobject import HttkObject, httk_typed_init
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
    def use(cls, other):
        if isinstance(other, InitialStructure):
            return other
        elif isinstance(other, Structure):
            return InitialStructure(other.assignments, other.rc_sites,
                                    other.rc_cell)
        else:
            raise Exception("InitialStructure.use: do not know how to use object of class:"+str(other.__class__))

    def __str__(self):
        return "<httk InitialStructure object:\n  "+str(self.rc_cell)+"\n  "+str(self.assignments)+"\n  "+str(self.rc_sites)+"\n  Tags:"+str([str(self.get_tags()[tag]) for tag in self.get_tags()])+"\n  Refs:"+str([str(ref) for ref in self.get_refs()])+"\n>"

class ElasticTensor(HttkObject):
    @httk_typed_init({'matrix': (FracVector, 6, 6)})
    def __init__(self, matrix):
        """
        Private constructor, as per httk coding guidelines. Use ElasticTensor.create instead.
        """
        self.matrix = matrix

    @classmethod
    def create(cls, matrix=None):
        """
        matrix = A 6x6 array that represent the elastic constants.
        """
        if matrix is None:
            raise Exception("ElasticTensor.create: The elastic constants matrix must be given as a 6x6 array.")
        else:
            matrix = FracVector.use(matrix)
        return cls(matrix)

class ElasticTensorFloat(HttkObject):
    @httk_typed_init({'_matrix': (float, 6, 6)})
    def __init__(self, _matrix):
        """
        Private constructor, as per httk coding guidelines. Use ElasticTensorFloat.create instead.
        """
        self._matrix = _matrix

    @classmethod
    def create(cls, matrix=None):
        """
        matrix = A 6x6 array that represent the elastic constants.
        """
        if matrix is None:
            raise Exception("ElasticTensorFloat.create: The elastic constants matrix must be given as a 6x6 array of floats.")
        return cls(matrix)

    @property
    def matrix(self):
        return list(self._matrix)

class ThirdOrderElasticTensor(HttkObject):
    @httk_typed_init({'_matrix': (float, 6*6, 6), '_shape': (int, 1, 3)})
    def __init__(self, _matrix, _shape):
        """
        Private constructor, as per httk coding guidelines. Use ThirdOrderElasticTensor.create instead.
        """
        # The SQLite database returns the _matrix and the _shape as a zip iterator,
        # so for convenience we make sure that they are always normal lists here.
        self._matrix = list(_matrix)
        # Make sure that _matrix is always in the 2D 6x36 format.
        if len(self._matrix[0]) == 6:
            tmp1 = []
            for i in range(6):
                tmp2 = []
                for j in range(6):
                    for k in range(6):
                        tmp2.append(self._matrix[i][j][k])
                tmp1.append(tmp2)
            self._matrix = tmp1
        self._shape = list(_shape)

    @classmethod
    def create(cls, matrix=None, shape=(6,6,6)):
        """
        matrix = A 6x6x6 array that represent the third order elastic constants.
        """
        if matrix is None:
            raise Exception("ThirdOrderElasticTensor.create: The elastic constants matrix must be given as a 6x6x6 array.")
        return cls(matrix, shape)

    # @property
    def matrix(self, flatten=False, include_indices=False):
        """If flatten=False, re-create the third dimension from the flattened 2D _matrix.
        If flatten=True, return a flattened 1D array.
        """
        shape = self.shape
        matrix = []
        if flatten:
            for i in range(shape[0]):
                index_flat = 0
                for j in range(shape[1]):
                    for k in range(shape[2]):
                        if include_indices:
                            index_tuple = (i+1,j+1,k+1)
                            matrix.append((index_tuple, self._matrix[i][index_flat]))
                        else:
                            matrix.append(self._matrix[i][index_flat])
                        index_flat += 1
        else:
            for i in range(shape[0]):
                index_flat = 0
                tmp1 = []
                for j in range(shape[1]):
                    tmp2 = []
                    for k in range(shape[2]):
                        tmp2.append(self._matrix[i][index_flat])
                        index_flat += 1
                    tmp1.append(tmp2)
                matrix.append(tmp1)
        return matrix

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
    @httk_typed_init({'_matrix': (float, (Nmax+1)*(Nmax+1), Nmax+1), '_shape': (int, 1, Nmax+1)})
    def __init__(self, _matrix, _shape):
        global Nmax
        """
        Private constructor, as per httk coding guidelines. Use PlaneDependentTensor.create instead.
        """
        self._matrix = list(_matrix)
        # Make sure that _matrix is always in the 2D 3x9 format.
        if len(self._matrix[0]) == Nmax+1:
            tmp1 = []
            for i in range(Nmax+1):
                tmp2 = []
                for j in range(Nmax+1):
                    for k in range(Nmax+1):
                        tmp2.append(self._matrix[i][j][k])
                tmp1.append(tmp2)
            self._matrix = tmp1
        self._shape = list(_shape)

    @classmethod
    def create(cls, matrix=None, shape=(Nmax+1,Nmax+1,Nmax+1)):
        """
        matrix = A 3x3x3 array that represent plane dependent quantities.
        """
        if matrix is None:
            raise Exception("PlaneDependentTensor.create: The matrix must be given as a 3x3x3 array.")
        return cls(matrix, shape)

    # @property
    def matrix(self, flatten=False, include_indices=False):
        """If flatten=False, re-create the third dimension from the flattened 2D _matrix.
        If flatten=True, return a flattened 1D array.
        """
        shape = self.shape
        matrix = []
        if flatten:
            for i in range(shape[0]):
                index_flat = 0
                for j in range(shape[1]):
                    for k in range(shape[2]):
                        if include_indices:
                            matrix.append(((i,j,k), self._matrix[i][index_flat]))
                        else:
                            matrix.append(self._matrix[i][index_flat])
                        index_flat += 1
        else:
            for i in range(shape[0]):
                index_flat = 0
                tmp1 = []
                for j in range(shape[1]):
                    tmp2 = []
                    for k in range(shape[2]):
                        tmp2.append(self._matrix[i][index_flat])
                        index_flat += 1
                    tmp1.append(tmp2)
                matrix.append(tmp1)
        return matrix

    @property
    def shape(self):
        # When returned from SQLite, each integer is wrapped in a tuple,
        # so we check for it here.
        if hasattr(self._shape[0], "__iter__"):
            return [x[0] for x in self._shape]
        else:
            return self._shape

