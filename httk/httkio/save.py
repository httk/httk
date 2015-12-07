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

import os

import httk
import httk.iface

from httk.atomistic.data import periodictable, spacegroups
from httk.core import *
from httk.atomistic import *


def save(obj, ioa, ext=None):
    """
    A *very* generic file writer method.
    
    Load a file into a suitable httk object. Try to do the most sane thing possible given the input file.
    If you know what to expect from the input file, it may be safer to use a targeted method for that file type.
    """
    try:
        import httk.atomistic
        import httk.atomistic.atomisticio

        if isinstance(obj, httk.atomistic.Structure):        
            return obj.io.save(ioa, ext=ext)
    except Exception:
        raise
        pass        
    raise Exception("httk.httkio.save: I do not know how to save the object: "+str(obj))
    #info = sys.exc_info()   
    #raise Exception("httk.httkio.load: I do not know what to do with the file: "+str(ioa)+"\n("+str(e)+")"),None,info[2]
    
#     ioa = IoAdapterFilename.use(ioa)
#     if ext == None:
#         try:
#             filename = ioa.filename
#             ext = os.path.splitext(filename)[1]
#             if ext == '':
#                 if filename.startswith("POSCAR"):
#                     ext = '.vasp'
#         except Exception:
#             raise Exception("httk.httkio.load: original filename not known. Cannot open a generic file.")
# 
#     if ext == '.vasp':
#         return httk.iface.vasp_if.poscar_to_structure(filename)
#     elif ext == '.cif':
#         filedata = list(ioa)
#         ioa = IoAdapterString("\n".join(filedata))
#         for line in filedata:
#             if line.startswith("# This is a cif file prepared for use with the openmaterialsdb.se"):
#                 return httk.httkio.cif_to_struct(ioa,backends=['cif_reader_httk_preprocessed'])
#         else:
#             return httk.httkio.cif_to_struct(ioa,backends=['cif2cell_reduce'])
#     else:
#         raise Exception("httk.httkio.load: I do not know what to do with the file:"+filename)
#     



    
