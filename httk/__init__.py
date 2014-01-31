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
The high-throughput toolkit (httk)

A set of tools and utilities meant to help with:
   - Project management, preparation of large-scale computational project.
   - Execution of large-scale computational projects 
        - interface with supercomputer cluster queuing systems, etc.
        - aid with scripting multi-stage runs
        - retrieval of data from supercomputers
   - Storage of data in databases 
   - Search, retrieval and 'processing' of data in storage
   - Analysis (especially as a helpful interface against 3:rd party software)    
"""
from core import citation
citation.add_src_citation("httk","Rickard Armiento")

import analysis, ctrl, db, exe, external, iface, tasks, io
from core import *
import crypto
import utils
from config import config

#
# IF YOU MAKE SIGNIFICANT CHANGES TO httk, PLEASE UPDATE THIS VARIABLE WITH A PERSONAL SUFFIX 
# E.G. 0.4.rickard.2

version='0.4.1'



