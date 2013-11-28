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
httk core module

Basic utilities and data definitions that are used throughout the httk code.

A few of the most important components:
  fracvector: our general matrix object used to allow exact representation of arrays to allow, e.g., exact matching 
              of coordinates to existing structures in the database.

  ioadapters: our classes for generic handling of IO to files, streams, etc.
  
  structure: our basic definition of a "structure of atoms"
"""

import citation
citation.add_src_citation("httk","Rickard Armiento")

from fracvector import FracVector
from structure import Structure
from prototype import Prototype
from compound import Compound
from ioadapters import IoAdapterFileReader, IoAdapterFileWriter, IoAdapterFileAppender, IoAdapterString, IoAdapterStringList, IoAdapterFilename
import htdata

