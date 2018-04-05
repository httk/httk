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
from config import httk_dir as httk_dir_imported, config
from core import *
from io import load, save
import iface

citation.add_src_citation("httk","Rickard Armiento")

#: The version of httk (if you make signifcant changes to httk, please update with 
#: a personal suffix, e.g., 1.0.7.rickard.2)
version='1.0.7' 

# This is to make the docstring work correctly 
#: The path to the main httk directory
httk_dir = httk_dir_imported

# From this module
__all__ = ["httk_dir", "config", "load", "save", "iface", "version"]

# From core:
__all__ += ["citation","basic","Code","Computation","Result","ComputationRelated","ComputationProject",
            "Author","Reference","Project","ProjectRef","ProjectTag","crypto","FracVector","FracScalar",
            "MutableFracVector", "IoAdapterFileReader","IoAdapterFileWriter","IoAdapterFileAppender",
            "IoAdapterString","IoAdapterStringList","IoAdapterStringList","HttkObject",
            "httk_typed_property","httk_typed_init","httk_typed_property_delayed","httk_typed_init_delayed",
            "HttkPluginWrapper","HttkPlugin","HttkPluginPlaceholder","Signature","SignatureKey"]

# Fiddling to get Sphinx document imported modules correctly
crypto.__module__ = "httk"
basic.__module__ = "httk"
citation.__module__ = "httk"
iface.__module__ = "httk"
