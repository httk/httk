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
from fracvector import FracVector

class MutableFracVector(FracVector):
    """
    Same as FracVector, only, this version does allow assignment of elements, e.g., 
        mfracvec[2,7] = 5
    and, e.g.,
        mfracvec[:,7] = [1,2,3,4] 

    Other than this, all methods are the same as FracVector, meaning that they return *copies* of the fracvector, rather than modifying it.

    Specific methods added named with mutate_* prefix allows mutating operations, e.g., if implemented (it is not yet)
       mutate_mul(B)
    does a multiplication that changes the fracvector itself.
    """    
    
    def __init__(self, noms, denom):
        """ Low overhead constructor.
        
        noms: nested *tuples* (may not be a lists!) of nominator integers
        denom: integer denominator
        
        Represents the tensor 1/denoms*(noms)
        
        If you want to create a MutableFracVector from something else than tuples, use the MutableFracVector.create() method.
        """
        super(MutableFracVector,self).__init__(noms,denom)

    @classmethod
    def use(cls,old):
        """Make sure variable is a MutableFracVector, and if not, convert it."""
        if isinstance(old,MutableFracVector):
            return old
        elif isinstance(old,FracVector):
            return cls.__init__(old.noms,old.denom)        
        else:
            try:
                return old.to_MutableFracVector()
            except Exception:
                pass

            try:
                fracvec = old.to_FracVector()
                return cls.__init__(fracvec.noms,fracvec.denom)        
            except Exception:
                pass
            
            return cls.create(old)
        

    def to_FracVector(self):
        return FracVector(self.norms,self.denom)
    
    def __hash__(self):
        raise Exception("MutableFracVector.__hash__: Cannot (should not) use hash number of a mutable object.")

    def __setitem__(self, key, values):
        # I have this implemented already somewhere, need to look for the code (rar, Nov 2013)
        raise Exception("MutableFracVector.__setitem__: not implemented yet.")

    