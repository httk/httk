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

from httk.core import *
from storable import Storable, storable_types

class DbFracTriple(Storable):
    """
    """   
    types = storable_types('FracTriple', ('hexhash',str), ('noms',[('a',int), ('b',int), ('c',int)]), ('denom',int),index=['hexhash'])    
    
    def __init__(self, hexhash, noms, denom, store=None):
        """
        """                
        # Storable init        
        self.storable_init(store, hexhash=hexhash, denom=denom, noms=noms)

    @classmethod
    def create(cls,fracvec, store=None):
        hexhash = fracvec.hexhash

        return DbFracTriple(hexhash, fracvec.noms, fracvec.denom, store=store)
    
    @classmethod            
    def use(cls, old, store=None, reuse=False):
        if isinstance(old,DbFracTriple) and (store == None or store == old.store.store):
            return old    
        else:
            hexhash = old.hexhash
            if reuse and store != None:
                p = DbFracTriple.find_one(store, 'hexhash', hexhash)                
                if p != None:
                    return p

            return DbFracTriple.create(old.simplify(), store=store)
    
    
    
class DbIntTriple(Storable):
    """
    """   
    types = storable_types('IntTriple', ('hexhash',str), ('vals',[('a',int), ('b',int), ('c',int)]), index=['hexhash'])    
    
    def __init__(self, hexhash, vals, store=None):
        """
        """                
        # Storable init        
        self.storable_init(store, hexhash=hexhash, vals=vals)

    @classmethod
    def create(cls,fracvec, store=None):
        hexhash = fracvec.hexhash

        newfrac = (fracvec*1000000000).limit_resolution(1).simplify()

        return DbFracTriple(hexhash, newfrac.noms, store=store)
    
    @classmethod            
    def use(cls, old, store=None, reuse=False):
        if isinstance(old,DbIntTriple) and (store == None or store == old.store.store):
            return old    
        elif isinstance(old,FracVector):
            newfrac = (old*1000000000).limit_resolution(1).simplify()
            hexhash = newfrac.hexhash
            if reuse and store != None:
                p = DbIntTriple.find_one(store, 'hexhash', hexhash)                
                if p != None:
                    return p
            return DbIntTriple(hexhash, newfrac.noms, store=store)
        else:
            hexhash = old.hexhash
            if reuse and store != None:
                p = DbIntTriple.find_one(store, 'hexhash', hexhash)                
                if p != None:
                    return p

            return DbIntTriple.create(old, store=store)

    def to_fracvector(self):
        return FracVector.create(self.vals,1000000000)
    