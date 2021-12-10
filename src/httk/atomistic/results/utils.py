from httk.core.httkobject import HttkObject, httk_typed_init
from httk.core import FracVector

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
        Private constructor, as per httk coding guidelines. Use ElasticTensor.create instead.
        """
        self._matrix = _matrix

    @classmethod
    def create(cls, matrix=None):
        """
        matrix = A 6x6 array that represent the elastic constants.
        """
        if matrix is None:
            raise Exception("ElasticTensor.create: The elastic constants matrix must be given as a 6x6 array.")
        # else:
        #     matrix = FracVector.use(matrix)
        return cls(matrix)

    @property
    def matrix(self):
        return list(self._matrix)

class ThirdOrderElasticTensor(HttkObject):
    @httk_typed_init({'_matrix': (float, 6, 6*6), '_shape': (int, 1, 3)})
    def __init__(self, _matrix, _shape):
        """
        Private constructor, as per httk coding guidelines. Use ThirdOrderElasticTensor.create instead.
        """
        self._matrix = _matrix
        self._shape = _shape

    @classmethod
    def create(cls, matrix=None, shape=(6,6,6)):
        """
        matrix = A 6x6x6 array that represent the third order elastic constants.
        """
        if matrix is None:
            raise Exception("ThirdOrderElasticTensor.create: The elastic constants matrix must be given as a 6x6x6 array.")
        # else:
        #     matrix = FracVector.use(matrix)
        return cls(matrix, shape)

    @property
    def matrix(self):
        return list(self._matrix)

    @property
    def shape(self):
        return [x[0] for x in list(self._shape)]

class PlaneDependentTensor(HttkObject):
    """Generic class for a crystal plane direction dependent quantities.
    Goes from [000] up to [222].
    """
    @httk_typed_init({'_matrix': (float, 3, 3*3), '_shape': (int, 1, 3)})
    def __init__(self, _matrix, _shape):
        """
        Private constructor, as per httk coding guidelines. Use PlaneDependentTensor.create instead.
        """
        self._matrix = _matrix
        self._shape = _shape

    @classmethod
    def create(cls, matrix=None, shape=(3,3,3)):
        """
        matrix = A 2x2x2 array that represent the elastic constants.
        """
        if matrix is None:
            raise Exception("PlaneDependentTensor.create: The elastic constants matrix must be given as a 2x2x2 array.")
        # else:
        #     matrix = FracVector.use(matrix)
        return cls(matrix, shape)

    @property
    def matrix(self):
        return list(self._matrix)

    @property
    def shape(self):
        return [x[0] for x in list(self._shape)]
