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

from httk.core import citation
citation.add_ext_citation('aflow', "(Author list to be added)")

from httk import config
from command import Command
import httk

try:    
    aflow_path = config.get('paths', 'aflow')
except Exception:
    aflow_path = None
    raise Exception("httk.external.aflow imported with no aflow path set in httk.cfg")


def aflow(ioa_in, args, timeout=30):
    ioa_in = httk.IoAdapterString.use(ioa_in)
    #
    #print "COMMAND AFLOW"
    #print "SENDING IN",ioa_in.string
    out, err, completed = Command(aflow_path, args, inputstr=ioa_in.string).run(timeout)
    #print "COMMAND AFLOW END"
    #return out, err
    #
    #p = subprocess.Popen([aflow_path]+args, stdin=subprocess.PIPE,stdout=subprocess.PIPE, 
    #                                   stderr=subprocess.PIPE)
    #out, err = p.communicate(input=ioa_in.string)
    ioa_in.close()
    return out, err, completed


def standard_primitive(struct):
    ioa = httk.IoAdapterString()
    
    httk.iface.vasp_if.structure_to_poscar(ioa, struct)

    out, err = aflow(ioa, ["--prim"])

    print err

    ioa2 = httk.IoAdapterString(out)
    newstruct = httk.iface.vasp_if.poscar_to_structure(ioa2)
    ioa.close()
    ioa2.close()
    return newstruct

