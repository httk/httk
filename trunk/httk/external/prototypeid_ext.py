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

import os

from httk import config
from subimport import submodule_import_external
import httk

try:
    prototypeid_path=config.get('paths', 'prototypeid')
except Exception:
    prototypeid_path = None
    
if prototypeid_path != None:    
    prototypeid_path = submodule_import_external(prototypeid_path,'prototypeid')
else:
    try:
        external=config.get('general', 'allow_system_libs')
    except Exception:
        external = 'yes'
    if external == 'yes':
        import prototypeid
    else:
        raise Exception("httk.external.prototypeid_ext imported, but could not access prototypeid.")
    
from prototypeid.fracvector import FracVector as FracVector2

def find_chain(struct):
    if struct.comment == None:
        basecomment = ""
    else:
        basecomment = struct.comment + " "
    
    pidchain = prototypeid.prototypeid_chain(FracVector2.create(struct.cell), struct.scale, FracVector2.create(struct.coordgroups), struct.assignments)
    results = []
    for pid in pidchain:
        print "ODDISH",sqrt(pid.scalesqr),pid.orientation
        s = httk.Structure.create(niggli_matrix = pid.niggli_matrix, coordgroups=pid.coordgroups, 
                                       orientation = pid.orientation, scale=sqrt(pid.scalesqr), 
                                       assignments=pid.occupations, comment=basecomment + "pid:" + pid.hexkey())
        s.prototype = httk.Prototype(pid.niggli_matrix, pid.coordgroups, cell_resolution = pid.cell_resolution, coord_resolution = pid.coord_resolution)
        results.append(s)
    return results



