#!/usr/bin/env python
# -*- coding: utf-8 -*- 
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

from httk.core import citation
citation.add_ext_citation('cif2cell', "Torbjörn Björkman")

from httk import config
from command import Command
import httk

try:   
    cif2cell_path=config.get('paths', 'cif2cell')
except Exception:
    cif2cell_path = None
    raise Exception("httk.external.cif2cell imported with no cif2cell path set in httk.cfg")

def cif2cell(cwd, args,timeout=30):
    #p = subprocess.Popen([cif2cell_path]+args, stdout=subprocess.PIPE, 
    #                                   stderr=subprocess.PIPE, cwd=cwd)
    #print "COMMAND CIF2CELL"
    out,err,completed = Command(cif2cell_path,args,cwd=cwd).run(timeout)
    #print "COMMAND CIF2CELL END"
    return out, err, completed
    #out, err = p.communicate()
    #return out, err

def cif_to_structure(f):
    ioa = httk.IoAdapterFilename(f)
    out, err, completed = cif2cell("./",["--no-reduce",ioa.filename])
    if err != "":
        print err
    if not completed:
        return None
    struct = httk.iface.cif2cell_if.out_to_struct(httk.IoAdapterString(out))
    return struct
    #return Structure.create(cell=cell, coords=coords, occupations=occupations)

