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
from math import sqrt
import httk


def generate_fake_potentials(species):
    potentials = ""
    potentials += "atomab\n"
    for s1 in species:
        ss1 = periodictable.atomic_symbol(s1)
        ns1 = periodictable.atomic_number(s1)
        potentials += "%s core %.4f %.4f 0 0\n" % (ss1, sqrt(0.5*ns1), pow(0.75*ns1, 3.0/2.0))
    #potentials = "lennard combine 12 6\n"
    potentials += "lennard 12 6 combine all\n"
    potentials += "0.0 20.0\n"
    #for s1 in species:
    #    ss1 = periodictable.atomic_symbol(s1)
    #    for s2 in species:
    #        ss2 = periodictable.atomic_symbol(s2)
    #        potentials += "%s core %s core %.4f %.4f\n" % (ss1, ss2,0.0,10.0)

    return potentials


def generate_fake_potentials_try2(species):
    potentials = ""
    potentials += "epsilon\n"
    for s1 in species:
        ss1 = periodictable.atomic_symbol(s1)
        ns1 = periodictable.atomic_number(s1)
        #potentials += "%s core %.4f %.4f 0 0\n" % (ss1,sqrt(0.5*ns1),pow(0.75*ns1,3.0/2.0))
#        potentials += "%s core %.4f %.4f 0 0\n" % (ss1,pow(ns1,0.9783276738),pow(ns1,1.124243243))
        potentials += "%s core %.4f %.4f 0 0\n" % (ss1, 0.1*ns1, 0.1*ns1)

    potentials += "lennard zero epsilon combine all\n"
    potentials += "0.0 12.0\n"

    return potentials


def structure_to_gulp(iof, struct, runspec="single conp", postcards=[], potentials=None):
    """
    Writes a file on gulp input format.
    """        
    iof = httk.IoAdapterFileWriter.use(iof)
    f = iof.file
    
    f.write(str(runspec)+"\n")
    f.write("cell\n")
    f.write("  "+str(struct.a)+" "+str(struct.b)+" "+str(struct.c)+" ")
    f.write(str(struct.alpha)+" "+str(struct.beta)+" "+str(struct.gamma)+"\n")
    f.write("fractional\n")
    for i in range(struct.N):
        species = periodictable.atomic_symbol(struct.p1occupancies[i])
        f.write(species+" ")
        f.write(" ".join([str(float(x)) for x in struct.p1coords[i]])+"\n")
        #print "X",species+str(idx)+" "+" ".join([str(float(x)) for x in struct.coords[i]])+"\n"
    for card in postcards:
        f.write(card+"\n")
    if potentials is None:
        f.write(generate_fake_potentials(set(struct.p1assignments)))
    f.write("\n")
    iof.close()
    

         
