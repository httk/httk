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

from httk.atomistic import Structure
from httk.core import *

def load_struct(ioa, ext=None, filename=None):
    """
    Load structure data from a file into a Structure
    """
    ioa = IoAdapterFilename.use(ioa)   
    if ext == None:
        try:
            if filename == None:
                filename = ioa.filename
        except Exception:
            raise Exception("httk.io.load: original filename not known. Cannot open a generic file.")

        splitfilename = os.path.splitext(os.path.basename(filename))
        ext = splitfilename[1]

        if (ext == '.bz2' or ext == '.gz'):
            splitfilename = os.path.splitext(splitfilename[0])
            ext = splitfilename[1]

        if ext == '':
            ext = splitfilename[0]

        if ext.startswith("POSCAR"):
            ext = '.vasp'
        if ext.startswith("CONTCAR"):
            ext = '.vasp'

    if ext == '.vasp':
        import httk.iface.vasp_if
        return httk.iface.vasp_if.poscar_to_structure(ioa)
    elif ext == '.cif':
        from structure_cif_io import cif_to_struct
        #filedata = list(ioa)
        #ioa = IoAdapterString("\n".join(filedata))
        #for line in filedata:
        #    if line.startswith("# This is a cif file prepared for use with the openmaterialsdb.se"):
        #        return cif_to_struct(ioa,backends=['cif_reader_httk_preprocessed'])
        #else:
        #    return cif_to_struct(ioa,backends=['cif2cell_reduce'])
        return cif_to_struct(ioa)
    else:
        raise Exception("httk.io.load: I do not know what to do with the file:"+filename)


def save_struct(struct, ioa, ext=None):
    """
    Save structure data from a file into a Structure
    """
    ioa = IoAdapterFilename.use(ioa)   
    if ext == None:
        try:
            filename = ioa.filename
        except Exception:
            raise Exception("httk.io.load: original filename not known. Cannot open a generic file.")

        splitfilename = os.path.splitext(os.path.basename(filename))
        ext = splitfilename[1]

        if (ext == '.bz2' or ext == '.gz'):
            splitfilename = os.path.splitext(splitfilename[0])
            ext = splitfilename[1]

        if ext == '':
            ext = splitfilename[0]

        if ext.startswith("POSCAR"):
            ext = '.vasp'
        if ext.startswith("CONTCAR"):
            ext = '.vasp'

    if ext == '.vasp':
        import httk.iface.vasp_if
        return httk.iface.vasp_if.structure_to_poscar(ioa, struct)
    elif ext == '.cif':
        from structure_cif_io import struct_to_cif
        return struct_to_cif(struct, ioa)
    else:
        raise Exception("httk.io.save: I do not know what to do with the file:"+filename)
    


