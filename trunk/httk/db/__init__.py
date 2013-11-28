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

"""
httk Database module

 - Creation of databases
 - Searching in databases
 - Insertion / removal of data in databases

 Submodules:
   - store (backends for different 'stores' for storing data)
   - backend (database backends for the sqlstore store)

"""

from httk.core import citation
citation.add_src_citation("httk_db","Rickard Armiento")

from storable import *
from dbstructure import *
from dbcompound import *
from dbresult import *
from dbcomputation import *
from filteredcollection import *
import store
import backend
from misc import *
