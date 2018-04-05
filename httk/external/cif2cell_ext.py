#!/usr/bin/env python
# -*- coding: utf-8 -*- 
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

from httk.core import citation, IoAdapterString
from httk.atomistic.io.structure_cif_io import struct_to_cif_httk
from httk.atomistic import Structure
citation.add_ext_citation('cif2cell', "Torbjörn Björkman")

from httk import config
from command import Command
import httk
import httk.iface

try:   
    cif2cell_path=config.get('paths', 'cif2cell')
except Exception:
    #return [name for name in os.listdir(a_dir)
    #        if os.path.isdir(os.path.join(a_dir, name))]    
    cif2cell_path = None
    #raise Exception("httk.external.cif2cell imported with no cif2cell path set in httk.cfg")

if cif2cell_path == None or cif2cell_path == "":
    from httk.config import httk_dir    
    path = os.path.join(httk_dir,'External')
    externaldirs=[name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]
    extvers=[name.split('-')[1] for name in externaldirs if name.split('-')[0] == "cif2cell"]    
    extvers = sorted(extvers,key=lambda x:map(int, x.split('.')))    
    bestversion = 'cif2cell-'+extvers[-1]
    cif2cell_path = os.path.join(path,bestversion,'cif2cell')

if cif2cell_path == "" or not os.path.exists(cif2cell_path):
    raise ImportError("httk.external.cif2cell imported without access to a cif2cell binary to run.")
    
def cif2cell(cwd, args,timeout=30):
    #p = subprocess.Popen([cif2cell_path]+args, stdout=subprocess.PIPE, 
    #                                   stderr=subprocess.PIPE, cwd=cwd)
    #print "COMMAND CIF2CELL",args
    out,err,completed = Command(cif2cell_path,args,cwd=cwd).run(timeout)
    #print "COMMAND CIF2CELL END",out
    return out, err, completed
    #out, err = p.communicate()
    #return out, err

# def cif_to_structure(f):
#     ioa = httk.IoAdapterFilename.use(f)
#     #out, err, completed = cif2cell("./",["--no-reduce",ioa.filename])
#     out, err, completed = cif2cell("./",["--no-reduce",ioa.filename])
#     if err != "":
#         print err
#     if completed != 0:
#         return None
#     struct = httk.iface.cif2cell_if.out_to_struct(httk.IoAdapterString(out))
#     return struct
#     #return Structure.create(cell=cell, coords=coords, occupations=occupations)

def cif_to_structure_reduce(f):
    ioa = httk.IoAdapterFilename.use(f)
    out, err, completed = cif2cell("./",[ioa.filename])
    if err != "":
        print err
    if completed != 0:
        return None
    struct = httk.iface.cif2cell_if.out_to_struct(httk.IoAdapterString(out))
    return struct

def cif_to_structure_noreduce(f):
    ioa = httk.IoAdapterFilename.use(f)
    #out, err, completed = cif2cell("./",["--no-reduce",ioa.filename])
    out, err, completed = cif2cell("./",["--no-reduce",ioa.filename])
    if err != "":
        print err
    if completed != 0:
        return None
    struct = httk.iface.cif2cell_if.out_to_struct(httk.IoAdapterString(out))
    return struct
    #return Structure.create(cell=cell, coords=coords, occupations=occupations)

def coordgroups_reduced_rc_to_unitcellsites(coordgroups,basis,hall_symbol):
    # Just fake representative assignments for the coordgroups
    assignments = range(1,len(coordgroups)+1)
    struct = Structure.create(rc_cell=basis, assignments=assignments, rc_reduced_coordgroups=coordgroups, hall_symbol=hall_symbol)
    ioa = IoAdapterString()
    struct_to_cif_httk(struct,ioa)
    struct = cif_to_structure_reduce(ioa)
    return struct.uc_sites, struct.uc_cell
        
    
    
    

