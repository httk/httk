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
from httk.core.htdata import periodictable
from storable import Storable, storable_types
from dbcomputation import *

class DbResult(Storable):
    """
    """   
    types = storable_types('Result', ('computation',DbComputation), ('result_table',str))    
    
    def __init__(self, computation, result_table, store=None):
        """
        """                
        # Storable init        
        self.storable_init(store, computation=computation, result_table=result_table)

    @classmethod
    def create(cls,computation, resultclass, store=None):
        return DbResult(computation, resultclass.types['name'],store=store)
    
    @classmethod
    def use(cls,old, store=None):
        if isinstance(old,DbResult) and (store == None or store == old.store.store):
            return old    
        raise Exception("DbResult.use of non-dbresult not implemented, sorry.")
    
    