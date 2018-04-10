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

import fractions
import operator
import itertools
from fracvector import FracVector, nested_map_list, nested_map_fractions_list, nested_reduce_fractions, nested_reduce
from vector import MutableVector

# Utility functions needed before defining the class (due to them being statically assigned)


def nested_inmap_list(op, *ls):
    """
    Like inmap, but work for nested lists
    """    
    if isinstance(ls[0], (list, tuple)):
        if len(ls[0]) == 0 or not isinstance(ls[0][0], list):
            inmap(op, *ls)
            return
        inmap(lambda *items: nested_map_list(op, *items), *ls)
        return
    raise Exception("nested_inmap_list: called with non-list, not possible to do inmap replacement on scalars:"+str(op)+":"+str(ls))

# Class definition


class MutableFracVector(FracVector, MutableVector):

    """
    Same as FracVector, only, this version allow assignment of elements, e.g., ::

        mfracvec[2,7] = 5

    and, e.g., ::

        mfracvec[:,7] = [1,2,3,4] 

    Other than this, the FracVector methods exist and do the same, i.e., they return *copies* of the fracvector, rather 
    than modifying it.

    However, methods have also been added named with set_* prefixes which performs mutating operations, e.g., ::

       A.set_T()

    replaces A with its own transpose, whereas ::

       A.T()

    just returns a new MutableFracVector that is the transpose of A, leaving A unmodified.
    """    

    # Implementation note: REMEMBER TO CALL 'self._invalidate()' if any mutation have been done on the frac vector that may have broken
    # cached properties, e.g., self._dim

    # Overloaded methods now replaced to be list-based rather than tuple-based
    nested_map = staticmethod(nested_map_list)
    nested_inmap = staticmethod(nested_inmap_list)
    nested_map_fractions = staticmethod(nested_map_fractions_list)
    _dup_noms = staticmethod(list)
                                              
    def __init__(self, noms, denom):
        """ 
        Low overhead constructor.
        
        noms: nested *tuples* (may not be a lists!) of nominator integers
        denom: integer denominator
        
        Represents the tensor (1/denom)*(noms)
        
        If you want to create a MutableFracVector from something else than tuples, use the MutableFracVector.create() method.
        """
        super(MutableFracVector, self).__init__(noms, denom)

    @classmethod
    def use(cls, old):
        """
        Make sure variable is a MutableFracVector, and if not, convert it.
        """
        if isinstance(old, MutableFracVector):
            return old
        elif isinstance(old, FracVector):
            return MutableFracVector.create(old)        
        else:
            try:
                return old.to_MutableFracVector()
            except Exception:
                pass

            try:
                fracvec = old.to_FracVector()
                return cls.__init__(fracvec.noms, fracvec.denom)        
            except Exception:
                pass
            
            return cls.create(old)

    def to_FracVector(self):
        """
        Return a FracVector with the values of this MutableFracVector.
        """
        return FracVector.create(self.noms, self.denom)

    @classmethod
    def from_FracVector(cls, other):
        """
        Create a MutableFracVector from a FracVector.
        """
        return MutableFracVector.create(other.noms, other.denom)

    def validate(self):
        # TODO: check all dimensions and make sure noms is a square tensor of only lists
        return True

    def invalidate(self):
        """
        Internal method to call when MutableFracVector is changed in such a way that cached properties
        are invalidated (e.g., _dim)
        """
        self._dim = None

    #### Python special overloads
    
    def __hash__(self):
        raise Exception("MutableFracVector.__hash__: Cannot (should not) use hash number of a mutable object.")

    def __setitem__(self, key, values):
        if not isinstance(key, tuple):
            key = (key,)

        other = FracVector.create(values)
        one, two, denom = self.set_common_denom(self, other)
        self.noms = one.noms
        self.denom = denom
        list_set_slice(self.noms, key, two.noms)
        if not self.validate():
            raise Exception("MutableFracVector: assignment slice: "+str(key)+" mismatch with vector dimensions: "+str(self.dim))

    def __getitem__(self, key):
        if not isinstance(key, tuple):
            key = (key,)
        noms = list_slice(self.noms, key)
        return MutableFracVector(noms, self.denom)

    def set_negative(self):
        """
        Changes MutableFracVector inline into own negative: self -> -self
        """
        nested_inmap_list(operator.neg, self.noms)

    def set_T(self):
        """
        Changes MutableFracVector inline into own transpose: self -> self.T
        """
        #TODO: Possible to optimize?
        dim = self.dim
        if len(dim) == 0:
            return 
        elif len(dim) == 1:
            self.noms = [[self.noms[col], ] for col in range(dim[0])]
            return
        elif len(dim) == 2:
            self.noms = [[self.noms[col][row] for col in range(dim[0])] for row in range(dim[1])]
            return
        raise Exception("FracVector.T(): on non 1 or 2 dimensional object not implemented")

    def set_inv(self):
        """
        Changes MutableFracVector inline into own inverse: self -> self^-1
        """
        dim = self.dim        
        if dim == ():
            return self.__class__(self.denom, self.nom)
        
        if dim != (3, 3):
            raise Exception("FracVector.inv: only scalar and 3x3 matrix implemented")

        # We are dividing with a determinant giving self.denom**3 in nominator, and 
        # from the matrix 1/self.denom**2 falls out => one factor of self.denom in nominator 

        det = self.det()
        det_nom = det.nom

        if det_nom == 0:
            raise Exception("ExactVector.inverse: cannot take inverse of singular matrix.")
        
        if det_nom < 0:
            self.denom = -det_nom
            m = -self.denom
        else:
            self.denom = det_nom
            m = self.denom
            
        A = self.noms
        self.noms = [[m * (A[1][1] * A[2][2] - A[1][2] * A[2][1]), m * (A[0][2] * A[2][1] - A[0][1] * A[2][2]), m * (A[0][1] * A[1][2] - A[0][2] * A[1][1])],
                    [m * (A[1][2] * A[2][0] - A[1][0] * A[2][2]), m * (A[0][0] * A[2][2] - A[0][2] * A[2][0]), m * (A[0][2] * A[1][0] - A[0][0] * A[1][2])],
                    [m * (A[1][0] * A[2][1] - A[1][1] * A[2][0]), m * (A[0][1] * A[2][0] - A[0][0] * A[2][1]), m * (A[0][0] * A[1][1] - A[0][1] * A[1][0])]]                    
            
    def set_simplify(self):
        """
        Changes MutableFracVector; reduces any common factor between denominator and all nominators
        """       
        if self.denom != 1:
            gcd = self._reduce_over_noms(lambda x, y: fractions.gcd(x, abs(y)), initializer=self.denom)
            if gcd != 1:
                self.denom = self.denom / gcd
                self._inmap_over_noms(lambda x: int(x / gcd))

    def set_set_denominator(self, resolution=1000000000):
        """
        Changes MutableFracVector; reduces resolution.
        
          resolution is the new denominator, each element becomes the closest numerical approximation using this denominator.
        """
        denom = self.denom

        def limit_resolution_one(x):
            low = (x * resolution) // denom
            if x * resolution * 2 > (low * 2 + 1) * denom:
                return low + 1
            else:
                return low
        
        self._inmap_over_noms(limit_resolution_one)        
        self.denom = resolution

    def set_normalize(self):
        """
        Add/remove an integer +/-N to each element to place it in the range [0,1)
        """
        self._inmap_over_noms(lambda x: x - self.denom * (x // self.denom))

    def set_normalize_half(self):
        """
        Add/remove an integer +/-N to each element to place it in the range [-1/2,1/2)
        
        This is useful to find the shortest vector C between two points A, B in a space with periodic boundary conditions [0,1):
           C = (A-B).normalize_half()
        """
        self._inmap_over_noms(lambda x: 2 * x - (2 * self.denom) * ((((2 * x) // self.denom) + 1) // 2))
        self.denom = 2*self.denom

    #### Private methods

    def _inmap_over_noms(self, op, *others):
        """Inmap an operation over all nominators"""
        othernoms = [x.noms for x in others]
        if isinstance(self.noms, (tuple, list)):
            self.nested_inmap(op, self.noms, *othernoms)
        else:
            self.noms = op(self.noms, *othernoms)


def list_slice(l, key):    
    """
    Given a python slice (i.e., what you get to __getitem__ when you write A[3:2]), cut out the relevant
    nested list.
    """    
    if isinstance(key[0], (int, long, slice)):
        slicedlist = l[key[0]]
    else: 
        slicedlist = tuple([l[i] for i in key[0]])
    cdr = key[1:]
    if len(cdr) > 0:
        if isinstance(key[0], slice):
            return tuple(list_slice(slicedlist[i], cdr) for i in range(len(slicedlist)))
        else:
            return list_slice(slicedlist, cdr)
    return slicedlist


def list_set_slice(l, key, values):
    """
    Given:
      l = list, 
      key = python slice (i.e., what you get to __setitem__ when you write A[3:2]=[2,5])
      values = a list of values, 

    change the elements specified by the slice in key to those given by values.
    """    
    if len(key) == 1:
        if isinstance(key[0], (slice,)):
            l[key[0]] = list(values)
        else:
            l[key[0]] = values
        return 
    
    if isinstance(key[0], (int, long)):
        list_set_slice(l[key[0]], key[1:], values)
    elif isinstance(key[0], slice):
        idxs = key[0].indices(len(l))
        i = 0
        for idx in range(*idxs):
            list_set_slice(l[idx], key[1:], values[i])
            i += 1
    else:
        for idx in key[0]:
            list_set_slice(l[idx], key[1:], values[i])
            i += 1


def inmap(f, x):
    """
    Like built-in map, but work on a list and *replace* the elements in the list with the result of the mapping. 
    """    
    for i, v in enumerate(x):
            x[i] = f(v)
    

def main():
    a = FracVector.create([[2, 3, 5], [3, 5, 4], [4, 6, 7]])
    b = MutableFracVector.from_FracVector(a)
    print(b)    
    print(b.T())    
    print(b.inv())    
    b[2, 1:] = [4711, 23] 
    print(b)
    b.set_negative()
    print(b)

if __name__ == "__main__":
    main()  

    
