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

"""
httk core module

Basic utilities and data definitions that are used throughout the httk code.

A few of the most important components:
  fracvector: our general matrix object used to allow exact representation of arrays to allow, e.g., exact matching 
              of coordinates to existing structures in the database.

  ioadapters: our classes for generic handling of IO to files, streams, etc.
  
  structure: our basic definition of a "structure of atoms"
"""

import sys
try:    
    python_major_version = sys.version_info[0]
    python_minor_version = sys.version_info[1]
except Exception:
    raise Exception("Python version too old. Httk appear to be running on a version older than python 2.0!")

import citation
citation.add_src_citation("httk","Rickard Armiento")

import basic
from code import Code
from computation import Computation, Result, ComputationRelated, ComputationProject
from reference import Author, Reference
from project import Project, ProjectRef, ProjectTag
import crypto
from fracvector import FracVector, FracScalar
from mutablefracvector import MutableFracVector
from signature import Signature, SignatureKey

from ioadapters import IoAdapterFileReader, IoAdapterFileWriter, IoAdapterFileAppender, IoAdapterString, IoAdapterStringList, IoAdapterFilename
from httkobject import HttkObject, httk_typed_property, httk_typed_init, httk_typed_property_delayed, httk_typed_init_delayed
from httkobject import HttkPluginWrapper, HttkPlugin, HttkPluginPlaceholder



