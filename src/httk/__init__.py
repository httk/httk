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
from httk.config import *

__version__ = version

from .core import *
cout = console.cout
cerr = console.cerr

from httk.httkio import load, save
import httk.iface

citation.add_src_citation("httk", "Rickard Armiento")

# From this module
__all__ = ["httk_root", "python_root", "config", "load", "save",
           "iface", "__version__", "version_date", "copyright_note",
           "version", "major_version", "minor_version",
           "patch_version", "python_major_version",
           "python_minor_version", "cout", "cerr"]

# From core:
__all__ += ["citation", "basic", "Code", "Computation", "Result", "ComputationRelated", "ComputationProject",
            "Author", "Reference", "Project", "ProjectRef", "ProjectTag", "crypto", "FracVector", "FracScalar",
            "MutableFracVector", "IoAdapterFileReader", "IoAdapterFileWriter", "IoAdapterFileAppender",
            "IoAdapterString", "IoAdapterStringList", "IoAdapterStringList", "HttkObject",
            "httk_typed_property", "httk_typed_init", "httk_typed_property_delayed", "httk_typed_init_delayed",
            "HttkPluginWrapper", "HttkPlugin", "HttkPluginPlaceholder", "Signature", "SignatureKey"]

cli_modules = {'atomistic':'httk.atomistic.cli'}

# Fiddling to get Sphinx document imported modules correctly
crypto.__module__ = "httk"
basic.__module__ = "httk"
citation.__module__ = "httk"
iface.__module__ = "httk"
