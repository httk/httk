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

import sys, fractions, random, operator, itertools, decimal
from functools import reduce
from fracmath import *
from vector import Vector

# Utility functions needed before defining the class (due to some of them being statically assigned)


def nested_map_tuple(op, *ls):
    """
    Map an operator over a nested tuple. (i.e., the same as the built-in map(), but works recursively on a nested tuple)
    """
    if isinstance(ls[0], (tuple, list)):
        if len(ls[0]) == 0 or not isinstance(ls[0][0], (tuple, list)):
            return tuple(map(op, *ls))
        return tuple(map(lambda *items: nested_map_tuple(op, *items), *ls))
    return op(*ls)


def nested_map_fractions_tuple(op, *ls):
    """
    Map an operator over a nested tuple, but checks every element for a method to_fractions() 
    and uses this to further convert objects into tuples of Fraction. 
    """
    if hasattr(ls[0], 'to_fractions'):
        ls = list(ls)
        ls[0] = ls[0].to_fractions()
    if not isinstance(ls[0], basestring):
        try:
            dummy = iter(ls[0])
        except TypeError:
            dummy = None
            pass
        if dummy is not None:
            return tuple(map(lambda *items: nested_map_fractions_tuple(op, *items), *ls))
    return op(*ls)


# Class definition
class FracVector(Vector):
    """
    FracVector is a general *immutable* N-dimensional vector (tensor) class for performing linear algebra with fractional numbers. 
    
    A FracVector consists of a multidimensional tuple of integer nominators, and a single shared integer denominator.
    
    Since FracVectors are immutable, every operation on a FracVector returns a new FracVector with the result of the operation. 
    A created FracVector never changes. Hence, they are safe to use as keys in dictionaries, to use in sets, etc.

    Note: most methods returns FracVector results that are not simplified (i.e., the FracVector returned does *not* have
    the smallest possible integer denominator). To return a FracVector with the smallest possible denominator, just call 
    FracVector.simplify() at the last step.
    """

    #### Static methods to overload in subclasses

    # a map-type function that handles nested sequences
    nested_map = staticmethod(nested_map_tuple)
    # a map-type function that handles nested sequences and objects that can be converted into fractions 
    nested_map_fractions = staticmethod(nested_map_fractions_tuple)
    # a method used to copy the nominator sequence
    _dup_noms = staticmethod(tuple)

    #### Creation

    def __init__(self, noms, denom=1):
        """
        Low overhead constructor.
        
        noms: nested *tuples* (may not be lists!) of nominator integers
        denom: integer denominator
        
        Represents the tensor (1/denom)*(noms)
        
        If you want to create a FracVector from something else than tuples, use the FracVector.create() method.
        """
        self.noms = noms
        self.denom = denom
        self._dim = None

    @classmethod
    def use(cls, old):
        """
        Make sure variable is a FracVector, and if not, convert it.
        """
        if isinstance(old, FracVector):
            return old
        else:
            try:
                fracvec = old.to_FracVector()
                return cls.__init__(fracvec.noms, fracvec.denom)        
            except Exception:
                pass
            
            return cls.create(old) 

    @classmethod
    def create(cls, noms, denom=None, simplify=True, chain=False, min_accuracy=fractions.Fraction(1,10000)):
        """
        Create a FracVector from various types of sequences.
              
        Simplest use::
        
          FracVector.create(some_kind_of_sequence)
          
        where 'some_kind_of_sequence' can be any nested list or tuple of objects that can be used in the constructor 
        of the Python Fraction class (also works with strings!). If any object found while traveling the items has a 
        .to_fractions() method, it will be called and is expected to return a fraction or list or tuple of fractions.

        Optional parameters:
        
        - Invocation with denominator: FracVector.create(nominators,denominator)  
          nominators is any sequence, and denominator a common denominator to divide all nominators with
          
        - simplify: boolean, return a FracVector with the smallest possible denominator.

        - chain: boolean, remove outermost dimension and chain the sub-sequences. I.e., if input=[[1 2 3],[4,5,6]], then
          FracVector.create(input) -> [1,2,3,4,5,6]  
       
        Relevant: FracVector itself implements .to_fractions(), and hence, the same constructor allows stacking
        several FracVector objects like this::
        
            vertical_fracvector = FracVector.create([[fracvector1],[fracvector2]])
            horizontal_fracvector = FracVector.create([fracvector1,fracvector2],chain=True)
        
        - min_accuracy: set to a boolean to adjust the minimum accuracy assumed in string input.
          The default is 1/10000, i.e. 0.33 = 0.3300 = 33/100, whereas 0.3333 = 1/3.    
          Set it to None to assume infinite accuracy, i.e., convert exactly whatever string is given 
          (unless a standard deviation is given as a parenthesis after the string.)
        
        """
        def getlcd(a, y):
            b = abs(y).denominator
            return a * b // fractions.gcd(a, b)
        
        def getnumerators(x):
            return (x * lcd).numerator

        fracnoms = cls.nested_map_fractions(lambda x: any_to_fraction(x, min_accuracy=min_accuracy), noms)

        lcd = nested_reduce_fractions(lambda x, y: getlcd(x, y), fracnoms, initializer=1)
        v_noms = cls.nested_map_fractions(lambda x: getnumerators(x), fracnoms)

        if chain:
            v_noms = cls._dup_noms(itertools.chain(*v_noms))

        if denom is None:
            v = cls(v_noms, lcd)
        else:
            v = cls(v_noms, lcd * denom)

        if simplify and v.denom != 1:
            v = v.simplify()

        return v

    # Note, these are different, and thus named different (get_ prefix), than the corresponding methods in a list, since
    # they do not modify the vector itself. 

    def get_append(self, other):
        return self.__class__.create([self, [other]], chain=True)

    def get_extend(self, other):
        return self.__class__.create([self, other], chain=True)

    def get_insert(self, pos, other):
        return self.__class__.create([self[:pos], [other], self[pos:]], chain=True)

    def get_prepend(self, other):
        return self.__class__.create([[other], self], chain=True)

    def get_prextend(self, other):
        return self.__class__.create([other, self], chain=True)

    def get_stacked(self, other):
        return self.__class__.create([self, [other]])

    def ged_prestacked(self, other):
        return self.__class__.create([[other], self])

    def ged_stackedinsert(self, pos, other):
        return self.__class__.create([self[:pos], [other], self[pos:]], chain=True)

    @classmethod
    def chain_vecs(cls, vecs):
        """
        Optimized chaining of FracVectors. 

        vecs: a list (or tuple) of fracvectors.

        Returns the same thing as
           FracVector.create(vecs,chain=True)
        i.e., removes outermost dimension and chain the sub-sequences. If input=[[1 2 3],[4,5,6]], then
          FracVector.chain(input) -> [1,2,3,4,5,6]
        
        but this method assumes all vectors share the same denominator (it raises an exception if this is not true)
        """
        noms = []
        denom = vecs[0].denom
        for vec in vecs:
            if vec.denom != denom:
                raise Exception("ExactVector.merge: can only work with vectors sharing the same denom.")
            noms += vec.noms
        noms = cls._dup_noms(noms)
        return cls(noms, denom)

    @classmethod
    def stack_vecs(cls, vecs):
        """
        Optimized stacking of FracVectors. 
        
        vecs = a list (or tuple) of fracvectors.
        
        Returns the same thing as::

           FracVector.create(vecs)

        but only works if all vectors share the same denominator (raises an exception if this is not true)
        """        
        noms = []
        denom = vecs[0].denom
        for vec in vecs:
            if vec.denom != denom:
                raise Exception("ExactVector.stack: can only work with vectors sharing the same denom.")
            noms += [vec.noms]
        noms = cls._dup_noms(noms)
        return cls(noms, denom)
    
    @classmethod
    def eye(cls, dims):
        """
        Create a diagonal one-matrix with the given dimensions
        """
        return cls.create(tuple_eye(dims))

    @classmethod
    def zeros(cls, dims):
        """
        Create a zero matrix with the given dimensions
        """
        return cls.create(tuple_zeros(dims))

    @classmethod
    def random(cls, dims, minnom=-100, maxnom=100, denom=100):
        """
        Create a zero matrix with the given dimensions
        """
        return cls.create(tuple_random(dims, minval=minnom, maxval=maxnom), denom)
    
    @classmethod
    def from_tuple(cls, t):
        """
        Return a FracVector created from the tuple representation: (denom, ...noms...), returned by the to_tuple() method.
        """
        return cls(t[1:], t[0])

    @classmethod
    def from_floats(cls, l, resolution=2**32):
        """
        Create a FracVector from a (nested) list or tuple of floats. You can convert a numpy array with
        this method if you use A.tolist()
        
        resolution: the resolution used for interpreting the given floating point numbers. Default is 2^32.
        """

        eps = (1.0 / resolution) * 0.1

        gcd = nested_reduce(lambda x, y: fractions.gcd(x, abs(int((y + eps) * resolution))), l, initializer=resolution)
        noms = cls.nested_map(lambda x: int((x + eps) * resolution) // gcd, l)
        denom = resolution / gcd

        return cls(noms, denom)

    @classmethod
    def _create_func(cls, data, func, find_best_rational = True, **args):
        def apply_func(arg):
            if is_string(arg):
                if find_best_rational:
                    val, delta = string_to_val_and_delta(arg)
                    low = val-delta
                    high = val+delta
                    lowval = func(low, **args)
                    highval = func(high, **args)
                    return best_rational_in_interval(lowval, highval)
                else:
                    val, delta = string_to_val_and_delta(arg)
                    if 'prec' in args:
                        low = val-fractions.Fraction(args['prec'])*10
                        high = val+fractions.Fraction(args['prec'])*10
                    else:
                        low = val-fractions.Fraction(1,100000000000)
                        high = val+fractions.Fraction(1,100000000000)
                    lowval = func(low, **args)
                    highval = func(high, **args)
                    return best_rational_in_interval(lowval, highval)
            else:
                try:
                    return func(arg.to_fraction())
                except Exception:
                    return func(fractions.Fraction(arg))
            
        newdata = nested_map_tuple(apply_func, data)      
        return cls.create(newdata)

    @classmethod
    def create_cos(cls, data, degrees=False, limit=False, find_best_rational=True, prec=fractions.Fraction(1, 1000000)):
        """
        Creating a FracVector as the cosine of the argument data. If data are composed by strings, the standard deviation of
        the numbers are taken into account, and the best possible fractional approximation to the cosines
        of the data are returned within the standard deviation.
        
        This is not the same as FracVector.create(data).cos(), which creates the best possible fractional
        approximations of data and then takes cos on that.
        """
        return cls._create_func(data, frac_cos, find_best_rational = find_best_rational, degrees=degrees, limit=limit, prec=prec)

    @classmethod
    def create_sin(cls, data, degrees=False, limit=False, prec=fractions.Fraction(1, 1000000)):
        """
        Creating a FracVector as the sine of the argument data. If data are composed by strings, the standard deviation of
        the numbers are taken into account, and the best possible fractional approximation to the cosines
        of the data are returned within the standard deviation.
        
        This is not the same as FracVector.create(data).sin(), which creates the best possible fractional
        approximations of data and then takes cos on that.
        """
        return cls._create_func(data, frac_sin, degrees=degrees, limit=limit, prec=prec)

    @classmethod
    def create_exp(cls, data, prec=fractions.Fraction(1, 1000000),limit=False):
        """
        Creating a FracVector as the exponent of the argument data. If data are composed by strings, the standard deviation of
        the numbers are taken into account, and the best possible fractional approximation to the cosines
        of the data are returned within the standard deviation.
        
        This is not the same as FracVector.create(data).exp(), which creates the best possible fractional
        approximations of data and then takes exp on that.
        """
        return cls._create_func(data, frac_exp, limit=limit, prec=prec)

    @classmethod
    def pi(cls, prec=fractions.Fraction(1, 1000000), limit=False):
        """
        Create a scalar FracVector with a rational approximation of pi to precision prec.
        """
        return cls.create(frac_pi(prec,limit=limit))

    
    #### Properties

    @property
    def dim(self):
        """ 
        This property returns a tuple with the dimensionality of each dimension of the FracVector 
        (the noms are assumed to be a nested list of rectangular shape).
        """
        if self._dim is None:
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
        """ 
        Returns the integer nominator of a scalar FracVector.
        """
        if self.dim != ():
            raise Exception("FracVector.nom: attempt to access scalar nominator on non-scalar FracVector:"+str(self))
        return self.noms
    
    #### Methods
        
    def validate(self):
        # TODO: check all dimensions and make sure noms is a square tensor of only tuples
        return True
        
    def to_tuple(self):
        """
        Return a FracVector on tuple representation: (denom, ...noms...).
        """
        return (self.denom, self.noms)
        
    def to_floats(self):
        """
        Converts the ExactVector to a list of floats.
        """
        #denom = float(self.denom)
        #return nested_map_list(lambda x: float(x) / denom, self.noms)
        return nested_map_list(lambda x: float(fractions.Fraction(x, self.denom)), self.noms)

    def to_float(self):
        """
        Converts a scalar ExactVector to a single float.
        """
        #try:
        #    return float(self.nom) / float(self.denom)
        #except OverflowError:
        return float(fractions.Fraction(self.nom, self.denom))

    def to_fractions(self):
        """
        Converts the FracVector to a list of fractions.
        """
        return nested_map_list(lambda x: fractions.Fraction(x, self.denom), self.noms)

    def to_ints(self):
        """
        Converts the FracVector to a list of integers, rounded off as best possible.
        """
        return nested_map_list(lambda x: round(fractions.Fraction(x, self.denom)), self.noms)

    def to_strings(self, accuracy=8):
        """
        Converts the ExactVector to a list of strings.
        """
        #denom = float(self.denom)
        #return nested_map_list(lambda x: float(x) / denom, self.noms)
        #return nested_map_list(lambda x: "%."+str(accuracy)+"f" % (fractions.Fraction(x, self.denom),), self.noms)
        return nested_map_list(lambda x: ("%."+str(accuracy)+"f") % (fractions.Fraction(x, self.denom),), self.noms)

    def to_string(self, accuracy=8):
        """
        Converts the ExactVector to a list of strings.
        """
        #denom = float(self.denom)
        #return nested_map_list(lambda x: float(x) / denom, self.noms)
        return ("%."+str(accuracy)+"f") % (fractions.Fraction(self.nom, self.denom),)

    def to_fraction(self):
        """
        Converts scalar FracVector to a fraction.
        """
        return fractions.Fraction(self.nom, self.denom)

    def to_int(self):
        """
        Converts scalar FracVector to an integer (truncating as necessary).
        """
        #return int(round(fractions.Fraction(self.nom, self.denom))+0.1)
        return int(self)

    def flatten(self):
        """
        Returns a FracVector that has been flattened out to a single rowvector
        """
        noms = nested_reduce(lambda x, y: x + [y], self.noms, initializer=[])        
        return self.__class__(self._dup_noms(noms), self.denom)

    @classmethod
    def set_common_denom(cls, A, B):
        """
        Used internally to combine two different FracVectors.
        
        Returns a tuple (A2,B2,denom) where A2 is numerically equal to A, and B2 is numerically equal to B, but A2 and B2 are both 
        set on the same shared denominator 'denom' which is the *product* of the denominator of A and B.
        """

        if not isinstance(A, FracVector):
            A = cls(A, 1)

        if not isinstance(B, FracVector):
            B = cls(B, 1)

        denom = A.denom * B.denom
        mA = B.denom
        mB = A.denom

        Anoms = A._map_over_noms(lambda x: x * mA)
        Bnoms = B._map_over_noms(lambda x: x * mB)
        
        return cls(Anoms, denom), cls(Bnoms, denom), denom

    def sign(self):
        """ 
        Returns the sign of the scalar FracVector: -1, 0 or 1.
        """
        if self.dim != ():
            raise Exception("FracVector.nom: attempt to access scalar nominator on non-scalar FracVector.")
        if self.noms < 0:
            return -1
        elif self.noms > 0:
            return 1
        else:
            return 0

    def T(self):
        """
        Returns the transpose, A^T.
        """
        dim = self.dim
        if len(dim) == 0:
            return self.__class__(self.noms, self.denom)
        elif len(dim) == 1:
            noms = self._dup_noms((self.noms[col],) for col in range(dim[0]))
            return self.__class__(noms, self.denom)
        elif len(dim) == 2:
            noms = self._dup_noms(self._dup_noms(self.noms[col][row] for col in range(dim[0])) for row in range(dim[1]))
            return self.__class__(noms, self.denom)
        raise Exception("FracVector.T(): on non 1 or 2 dimensional object not implemented")

    def det(self):
        """
        Returns the determinant of the FracVector as a scalar FracVector.
        """
        dim = self.dim
        if dim == (3, 3):
            A = self.noms
            noms = A[0][0] * A[1][1] * A[2][2] + A[0][1] * A[1][2] * A[2][0] + A[0][2] * A[1][0] * A[2][1] - A[0][2] * A[1][1] * A[2][0] - A[0][1] * A[1][0] * A[2][2] - A[0][0] * A[1][2] * A[2][1]
            return self.__class__(noms, self.denom ** 3)
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
            return self.__class__(noms, self.denom ** 4)

        raise Exception("FracVector.det: on non 3x3 or 4x4 matrix not implemented. Matrix was:"+str(dim))

    def inv(self):
        """
        Returns the matrix inverse, A^-1
        """
        dim = self.dim
        if dim == ():
            # For a FracScalar, just swap denominator and nominator
            return self.__class__(self.denom, self.nom)
        
        if dim != (3, 3):
            raise Exception("FracVector.inv: only scalar and 3x3 matrix implemented")

        # We are dividing with a determinant giving self.denom**3 in nominator, and 
        # from the matrix 1/self.denom**2 falls out -> one factor of self.denom in nominator 

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
        noms = self._dup_noms((
            self._dup_noms((m * (A[1][1] * A[2][2] - A[1][2] * A[2][1]), m * (A[0][2] * A[2][1] - A[0][1] * A[2][2]), m * (A[0][1] * A[1][2] - A[0][2] * A[1][1])),),
            self._dup_noms((m * (A[1][2] * A[2][0] - A[1][0] * A[2][2]), m * (A[0][0] * A[2][2] - A[0][2] * A[2][0]), m * (A[0][2] * A[1][0] - A[0][0] * A[1][2])),),
            self._dup_noms((m * (A[1][0] * A[2][1] - A[1][1] * A[2][0]), m * (A[0][1] * A[2][0] - A[0][0] * A[2][1]), m * (A[0][0] * A[1][1] - A[0][1] * A[1][0])),)
        ))
            
        return self.__class__(noms, denom)

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
                noms = self._map_over_noms(lambda x: int(x / gcd))
            
        return self.__class__(noms, denom)

    def set_denominator(self, set_denom=1000000000):
        """
        Returns a FracVector of reduced resolution where every element is the closest numerical approximation using this denominator.
        """
        denom = self.denom
        
        def limit_resolution_one(x):
            low = (x * set_denom) // denom
            if x * set_denom * 2 > (low * 2 + 1) * denom:
                return low + 1
            else:
                return low
        
        noms = self._map_over_noms(limit_resolution_one)
        return self.__class__(noms, set_denom)

    def limit_denominator(self, max_denom=1000000000):
        """
        Returns a FracVector of reduced resolution.
        
        resolution: each element in the returned FracVector is the closest numerical approximation that can is allowed by 
        a fraction with maximally this denominator. Note: since all elements must be put on a common denominator, the result
        may have a larger denominator than max_denom
        """
        denom = self.denom
        newvalues = self._map_over_noms(lambda x: fractions.Fraction(x, denom).limit_denominator(max_denom))
        return self.__class__.create(newvalues)

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
        noms = self._map_over_noms(lambda x: x - self.denom * (x // self.denom))
        return self.__class__(noms, self.denom)

    def normalize_half(self):
        """
        Add/remove an integer +/-N to each element to place it in the range [-1/2,1/2)
        
        This is useful to find the shortest vector C between two points A, B in a space with periodic boundary conditions [0,1):
           C = (A-B).normalize_half()
        """
        noms = self._map_over_noms(lambda x: 2 * x - (2 * self.denom) * ((((2 * x) // self.denom) + 1) // 2))
        return self.__class__(noms, 2 * self.denom)

    def mul(self, other):
        """
        Returns the result of multiplying the vector with 'other' using matrix multiplication. 
        
        Note that for two 1D FracVectors, A.dot(B) is *not* the same as A.mul(B), but rather: A.mul(B.T()). 
        """
        # Handle other being another object
        if not isinstance(other, FracVector):
            other = self.__class__.create(other)
        
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
            noms = self._dup_noms(A[i] * B[i] for i in range(Adim[0]))

        # Matrix * vector 
        elif len(Adim) == 2 and len(Bdim) == 1:
            if Adim[1] != Bdim[0]:
                raise Exception("ExactVector.dot: matrix multiplication dimension mismatch," + str(Adim) + " and " + str(Bdim))
            noms = self._dup_noms(sum([A[row][i] * B[i] for i in range(Adim[1])]) for row in range(Adim[0]))

        # vector * Matrix
        elif len(Adim) == 1 and len(Bdim) == 2:
            if Adim[0] != Bdim[0]:
                raise Exception("ExactVector.dot: matrix multiplication dimension mismatch," + str(Adim) + " and " + str(Bdim))
            noms = self._dup_noms(sum([A[i] * B[i][col] for i in range(Adim[0])]) for col in range(Bdim[1]))

        # Matrix * Matrix
        elif len(Adim) == 2 and len(Bdim) == 2:
            if Adim[1] != Bdim[0]:
                raise Exception("ExactVector.dot: matrix multiplication dimension mismatch," + str(Adim) + " and " + str(Bdim))
            noms = self._dup_noms(self._dup_noms(sum([A[row][i] * B[i][col] for i in range(Adim[1])]) for col in range(Bdim[1]))
                                  for row in range(Adim[0]))

        else:
            raise Exception("ExactVector.dot: cannot handle tensors of order > 2, dimensions:" + str(Adim) + " and " + str(Bdim))

        return self.__class__(noms, denom)

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
        return self.__class__(noms, denom)

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
        return self.__class__(noms, self.denom ** 2)

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
        
        return self.__class__(noms, denom)

    def reciprocal(self):
        dim = self.dim
        if dim != (3, 3):
            raise Exception("FracVector.reciprocal: can only calculate reciprocal matrix for a 3,3 matrix. The dimension are:" + str(dim))
        noms = self.noms

        def det_noms(A):
            return A[0][0] * A[1][1] * A[2][2] + A[0][1] * A[1][2] * A[2][0] + A[0][2] * A[1][0] * A[2][1] - A[0][2] * A[1][1] * A[2][0] - A[0][1] * A[1][0] * A[2][2] - A[0][0] * A[1][2] * A[2][1]
        
        def cross_noms(A, B):
            return ((A[1] * B[2] - A[2] * B[1]), (A[2] * B[0] - A[0] * B[2]), (A[0] * B[1] - A[1] * B[0]))

        detnom = det_noms(noms)
        denom = self.denom
        
        v1, v2, v3 = noms[0], noms[1], noms[2]
        noms = (cross_noms(v2, v3), cross_noms(v1, v3), cross_noms(v1, v2))
        noms = self.nested_map(lambda x: x*denom, noms)
        return self.__class__(noms, detnom)

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

        return self.__class__(noms, denom)

    def cos(self, prec=None, degrees=False, limit=False):
        """Return a FracVector where every element is the cosine of the element in the source FracVector.
    
        prec = precision (should be set as a fraction)
        limit = True requires the denominator to be smaller or equal to precision
        """        
        if prec is not None:
            fracs = self._map_over_noms(lambda nom: frac_cos(fractions.Fraction(nom, self.denom), prec=prec, limit=limit, degrees=degrees))        
        else:
            fracs = self._map_over_noms(lambda nom: frac_cos(fractions.Fraction(nom, self.denom), limit=limit, degrees=degrees))        
        return self.create(fracs)

    def sin(self, prec=None, degrees=False, limit=False):
        """Return a FracVector where every element is the sine of the element in the source FracVector.
    
        prec = precision (should be set as a fraction)
        limit = True requires the denominator to be smaller or equal to precision
        """
        if prec is not None:
            fracs = self._map_over_noms(lambda nom: frac_sin(fractions.Fraction(nom, self.denom), prec=prec, limit=limit, degrees=degrees))
        else:
            fracs = self._map_over_noms(lambda nom: frac_sin(fractions.Fraction(nom, self.denom), limit=limit, degrees=degrees))
        return self.create(fracs)

    def acos(self, prec=None, degrees=False, limit=False):
        """Return a FracVector where every element is the arccos of the element in the source FracVector.
    
        prec = precision (should be set as a fraction)
        limit = True requires the denominator to be smaller or equal to precision
        """        
        if prec is not None:
            fracs = self._map_over_noms(lambda nom: frac_acos(fractions.Fraction(nom, self.denom), prec=prec, limit=limit, degrees=degrees))        
        else:
            fracs = self._map_over_noms(lambda nom: frac_acos(fractions.Fraction(nom, self.denom), limit=limit, degrees=degrees))        
        return self.create(fracs)

    def asin(self, prec=None, degrees=False, limit=False):
        """Return a FracVector where every element is the arcsin of the element in the source FracVector.
    
        prec = precision (should be set as a fraction)
        limit = True requires the denominator to be smaller or equal to precision
        """
        if prec is not None:
            fracs = self._map_over_noms(lambda nom: frac_asin(fractions.Fraction(nom, self.denom), prec=prec, limit=limit, degrees=degrees))
        else:
            fracs = self._map_over_noms(lambda nom: frac_asin(fractions.Fraction(nom, self.denom), limit=limit, degrees=degrees))
        return self.create(fracs)


    def exp(self, prec=None, limit=False):
        """Return a FracVector where every element is the exponent of the element in the source FracVector.
    
        prec = precision (should be set as a fraction)
        limit = True requires the denominator to be smaller or equal to precision
        """
        if prec is not None:
            fracs = self._map_over_noms(lambda nom: frac_exp(fractions.Fraction(nom, self.denom), prec=prec, limit=limit))
        else:
            fracs = self._map_over_noms(lambda nom: frac_exp(fractions.Fraction(nom, self.denom), limit=limit))
        return self.create(fracs)

    def sqrt(self, prec=None, limit=False):
        """Return a FracVector where every element is the sqrt of the element in the source FracVector.
    
        prec = precision (should be set as a fraction)
        limit = True requires the denominator to be smaller or equal to precision
        """
        if prec is not None:
            fracs = self._map_over_noms(lambda nom: frac_sqrt(fractions.Fraction(nom, self.denom), prec=prec, limit=limit))
        else:
            fracs = self._map_over_noms(lambda nom: frac_sqrt(fractions.Fraction(nom, self.denom), limit=limit))
        return self.create(fracs)

    #### Python special overloading

    def __getitem__(self, key):
        if not isinstance(key, tuple):
            key = (key,)
        noms = tuple_slice(self.noms, key)
        return self.__class__(noms, self.denom)

    def __setitem__(self, key, values):
        raise Exception("FracVector is immutable, use MutableFracVector instead.")

    def __len__(self):
        if isinstance(self.noms, (list, tuple)):
            return len(self.noms)
        else:
            return 0

    def __iter__(self):
        try:
            if self.dim != ():
                for i in range(len(self.noms)):
                    yield self.__class__(self.noms[i], self.denom)
            else:
                yield self
        except GeneratorExit:
            pass

    def __mul__(self, other):
        return self.mul(other)

    def __rmul__(self, other):
        other = FracVector.create(other)
        return other.mul(self)

    def __pow__(self, exp):
        if exp == -1:
            return self.inv()
        if self.dim == ():
            if exp == 0:
                return self.__class__(1) 
            if exp > 0:
                return self.__class__(self.nom**exp, self.denom**exp)
            if exp < 0:
                return self.__class__(self.denom**(-exp), self.nom**(-exp))
        if isinstance(exp, (int, long)):
            if exp == 0:
                return self.eye(self.dim)
            if exp > 0:
                a = self
                for _ in range(exp-1):
                    a = a.mul(self)
                return a
            if exp < 0:
                a = self.inv()
                for _ in range(-exp-1):
                    a = a.mul(self)
                return a
        else:
            raise Exception("FracVector.__pow__: I do not know how to exponate a FracVector with "+str(exp))

    def __div__(self, other):
        if not isinstance(other, FracVector):
            other = self.__class__.create(other)
        frac = self.__class__(other.denom, other.nom)
        return self.mul(frac)

    def __truediv__(self, other):
        if not isinstance(other, FracVector):
            other = self.__class__.create(other)
        frac = self.__class__(other.denom, other.nom)
        return self.mul(frac)
    
    def __add__(self, other):
        noms, denom = self._map_binary_op_over_noms(operator.add, other)
        return self.__class__(noms, denom)

    def __radd__(self, other):
        noms, denom = self._map_binary_op_over_noms(operator.add, other)
        return self.__class__(noms, denom)

    def __sub__(self, other):
        noms, denom = self._map_binary_op_over_noms(operator.sub, other)
        return self.__class__(noms, denom)

    def __rsub__(self, other):
        minusself = -self
        noms, denom = minusself._map_binary_op_over_noms(operator.sub, -other)
        return self.__class__(noms, denom)
        
    def __repr__(self):
        return self.__class__.__name__+"(" + repr(self.noms) + "," + repr(self.denom) + ")"

    def __str__(self):
        return "(1/" + str(self.denom) + ")*" + str(self.noms)

    def __hash__(self):
        return (self.denom, self.noms).__hash__() 
    
    def __neg__(self):
        return self.__class__(self._map_over_noms(operator.neg), self.denom)

    def __abs__(self):
        return self.__class__(self._map_over_noms(operator.abs), self.denom)
    
    def __eq__(self, other):
        """
        Important: the == operator between FracVectors tests for numerical equality. (I.e., numerically equal FracVectors 
        with different denoms are still equal.)
        """
        # Note: somewhat optimized for speed
        try:
            if self.denom == other.denom:
                return (self.noms == other.noms)
            else:
                (A, B, _) = self.set_common_denom(self, other)
                return (A.noms == B.noms)
        except AttributeError:
            if other is None:
                return False

            if not isinstance(other, FracVector):
                other = self.__class__.create(other)
        
            if other.dim != self.dim:
                return False
        
        if self.denom == other.denom:
            return (self.noms == other.noms)
        else:
            (A, B, _) = self.set_common_denom(self, other)
            return (A.noms == B.noms)
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        try:
            return self.nom * other.denom < other.nom * self.denom
        except AttributeError:
            return self.nom < other * self.denom

    def __gt__(self, other):
        try:            
            return self.nom * other.denom > other.nom * self.denom
        except AttributeError:
            return self.nom > other * self.denom
        
    def __le__(self, other):
        return not self.__gt__(other)
    
    def __ge__(self, other):
        return not self.__lt__(other)

    def __float__(self):
        # This way of converting avoids many possible overflow errors
        return float(fractions.Fraction(self.nom, self.denom))

    def __int__(self):
        #return self.nom // self.denom
        return int(fractions.Fraction(self.nom, self.denom))

    def __long__(self):
        return long(fractions.Fraction(self.nom, self.denom))
        #return self.nom // self.denom

    def __index__(self):
        v = self.simplify()
        if v.denom != 1:
            raise Exception("FracVector.__index__: cannot index with non-integer value.")
        return v.nom

    def __complex__(self):
        return complex(self.__float__())

    def max(self):
        """
        Return the maximum element across all dimensions in the FracVector. max(fracvector) works for a 1D vector.
        """
        #largest_nom = nested_reduce(lambda x,y:x if x>y else y,self.noms)
        #return self.__class__(largest_nom,self.denom)
        return max(self.flatten())

    def nargmax(self):
        """
        Return a list of indices of all maximum elements across all dimensions in the FracVector.
        """
        
        idt = tuple_index(self.dim)
        maxval = self.max()
        indices = nested_reduce_levels(lambda x, y: x+[y] if self[y] == maxval else x, idt, len(self.dim), [])
        return indices

    def argmax(self):
        """
        Return the index of the maximum element across all dimensions in the FracVector.
        """
        idt = tuple_index(self.dim)
        flat_idt = nested_reduce_levels(lambda x, y: x + [y], idt, len(self.dim), initializer=[])        
        return max(flat_idt, key=lambda i: self[i])

    def min(self):
        """
        Return the minimum element across all dimensions in the FracVector. max(fracvector) works for a 1D vector.
        """
        #smallest_nom = nested_reduce(lambda x,y:x if x<y else y,self.noms)
        #return self.__class__(smallest_nom,self.denom)

        return min(self.flatten())

    def nargmin(self):
        """
        Return a list of indices for all minimum elements across all dimensions in the FracVector.
        """
        idt = tuple_index(self.dim)
        minval = self.min()
        indices = nested_reduce_levels(lambda x, y: x+[y] if self[y] == minval else x, idt, len(self.dim), [])
        return indices
    
    def argmin(self):
        """
        Return the index of the minimum element across all dimensions in the FracVector.
        """
        idt = tuple_index(self.dim)
        flat_idt = nested_reduce_levels(lambda x, y: x + [y], idt, len(self.dim), initializer=[])        
        return min(flat_idt, key=lambda i: self[i])
                
    #### Private methods

    def _map_over_noms(self, op, *others):
        """
        Map an operation over all nominators
        """
        othernoms = [x.noms for x in others]
        if isinstance(self.noms, (tuple, list)):
            return self.nested_map(op, self.noms, *othernoms)
        else:
            return op(self.noms, *othernoms)

    def _map_binary_op_over_noms(self, op, other):
        """
        Put self and other on common denominator form, and then map a binary operator
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
                result = B._map_over_noms(lambda x: op(A.nom, x))
        elif len(Bdim) == 0:
            # [Matrix or Vector] op scalar
            result = A._map_over_noms(lambda x: op(x, B.nom))
        else:
            # Matrix op Matrix
            result = A._map_over_noms(lambda x, y: op(x, y), B)

        return (result, denom)

    def _reduce_over_noms(self, op, initializer=None):
        """
        Run a nested reduce operation over all nominators
        """
        return nested_reduce(op, self.noms, initializer=initializer)
    
    
class FracScalar(FracVector):

    """
    Represents the fractional number nom/denom. This is a subclass of FracVector with the purpose of making 
    it clear when a scalar fracvector is needed/used.
    """     
    
    def __init__(self, nom, denom):
        """ 
        Low overhead constructor.
        
        nom: nominator (int)
        denom: denominator (int)
                
        If you want to create a FracNumber from something else than integers, use the FracScalar.create() method.
        """
        self.noms = nom
        self.denom = denom
        self._dim = ()

    @classmethod
    def create(cls, nom, denom=None, simplify=True):
        """
        Create a FracScalar.
              
        FracScalar(something)
          something may be any object that can be used in the constructor of the Python Fraction class
          (also works with strings!). 
        """
        def lcd(a, y):
            try:
                b = abs(fractions.Fraction(y)).denominator
            except TypeError:
                b = abs(fractions.Fraction(str(y))).denominator
            return a * b // fractions.gcd(a, b)
        
        def frac(x):
            return (fractions.Fraction(x) * lcd).numerator

        lcd = nested_reduce_fractions(lambda x, y: lcd(x, y), nom, initializer=1)
        v_noms = cls.nested_map_fractions(lambda x: frac(x), nom)

        if denom is None:
            v = cls(v_noms, lcd)
        else:
            v = cls(v_noms, lcd * denom)

        if simplify and v.denom != 1:
            v = v.simplify()

        return v

# Utility functions


def nested_map_list(op, *ls):
    """
    Map an operator over a nested list. (i.e., the same as the built-in map(), but works recursively on a nested list)
    """
    if isinstance(ls[0], (tuple, list)):
        if len(ls[0]) == 0 or not isinstance(ls[0][0], (tuple, list)):
            return list(map(op, *ls))
        return list(map(lambda *items: nested_map_list(op, *items), *ls))
    return op(*ls)


def nested_map_fractions_list(op, *ls):
    """
    Map an operator over a nested list, but checks every element for a method to_fractions() 
    and uses this to further convert objects into lists of Fraction. 
    """
    if hasattr(ls[0], 'to_fractions'):
        ls = list(ls)
        ls[0] = ls[0].to_fractions()
    if not isinstance(ls[0], basestring):
        try:
            dummy = iter(ls[0])
            return list(map(lambda *items: nested_map_fractions_list(op, *items), *ls))
        except TypeError:
            pass
    return op(*ls)


def nested_reduce(op, l, initializer=None):
    """
    Same as built-in reduce, but operates on a nested tuple/list/sequence.
    """
    if isinstance(l, (tuple, list)):
        return reduce(lambda x, y: nested_reduce(op, y, initializer=x), l, initializer)
    else:
        return op(initializer, l)


def nested_reduce_levels(op, l, level=1, initializer=None):
    """
    Same as built-in reduce, but operates on a nested tuple/list/sequence.
    """
    if level == 1:
        return reduce(op, l, initializer)
    if isinstance(l, (tuple, list)):
        return reduce(lambda x, y: nested_reduce_levels(op, y, level-1, initializer=x), l, initializer)
    else:
        return op(initializer, l)


def nested_reduce_fractions(op, l, initializer=None):
    """
    Same as built-in reduce, but operates on a nested tuple/list/sequence. Also checks every element
    for a method to_fractions() and uses this to further convert such elements to lists of fractions.
    """
    if hasattr(l, 'to_fractions'):
        l = l.to_fractions()
    if not isinstance(l, basestring):
        try:
            dummy = iter(l)
            return reduce(lambda x, y: nested_reduce_fractions(op, y, initializer=x), l, initializer)
        except TypeError:
            pass
    return op(initializer, l)


def tuple_slice(l, key):
    """
    Given a python slice (i.e., what you get to __getitem__ when you write A[3:2]), cut out the relevant
    nested tuple.
    """
    if isinstance(key[0], (int, long, slice)):
        slicedlist = l[key[0]]
    else: 
        slicedlist = tuple([l[i] for i in key[0]])
    cdr = key[1:]
    if len(cdr) > 0:
        if isinstance(key[0], slice):
            return tuple(tuple_slice(slicedlist[i], cdr) for i in range(len(slicedlist)))
        else:
            return tuple_slice(slicedlist, cdr)
    return slicedlist


def tuple_index(dims, uppidx=()):
        """
        Create a nested tuple where every element is a tuple indicating the position of that tuple
        """
        if dims == ():
            if len(uppidx) == 1:
                return uppidx[0]
            else:
                return uppidx
        else:
            neweye = []
            lastdim = dims[0]
            lowerdims = dims[1:]
            for i in range(lastdim):
                neweye += [tuple_index(lowerdims, uppidx + (i,))]
        return neweye


def tuple_zeros(dims):
        """
        Create a netsted tuple with the given dimensions filled with zeroes
        """
        if dims == ():
            return 0
        else:
            neweye = []
            lastdim = dims[0]
            lowerdims = dims[1:]
            for _ in range(lastdim):
                neweye += [tuple_zeros(lowerdims)]
        return neweye


def tuple_random(dims, minval, maxval):
        """
        Create a nested tuple with the given dimensions filled with random numbers between minval and maxval
        """
        if dims == ():
            return random.randint(minval, maxval)
        else:
            neweye = []
            lastdim = dims[0]
            lowerdims = dims[1:]
            for _ in range(lastdim):
                neweye += [tuple_random(lowerdims, minval, maxval)]
        return neweye


def tuple_eye(dims, onepos=0):
        """
        Create a matrix with the given dimensions and 1 on the diagonal
        """
        if dims == ():
            return 1

        if len(dims) == 1:
            neweye = [0]*dims[0]
            neweye[onepos] = 1
        
        else:
            neweye = []
            lastdim = dims[-1]
            nextdim = dims[-2]
            lowerdims = dims[:-1]
            for i in range(lastdim):
                neweye += [tuple_eye(lowerdims, onepos=(i*nextdim//lastdim))]
        return neweye



# The following copyright notice applies to frac_log, frac_tan, frac_asin, frac_acos, frac_atan2, sinh, cosh, tanh
#
#Copyright (c) 2006 Brian Beck <exogen@gmail.com>,
#                   Christopher Hesse <christopher.hesse@gmail.com>
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.



def main():
    import math
    
    data1 = [['8.04', '0.0', '0.0'], ['0.0', '3.72', '0.0'], ['0.0', '0.0', '7.38']]
    data2 = [[804, 0, 0], [0, 372, 0], [0, 0, 738]]

    fv1 = FracVector.create(data2,100)
    fv2 = FracVector.create(data1)

    print fv1
    
    print fv2
    
    print "===",any_to_fraction('8.04'),any_to_fraction('3.72'),any_to_fraction('7.38')
    data3 = [[fractions.Fraction(185,23), 0, 0], [0, fractions.Fraction(67,18), 0], [0, 0, fractions.Fraction(59,8)]]
    print FracVector.create(data3)
    
    exit(0)
    
    print "PI=",float(frac_pi(prec=fractions.Fraction(1,100000000000))),math.pi
    
    print FracVector.create('120').cos(limit=False, degrees=True)
    print FracVector.create_cos('120',limit=False, degrees=True)
    exit(0)
    
    print "==== Simple things:"
    a = FracVector.create([[2, 7, 5], [3, 5, 4], [4, 6, 7]])
    print a
    print "Max value,", a.max(), "at position:", a.argmax(), "all pos:", a.nargmax()
    print "Min value,", a.min(), "at position:", a.argmin(), "all pos:", a.nargmin()
    print
    b = FracVector([1, 2, 3, 4])
    # NOTE: cannot do b + [5] to append, because that is interpreted as vector addition
    print b.get_append(5)
    print b.argmax()
    print tuple_index((5,))
    print
    
    print list(get_continued_fraction(10, 1333))

    data = 0.33333

    print best_rational_in_interval(data-0.000005, data+0.000005)    

    data = 0.12312

    print best_rational_in_interval(data-0.000005, data+0.000005), 41.0/333

    
    print FracVector.create(["0.33342(10)"])    
    print FracVector.create(["0.33352(10)"])    
    print FracVector.create(["0.33342(10)","0.33352(10)"])    
    print "==="
    print FracVector.create('0.5').cos()
    exit(0)
    print(a)
    print(a.T())
    print(a.inv())
    print a.to_floats()
    print a.zeros((5, 7))
    print a.eye((5, 5))
    print a.eye((5, 7))
    # TODO: Is this right? Need to think about identity tensors of order > 2
    print a.eye((3, 3, 3))
    print
    print "==== Numpy conversion:"
    try:
        import numpy
        x = numpy.array([[2.3, 3.5, 5.3], [3.7, 5.4, 4.2], [4.6, 6.7, 7.4]])
        a = FracVector.create(x)
        print "Original numpy array:", x
        print "FracVector:", a
        print "FracVector as floats:", a.to_floats()
    except ImportError:
        print "(Could not import numpy, numpy tests skipped)"

    print
    print "==== Exact cell transformation example:"
    prim_cell = FracVector.create([[2, 3, 5], [3, 5, 4], [4, 6, 7]], 10)
    print "Primitive cell:", prim_cell
    
    inv = prim_cell.inv().simplify()
    transformation = (inv*inv.denom).simplify()

    print "Integer-only transformation matrix that diagonalize the primitive cell:", transformation

    print "How does this transformation matrix act on the original basis vectors?:"
    result = transformation*prim_cell

    print result
    print "I.e., this transformation matrix gives a perfectly cubic cell in cartesian coordinates of dimensions 3x3x3 Ang^3"

    print
    print "==== Approximate cell transformation example:"
    prim_cell = FracVector.create([[23243253, 32352322, 52343423], [32433242, 52324332, 42343242], [42342342, 62433453, 72432343]], 100000000)
    print "Primitive cell:", prim_cell
    print "Primitive cell in float representation:", prim_cell.to_floats()
    
    inv = prim_cell.inv().simplify()
    transformation = (inv*inv.denom).simplify()

    print "Integer-only transformation matrix that diagonalize the primitive cell:", transformation

    print "How does this transformation matrix act on the original basis vectors?:"
    result = transformation*prim_cell

    print result.to_floats()
    print "I.e., enormous unit cell... Try approximation instead:"
    
    approxinv = prim_cell.inv().set_denominator(10).simplify()
    transformation = (approxinv*approxinv.denom).simplify()
    print "Integer-only transformation matrix that approximately diagonalize the primitive cell:", transformation

    print "How does this transformation matrix act on the original basis vectors?:"
    result = transformation*prim_cell
    print result.to_floats()
    print "I.e., a MOSTLY cubic cell of ~ 10x10x10 Ang^3 comes out."
    

if __name__ == "__main__":
    main()

