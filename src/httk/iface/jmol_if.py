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

import tempfile, os, shutil

from httk.atomistic.data import periodictable
from httk.core.basic import is_sequence
from math import sqrt
import httk


def structure_to_jmol(iof, struct, extbonds=True, repeat=None, copies=None):
    """
    Converts structure into jmol format.

    Example output format::
        load data 'model'
        1
        Computation1
        Al 0 0 0
        end 'model' { 4 4 4 } supercell "x, y, z " unitcell [
        2.025 2.025 0
        2.025 0 2.025
        0 2.025 2.025
        ]
        set slabByAtom TRUE
        unitcell {1/1 1/1 1/1}
        delete (NOT (unitcell OR connected(unitcell)))
        {connected(unitcell) AND NOT unitcell}.radius = 0
        restrict cell={2 2 2}
        center visible
        zoom 0
    """            

    if repeat is None:
        supercell = "supercell \"x, y, z\""
    else:
        supercell = "supercell \""+str(int(repeat[0]))+"x, "+str(int(repeat[1]))+"y, "+str(int(repeat[2]))+"z \""

    if copies is None:
        copies = "{ 1 1 1 }"
    else:
        copies = "{ "+str(int(copies[0]))+" "+str(int(copies[1]))+" "+str(int(copies[2]))+" }"

    iof = httk.IoAdapterFileWriter.use(iof)
    f = iof.file
    
    nl = "|"
    
    if struct.has_rc_repr:
        basis = struct.rc_basis.to_floats()
        coords = struct.rc_cartesian_coords.to_floats()
        symbollist = struct.rc_occupationssymbols
        spacegroup = struct.rc_sites.hall_symbol
    elif struct.has_uc_repr:
        basis = struct.uc_basis.to_floats()
        coords = struct.uc_cartesian_coords.to_floats()
        symbollist = struct.uc_occupationssymbols
        spacegroup = 'P 1'
    else:
        raise Exception("httk.jmol_if.structure_to_jmol: structure has neither representative nor primcell representation?")

    symbols = []
    for s in symbollist:
        if is_sequence(s):
            if len(s) == 1:
                symbols += [s[0]]
            else:
                symbols += [str(s)]
        else:
            symbols += [s]

    f.write("load data 'model'"+nl)
    f.write(str(len(symbols))+nl)
    f.write("Computation1"+nl)

    for i in range(len(symbols)):
        f.write(symbols[i]+" "+str(coords[i][0])+" "+str(coords[i][1])+" "+str(coords[i][2])+str(nl))
        #print "XX",symbols[i]+" "+str(coords[i][0])+" "+str(coords[i][1])+" "+str(coords[i][2])+str(nl)
    
    f.write("end 'model' ")
    f.write(" "+copies+" "+supercell+" spacegroup '"+spacegroup+"' unitcell [ ")
    for i in range(3):
        f.write(str(basis[i][0])+" "+str(basis[i][1])+" "+str(basis[i][2])+" ")
    f.write("];\n")

    #f.write("show data;\n")

    iof.close()

         
