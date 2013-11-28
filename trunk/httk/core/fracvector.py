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

import fractions
import operator
import itertools
from httk.crypto import tuple_to_hexhash

class FracVector(object):
    """
    FracVector is a general *unmutable* N-dimensional vector (tensor) class for performing linear algebra with fractional numbers. 
    
    A FracVector consists of a multidimensional tuple of integer nominators, and a single shared integer denominator.
    
    FracVectors are immutable. Every operation on a FracVector returns a new FracVector with the result of the operation. A created
    FracVector never changes. Hence, they are safe to use as keys in dictionaries, to use in sets, etc.

    Note: most methods return un-simplified FracVector results. I.e., if one expects to get a FracVector with the smallest possible
    denominator, one should generally call fracvector.simplify() before using the result.
    """

    #### Creation methods

    def __init__(self, noms, denom):
        """ Low overhead constructor.
        
        noms: nested *tuples* (may not be a lists!) of nominator integers
        denom: integer denominator
        
        Represents the tensor 1/denoms*(noms)
        
        If you want to create a FracVector from something else than tuples, use the FracVector.create() method.
        """
        self.noms = noms
        self.denom = denom
        self._dim = None
        self._hexhash = None

    @classmethod
    def use(cls,old):
        """Make sure variable is a FracVector, and if not, convert it."""
        if isinstance(old,FracVector):
            return old
        else:
            try:
                fracvec = old.to_FracVector()
                return cls.__init__(fracvec.noms,fracvec.denom)        
            except Exception:
                pass
            
            return cls.create(old) 

    @classmethod
    def create(cls, noms, denom=None, simplify=True, chain=False):
        """
        Create a FracVector.
              
        FracVector(something)
          something may be any nested list or tuple of objects that can be used in the constructor of the Python Fraction class
          (also works with strings!). If any object found while traveling the items has a .to_fractions() method, it will be called
          and is expected to return a fraction or list or tuple of fractions.
        
          Most importantly: FracVector itself implements .to_fractions(), and hence, the same constructor allows stacking
          several FracVector objects like this:
            horizvector = FracVector([fracvector1,fracvector2],chain=True)
            vertvector = FracVector([[fracvector1],[fracvector2]])
        """
        def lcd(a, y):
            try:
                b = abs(fractions.Fraction(y)).denominator
            except TypeError:
                b = abs(fractions.Fraction(str(y))).denominator                
            return a * b // fractions.gcd(a, b)
        def frac(x):
            return (fractions.Fraction(x) * lcd).numerator

        lcd = nested_reduce_fractions(lambda x, y: lcd(x, y), noms, initializer=1)
        v_noms = nested_map_fractions(lambda x: frac(x), noms)

        if chain:
            v_noms = tuple(itertools.chain(*v_noms))

        if denom == None:                          
            v = FracVector(v_noms, lcd)                       
        else:
            v = FracVector(v_noms, lcd * denom)                       

        if simplify and v.denom != 1:
            v = v.simplify()

        return v

    @classmethod
    def chain(cls, vecs):
        """
        Optimized chaning of FracVectors. 
        
        vecs = a list (or tuple) of fracvectors.
        
        Returns the same thing as
           FracVector.create(vecs,chain=True)
        but only works if all vectors share the same denominator (raises an exception if this is not true)
        """   
        noms = []
        denom = vecs[0].denom
        for vec in vecs:
            if vec.denom != denom:
                raise Exception("ExactVector.merge: can only work with vectors sharing the same denom.")
            noms += vec.noms
        noms = tuple(noms)
        return FracVector(noms, denom)

    @classmethod
    def stack(cls, vecs):
        """
        Optimized stacking of FracVectors. 
        
        vecs = a list (or tuple) of fracvectors.
        
        Returns the same thing as
           FracVector.create(vecs)
        but only works if all vectors share the same denominator (raises an exception if this is not true)
        """        
        noms = []
        denom = vecs[0].denom
        for vec in vecs:
            if vec.denom != denom:
                raise Exception("ExactVector.stack: can only work with vectors sharing the same denom.")
            noms += [vec.noms]
        noms = tuple(noms)
        return FracVector(noms, denom)
    
    @classmethod
    def from_tuple(cls, t):
        """Return a FracVector created from the tuple representation: (denom, ...noms...), returned by the to_tuple() method."""
        return FracVector(t[0], t[1:])

    @classmethod
    def from_floats(cls, l, resolution=2 ** 32):
        """
        Create a FracVector from a (nested) list or tuple of floats. If you want to 
        convert a numpy array A, use A.tolist()
        
        resolution = the resolution used for interpreting the given floating point numbers. Default is 2^32.
        """

        eps = (1.0 / resolution) * 0.1

        gcd = nested_reduce(lambda x, y: fractions.gcd(x, abs(int((y + eps) * resolution))), l, initializer=resolution)
        noms = nested_map(lambda x: int((x + eps) * resolution) // gcd, l)
        denom = resolution / gcd

        return FracVector(noms, denom)
    
    #### Properties

    @property
    def dim(self):
        """ This propery returns a tuple with the dimensionality of each dimension of the FracVector (the noms are assumed to be a nested list of rectangular shape)."""
        #if self._dim == None:            
        #    self._dim = tuple_dim(self.noms)
        #return self._dim
        if self._dim == None:   
            dimchk = self.noms
            self._dim = ()
            while True:
                try:
                    d = len(dimchk)
                except TypeError:
                    break
                if d > 0:
                    self._dim += (d,)
                    dimchk = dimchk[0]
                else:
                    break
        return self._dim


    @property
    def nom(self):
        """ Returns the integer nominator of a scalar FracVector."""
        if self.dim != ():
            raise Exception("FracVector.nom: attempt to access scalar nominator on non-scalar FracVector.")
        return self.noms
    
    #### Methods
    
    def to_tuple(self):
        """Return a FracVector on tuple representation: (denom, ...noms...)."""
        return (self.denom, self.noms)
        
    def to_floats(self):
        """
        Converts the ExactVector to a list of floats.
        """
        denom = float(self.denom)
        return nested_map(lambda x: float(x) / denom, self.noms)

    def to_float(self):
        """
        Converts a scalar ExactVector to a single float.
        """
        try:
            return float(self.nom) / float(self.denom)
        except OverflowError:
            return float(fractions.Fraction(self.nom/self.denom))            

    def to_fractions(self):
        """
        Converts the FracVector to a list of fractions.
        """
        return nested_map(lambda x: fractions.Fraction(x, self.denom), self.noms)

    def to_fraction(self):
        """
        Converts scalar FracVector to a fraction.
        """
        return fractions.Fraction(self.nom, self.denom)

    def flatten(self):
        """
        Returns a FracVector that has been flattened out to a single rowvector
        """
        noms = nested_reduce(lambda x,y: x + [y],self.noms, initializer=[])        
        return FracVector(tuple(noms), self.denom)

    @classmethod
    def set_common_denom(cls, A, B):
        """
        Returns a tuple (A2,B2,denom) where A2 is equal to A, and B2 is equal to B, but A2 and B2 are both set on the same shared denominator 'denom' which
        is the product of the denominator of A and B.        
        """

        if not isinstance(A, FracVector):
            A = FracVector(A, 1)

        if not isinstance(B, FracVector):
            B = FracVector(B, 1)

        denom = A.denom * B.denom
        mA = B.denom
        mB = A.denom

        Anoms = A._map_over_noms(lambda x: x * mA)
        Bnoms = B._map_over_noms(lambda x: x * mB)
        
        return FracVector(Anoms, denom), FracVector(Bnoms, denom), denom

    def sign(self):
        """ Returns the sign of the scalar FracVector."""
        if self.dim != ():
            raise Exception("FracVector.nom: attempt to access scalar nominator on non-scalar FracVector.")
        if self.noms < 0:
            return -1
        else:
            return 1

    def T(self):
        """
        Returns the transpose, A^T.
        """
        dim = self.dim
        if len(dim) == 0:
            return FracVector(self.noms, self.denom)
        elif len(dim) == 1:
            noms = tuple((self.noms[col],) for col in range(dim[0]))
            return FracVector(noms, self.denom)
        elif len(dim) == 2:
            noms = tuple(tuple(self.noms[col][row] for col in range(dim[0])) for row in range(dim[1]))
            return FracVector(noms, self.denom)
        raise Exception("FracVector.T(): on non 1 or 2 dimensional object not implemented")

    def det(self):
        """
        Returns the determinant as a scalar FracVector.
        """
        dim = self.dim
        if dim == (3, 3):
            A = self.noms
            noms = A[0][0] * A[1][1] * A[2][2] + A[0][1] * A[1][2] * A[2][0] + A[0][2] * A[1][0] * A[2][1] - A[0][2] * A[1][1] * A[2][0] - A[0][1] * A[1][0] * A[2][2] - A[0][0] * A[1][2] * A[2][1]
            return FracVector(noms, self.denom ** 3)
        elif dim == (4, 4):
            A = self.noms
            noms = \
              A[0][0] * A[1][1] * A[2][2] * A[3][3] + A[0][0] * A[2][1] * A[3][2] * A[1][3] + A[0][0] * A[3][1] * A[1][2] * A[2][3] \
            + A[1][0] * A[0][1] * A[3][2] * A[2][3] + A[1][0] * A[2][1] * A[0][2] * A[3][3] + A[1][0] * A[3][1] * A[2][2] * A[0][3] \
            + A[2][0] * A[0][1] * A[1][2] * A[3][3] + A[2][0] * A[1][1] * A[3][2] * A[0][3] + A[2][0] * A[3][1] * A[0][2] * A[1][3] \
            + A[3][0] * A[0][1] * A[2][2] * A[1][3] + A[3][0] * A[1][1] * A[0][2] * A[2][3] + A[3][0] * A[2][1] * A[1][2] * A[0][3] \
            - A[0][0] * A[1][1] * A[3][2] * A[2][3] - A[0][0] * A[2][1] * A[1][2] * A[3][3] - A[0][0] * A[3][1] * A[2][2] * A[1][3] \
            - A[1][0] * A[0][1] * A[2][2] * A[3][3] - A[1][0] * A[2][1] * A[3][2] * A[0][3] - A[1][0] * A[3][1] * A[0][2] * A[2][3] \
            - A[2][0] * A[0][1] * A[3][2] * A[1][3] - A[2][0] * A[1][1] * A[0][2] * A[3][3] - A[2][0] * A[3][1] * A[1][2] * A[0][3] \
            - A[3][0] * A[0][1] * A[1][2] * A[2][3] - A[3][0] * A[1][1] * A[2][2] * A[0][3] - A[3][0] * A[2][1] * A[0][2] * A[1][3] 
            return FracVector(noms, self.denom ** 4)

        raise Exception("FracVector.det: on non 3x3 or 4x4 matrix not implemented")

    def inv(self):
        """
        Returns the matrix inverse, A^-1
        """
        dim = self.dim        
        if dim == ():
            return FracVector(self.denom, self.nom)
        
        if dim != (3, 3):
            raise Exception("FracVector.inv: only scalar and 3x3 matrix implemented")

        # We are dividing with a determinant giving self.denom**3 in nominator, and 
        # from the matrix 1/self.denom**2 falls out => one factor of self.denom in nominator 

        det = self.det()
        det_nom = det.nom

        if det_nom == 0:
            raise Exception("ExactVector.inverse: cannot take inverse of singular matrix.")
        
        if det_nom < 0:
            denom = -det_nom
            m = -self.denom
        else:
            denom = det_nom
            m = self.denom
            
        A = self.noms
        noms = ((m * (A[1][1] * A[2][2] - A[1][2] * A[2][1]), m * (A[0][2] * A[2][1] - A[0][1] * A[2][2]), m * (A[0][1] * A[1][2] - A[0][2] * A[1][1])),
                   (m * (A[1][2] * A[2][0] - A[1][0] * A[2][2]), m * (A[0][0] * A[2][2] - A[0][2] * A[2][0]), m * (A[0][2] * A[1][0] - A[0][0] * A[1][2])),
                   (m * (A[1][0] * A[2][1] - A[1][1] * A[2][0]), m * (A[0][1] * A[2][0] - A[0][0] * A[2][1]), m * (A[0][0] * A[1][1] - A[0][1] * A[1][0])))                    
            
        return FracVector(noms, denom)

    def simplify(self):
        """
        Returns a reduced FracVector. I.e., each element has the same numerical value 
        but the new FracVector represents them using the smallest possible shared denominator.
        """
        noms = self.noms
        denom = self.denom

        if self.denom != 1:
            gcd = self._reduce_over_noms(lambda x, y: fractions.gcd(x, abs(y)), initializer=self.denom)
            if gcd != 1:
                denom = denom / gcd
                noms = self._map_over_noms(lambda x:int(x / gcd))
            else:
                noms = self._map_over_noms(lambda x:int(x))
        else:
            noms = self._map_over_noms(lambda x:int(x))
            
        return FracVector(noms, denom)

    def limit_resolution(self, resolution):
        """
        Returns a FracVector of reduced resolution.
        
          resolution is the new denominator, each element in the returned FracVector is the closest numerical approximation using this denominator.
        """
        denom = self.denom
        def limit_resolution_one(x):
            low = (x * resolution) // denom
            if x * resolution * 2 > (low * 2 + 1) * denom:
                return low + 1
            else:
                return low
        
        noms = self._map_over_noms(limit_resolution_one)        
        return FracVector(noms, resolution)  

    def floor(self):
        """
        Returns the integer that is equal to or just below the value stored in a scalar FracVector.
        """
        if self.dim != ():
            raise Exception("FracVector.floor: Needs scalar FracVector")
        # Python integer division really does floor, even for negative numbers
        return self.nom // self.denom

    def ceil(self):
        """
        Returns the integer that is equal to or just below the value stored in a scalar FracVector.
        """
        if self.dim != ():
            raise Exception("FracVector.ceil: Needs scalar FracVector")
        if self.nom % self.denom == 0:            
            return self.nom // self.denom
        else:
            return self.nom // self.denom + 1

    def normalize(self):
        """
        Add/remove an integer +/-N to each element to place it in the range [0,1)
        """
        noms = self._map_over_noms(lambda x:x - self.denom * (x // self.denom))
        return FracVector(noms, self.denom)        

    def normalize_half(self):
        """
        Add/remove an integer +/-N to each element to place it in the range [-1/2,1/2)
        
        This is useful to find the shortest vector C between two points A, B in a space with periodic boundary conditions [0,1):
           C = (A-B).normalize_half()
        """
        noms = self._map_over_noms(lambda x:2 * x - (2 * self.denom) * ((((2 * x) // self.denom) + 1) // 2))
        return FracVector(noms, 2 * self.denom)

    def mul(self, other):
        """
        Returns the result of multiplying the vector with 'other' using matrix multiplication. 
        
        Note that for two 1D FracVectors, A.mul(B) is not the same as A.dot(B), but rather, A.mul(B.T()) is. 
        """
        # Handle other being another object  
        if not isinstance(other, FracVector):
            other = FracVector.create(other)
               
        Adim = self.dim
        Bdim = other.dim
        A = self.noms
        B = other.noms    
        denom = self.denom * other.denom

        # Other is scalar
        if Bdim == ():
            m = other.nom
            noms = self._map_over_noms(lambda x: x * m)
        
        # Self is scalar
        elif Adim == ():
            m = self.nom
            noms = other._map_over_noms(lambda x: x * m)

        # Vector * Vector
        elif len(Adim) == 1 and len(Bdim) == 1:
            if Adim[0] != Bdim[0]:
                raise Exception("ExactVector.dot: vector multiplication dimension mismatch," + str(Adim) + " and " + str(Bdim))
            noms = tuple(A[i] * B[i] for i in range(Adim[0]))            

        # Matrix * vector 
        elif len(Adim) == 2 and len(Bdim) == 1:
            if Adim[1] != Bdim[0]:
                raise Exception("ExactVector.dot: matrix multiplication dimension mismatch," + str(Adim) + " and " + str(Bdim))                
            noms = tuple(sum([A[row][i] * B[i] for i in range(Adim[1])]) for row in range(Adim[0]))

        # vector * Matrix    
        elif len(Adim) == 1 and len(Bdim) == 2:
            if Adim[0] != Bdim[0]:
                raise Exception("ExactVector.dot: matrix multiplication dimension mismatch," + str(Adim) + " and " + str(Bdim))                
            noms = tuple(sum([A[i] * B[i][col] for i in range(Adim[0])]) for col in range(Bdim[1]))

        # Matrix * Matrix
        elif len(Adim) == 2 and len(Bdim) == 2:
            if Adim[1] != Bdim[0]:
                raise Exception("ExactVector.dot: matrix multiplication dimension mismatch," + str(Adim) + " and " + str(Bdim))                
            noms = tuple(tuple(sum([A[row][i] * B[i][col] for i in range(Adim[1])]) for col in range(Bdim[1]))
                      for row in range(Adim[0]))

        else:
            raise Exception("ExactVector.dot: cannot handle tensors of order > 2, dimensions:" + str(Adim) + " and " + str(Bdim))

        return FracVector(noms, denom)

    def dot(self, other):
        """
        Returns the vector dot product of the 1D vector with the 1D vector 'other', i.e., A . B or A \cdot B. The same as A * B.T(). 
        """
        Adim = self.dim
        Bdim = other.dim
        A = self.noms
        B = other.noms    
        denom = self.denom * other.denom

        if len(Adim) == 1 and len(Bdim) == 1:
            if Adim[0] != Bdim[0]:
                raise Exception("ExactVector.dot: vector multiplication dimension mismatch," + str(Adim) + " and " + str(Bdim))
            noms = sum(A[i] * B[i] for i in range(Adim[0]))       
        else:
            raise Exception("ExactVector.dot: dot multiplication dimensions not = 1," + str(Adim) + " and " + str(Bdim))
        return FracVector(noms, denom)

    def lengthsqr(self):
        """
        Returns the square of the length of the vector. The same as A * A.T()
        """
        # Other is scalar
        dim = self.dim
        
        if dim == ():
            noms = self.noms ** 2
        elif len(self.dim) == 1:
            noms = sum(self.noms[i] ** 2 for i in range(self.dim[0]))       
        else:
            raise Exception("ExactVector.lengthsqr: vector must be scalar or dimension must be = 1, is " + str(self.dim))
        return FracVector(noms, self.denom ** 2)

    def cross(self, other):
        """
        Returns the vector cross product of the 3-element 1D vector with the 3-element 1D vector 'other', i.e., A x B.
        """
        # Note: multiplication is an especially simple case, there is no need to bring the two vectors into a
        # common denom with common_denom, since a/b * c/d = a*c/(b*d)        
        Adim = self.dim
        A = self.noms
        Bdim = other.dim
        B = other.noms    
        denom = self.denom * other.denom
        if Adim != (3,) or Bdim != (3,):
            raise Exception("FracVector.cross: can only do cross products of 3-element 1D vectors. The dimensions are:" + str(Adim) + " and " + str(Bdim))
        
        noms = ((A[1] * B[2] - A[2] * B[1]), (A[2] * B[0] - A[0] * B[2]), (A[0] * B[1] - A[1] * B[0]))
        
        return FracVector(noms, denom)

    def metric_product(self, vecA, vecB):
        """
        Returns the result of the metric product using the present square FracVector as the metric matrix. The same as
          vecA*self*vecB.T().
        """
 
        dimM = self.dim
        dimA = vecA.dim
        dimB = vecB.dim

        M = self.noms
        A = vecA.noms
        B = vecB.noms

        denom = vecA.denom * vecB.denom * self.denom

        l = dimM[0]

        if dimA != dimB or dimM != (l, l) or ((len(dimA) != 1 or len(dimB) != 1) and (dimA[1] != l or dimB[1] != l)):
            raise Exception("ExactVector.metric_product: vectors not in right dimensions.")
                
        if len(dimA) == 1: 
            noms = sum([A[row] * M[row][col] * B[col] for row in range(l) for col in range(l)])
        else:
            # Matrix * Matrix
            noms = [sum([A[i][row] * M[row][col] * B[i][col] for row in range(l) for col in range(l)]) for i in range(dimA[0])]

        return FracVector(noms, denom)   

    #### System methods
    def __getitem__(self, key):
        if not isinstance(key, tuple):
            key = (key,)
        noms = list_slice(self.noms, key)
        return FracVector(noms, self.denom)

    def __setitem__(self, key, values):
        raise Exception("FracVector is immutable")

    def __len__(self):
        return len(self.noms)

    def __iter__(self):
        try:
            for i in range(len(self.noms)):
                yield FracVector(self.noms[i], self.denom)
        except GeneratorExit:
            pass

    def __mul__(self, other):
        return self.mul(other)

    def __div__(self, other):
        if not isinstance(other, FracVector):
            frac = FracVector(1, other)
        else:
            frac = FracVector(other.denom,other.nom)
        return self.mul(frac)
    
    def __add__(self, other):
        noms, denom = self._map_binary_op_over_noms(operator.add, other)
        return FracVector(noms, denom)

    def __sub__(self, other):
        noms, denom = self._map_binary_op_over_noms(operator.sub, other)
        return FracVector(noms, denom)
        
    def __repr__(self):
        return "FracVector(" + repr(self.noms) + "," + repr(self.denom) + ")"

    def __str__(self):
        return "(1/" + str(self.denom) + ")*" + str(self.noms)

    def __hash__(self):
        return (self.denom, self.noms).__hash__() 

    @property
    def hexhash(self):
        if self._hexhash == None:
            self._hexhash = tuple_to_hexhash(self.to_tuple())
        return self._hexhash
    
    def __neg__(self):
        return FracVector(self._map_over_noms(operator.neg), self.denom)

    def __abs__(self):
        return FracVector(self._map_over_noms(operator.abs), self.denom)
    
    def __eq__(self, other):
        """
        The == operator between FracVectors tests for numerical equality. (I.e., numerically equal FracVectors with different denoms are still equal.)
        """
        # Note: somewhat optimized for speed
        try:
            if self.denom == other.denom:
                return (self.noms == other.noms)
            else:
                (A,B,denom) = self.set_common_denom(self,other)
                return (A.noms == B.noms)
        except AttributeError:                
            if other == None:
                return False

            if not isinstance(other, FracVector):
                other = FracVector.create(other)
        
            if other.dim != self.dim:
                return False
        
        if self.denom == other.denom:
            return (self.noms == other.noms)
        else:
            (A,B,denom) = self.set_common_denom(self,other)
            return (A.noms == B.noms)
        

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        try:
            return self.nom * other.denom < other.nom * self.denom
        except AttributeError:
            return self.nom < other * self.denom
        #if not isinstance(other, FracVector):
        #    other = FracVector.create(other)

    def __gt__(self, other):
        #if not isinstance(other, FracVector):
        #    other = FracVector.create(other)
        try:            
            return self.nom * other.denom > other.nom * self.denom
        except AttributeError:
            return self.nom > other * self.denom
        
    def __le__(self, other):           
        return not self.__gt__(other)
        
    def __ge__(self, other):
        return not self.__lt__(other)

    def __float__(self):
        try:
            return float(self.nom) / float(self.denom)
        except OverflowError:
            return float(fractions.Fraction(self.nom,self.denom))

    def __int__(self):
        return self.nom // self.denom

    def __long__(self):
        return self.nom // self.denom

    def __index__(self):
        v = self.simplify()
        if v.denom != 1:
            raise Exception("FracVector.__index__: cannot index with non-integer value.")
        return v.nom

    def __complex__(self):
        return complex(self.__float__())
                
    #### Private methods

    def _map_over_noms(self, op, *others):
        """Map an operation over all nominators"""
        othernoms = [x.noms for x in others]
        if isinstance(self.noms, tuple):
            return nested_map(op, self.noms, *othernoms)
        else:
            return op(self.noms, *othernoms)

    def _map_binary_op_over_noms(self, op, other):
        """Put self and other on common denominator form, and then map a binary operator
           over pairs of nominators, handling the cases where either of the operands is 
           a scalar (thus pairing it with every nominator)
        """

        A, B, denom = self.set_common_denom(self, other)
        
        Adim = A.dim
        Bdim = B.dim

        if len(Adim) == 0:
            if len(Bdim) == 0:
                # scalar [op] scalar
                result = op(A.nom, B.nom)
            else:
                # scalar [op] (Matrix or Vector)
                result = B._map_over_noms(lambda x:op(A.nom, x))            
        elif len(Bdim) == 0:
            # [Matrix or Vector] op scalar
            result = A._map_over_noms(lambda x:op(B.nom, x))
        else:
            # Matrix op Matrix
            result = A._map_over_noms(lambda x, y: op(x, y), B)

        return (result, denom)        


    def _reduce_over_noms(self, op, initializer=None):
        """Run a nested reduce operation over all nominators"""
        return nested_reduce(op, self.noms, initializer=initializer)
    
                
#### Utility functions
            
#def nested_map_slower(op, *ls):
#    try:
#        ls[0][0][0]
#        return tuple(map(lambda *items: nested_map(op, *items), *ls))
#    except TypeError:
#        try:
#            ls[0][0]
#            return tuple(map(op, *ls))
#        except TypeError:
#            return op(*ls)
                      
def nested_map(op, *ls):
    if isinstance(ls[0], (tuple, list)):
        if len(ls[0]) == 0 or not isinstance(ls[0][0], (tuple, list)):
            return tuple(map(op, *ls))
        return tuple(map(lambda *items: nested_map(op, *items), *ls))
    return op(*ls)

def nested_map_fractions(op, *ls):
    if hasattr(ls[0], 'to_fractions'):
        ls = list(ls)
        ls[0] = ls[0].to_fractions()
    if not isinstance(ls[0],basestring):
        try:
            dummy = iter(ls[0])
            return tuple(map(lambda *items: nested_map_fractions(op, *items), *ls))
        except TypeError:
            pass
    return op(*ls)

def nested_reduce(op, l, initializer=None):
    if isinstance(l, (tuple, list)):
        return reduce(lambda x, y: nested_reduce(op, y, initializer=x), l, initializer)
    else:
        return op(initializer, l)

def nested_reduce_fractions(op, l, initializer=None):
    if hasattr(l, 'to_fractions'):
        l = l.to_fractions()
    if not isinstance(l,basestring):
        try:
            dummy = iter(l)
            return reduce(lambda x, y: nested_reduce_fractions(op, y, initializer=x), l, initializer)
        except TypeError:
            pass
    return op(initializer, l)

def list_slice(l, key):    
    if isinstance(key[0], (int, long, slice)):
        slicedlist = l[key[0]]
    else: 
        slicedlist = tuple([ l[i] for i in key[0]])
    cdr = key[1:]
    if len(cdr) > 0:
        if isinstance(key[0], slice):
            return tuple(list_slice(slicedlist[i], cdr) for i in range(len(slicedlist)))
        else:
            return list_slice(slicedlist, cdr)
    return slicedlist

#def tuple_dim(l):
#    """Returns the dimension Of a nested tuple"""
#    try:
#        dim = (len(l),)
#    except TypeError:
#        return ()
#    if dim[0] > 0:
#        dim += tuple_dim(l[0])
#    return dim

    