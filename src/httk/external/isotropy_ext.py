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

import sys, os, tempfile

from httk.core import citation, IoAdapterString
citation.add_ext_citation('isotropy', "Harold T. Stokes, Dorian M. Hatch, and Branton J. Campbell, Department of Physics and Astronomy, Brigham Young University, Provo, Utah 84606, USA")

from httk.core.basic import int_to_anonymous_symbol
from httk import config
from command import Command
import httk.httkio
import httk.iface

from httk.atomistic.atomisticio.structure_cif_io import cif_to_struct
from httk.atomistic.data.periodictable import atomic_symbol, atomic_number

isotropy_path = None

def ensure_has_isotropy():
    if isotropy_path is None or isotropy_path == "":
        raise ImportError("httk.external.isotropy_ext imported with no access to isotropy binary")

try:   
    isotropy_path = config.get('paths', 'isotropy')
except Exception:
    pass

def isotropy(cwd, args, inputstr, timeout=30):
    ensure_has_isotropy()
    
    #p = subprocess.Popen([cif2cell_path]+args, stdout=subprocess.PIPE, 
    #                                   stderr=subprocess.PIPE, cwd=cwd)
    #print "COMMAND CIF2CELL"
    out, err, completed = Command(os.path.join(isotropy_path, 'findsym'), args, cwd=cwd, inputstr=inputstr).run(timeout)
    #print "COMMAND CIF2CELL END"
    return out, err, completed
    #out, err = p.communicate()
    #return out, err


def uc_reduced_coordgroups_process_with_isotropy(coordgroup, cell, get_wyckoff=False):
    #print "GURK",struct.formula,len(struct.uc_reduced_coords)

    inputstr = httk.iface.isotropy_if.reduced_coordgroups_to_input(coordgroup, cell)
    out, err, completed = isotropy("./", [], inputstr)
    if completed == 0:
        cif = httk.iface.isotropy_if.out_to_cif(IoAdapterString(string=out), [atomic_symbol(x) for x in range(1, len(coordgroup)+1)])
        #print "CIF",cif
        newstruct = cif_to_struct(IoAdapterString(string=cif), backends=['cif2cell_reduce'])
        checkstruct = cif_to_struct(IoAdapterString(string=cif), backends=['cif2cell'])
        only_rc_struct = cif_to_struct(IoAdapterString(string=cif), backends=['cif_reader_that_can_only_read_isotropy_cif'])
        # This is an illeelegant hack
        newstruct.rc_sites.wyckoff_symbols = only_rc_struct.rc_sites.wyckoff_symbols
        # Cell basis can only be constructed from the cif approximately
        cell_mismatch = sum(sum((checkstruct.rc_cell.basis - only_rc_struct.rc_cell.basis))).to_float()
        #print "CELL MISMATCH:",sum(sum((newstruct.cell.maxnorm_basis - only_rc_struct.cell.maxnorm_basis))).to_float()
        only_rc_struct._rc_cell = newstruct.rc_cell
        # Make sure the hexhash is recomputed
        only_rc_struct.rc_sites._hexhash = None
        #print "CHECK THIS:", newstruct.rc_sites.hexhash, only_rc_struct.rc_sites.hexhash
        #print "CHECK THIS:", newstruct.cell.to_tuple(), only_rc_struct.cell.to_tuple()
        if cell_mismatch > 1e-6 or newstruct.rc_sites.hexhash != only_rc_struct.rc_sites.hexhash:
            print "Cell mismatch:", cell_mismatch
            print "Structure hashes:", newstruct.rc_sites.hexhash, only_rc_struct.rc_sites.hexhash
            #print "Structures:", newstruct.rc_sites.to_tuple(), only_rc_struct.rc_sites.to_tuple()
            raise Exception("isotropy_ext.struct_process_with_isotropy: internal error, structures that absolutely should be the same are not, sorry.")       
 
        #order = [x.as_integer-1 for x in newstruct.assignments]
        #print "ORDER:",order
        
        if get_wyckoff:
            return newstruct.rc_reduced_coordgroups, newstruct.rc_sites.wyckoff_symbols, [[atomic_number(x) for x in y] for y in newstruct.assigments.symbols_list()]
        else:
            return newstruct.rc_reduced_coordgroups
    else:
        print "ISOTROPY STDERR:"
        #print inputstr
        print "========"
        #print out
        #print "========"
        print err
        print "========"

        raise Exception("isotropy_ext: isotropy did not complete.")


def struct_process_with_isotropy(struct):
    tmpdir = tempfile.mkdtemp(prefix='ht.tmp.isotropy_')
    
    inputstr = httk.iface.isotropy_if.struct_to_input(struct)
    #print >> sys.stderr, "== Running findsym"
    #print "==================== INPUT\n",inputstr
    #print "===================="
    out, err, completed = isotropy(tmpdir, [], inputstr)

    # Clean up
    try:
        os.unlink(os.path.join(tmpdir, 'findsym.log'))
    except IOError:
        pass
    try:
        os.rmdir(tmpdir)
    except (IOError, OSError):
        pass
    
    #print >> sys.stderr, "== Running findsym complete, stderr output follows:"
    #print >> sys.stderr, out
    #print >> sys.stderr, "============================================"
    #print >> sys.stderr, err
    #print >> sys.stderr, float(struct.volume)
    #print >> sys.stderr, "============================================"
    #print "=== OUTPUT ===="
    #print out
    #print "=============="
    #print "XXX",struct.assignments.symbols
    if completed == 0:
        #print "what?",completed
        # TODO: Clean this up with own cif reader that actually reads wyckoff sites out of cif file!
        cif = httk.iface.isotropy_if.out_to_cif(IoAdapterString(string=out), struct.assignments)
        newstruct = cif_to_struct(IoAdapterString(string=cif))
        #print "Rejected?"
        
        newstruct.add_tags(struct.get_tags())
        newstruct._refs = struct.get_refs()

        #print "CHECKING",struct.uc_volume,newstruct.rc_volume
        
#         only_rc_struct = cif_to_struct(IoAdapterString(string=cif), backends=['cif_reader_that_can_only_read_isotropy_cif'])
#         #newstruct.rc_sites.wyckoff_symbols = only_rc_struct.rc_sites.wyckoff_symbols
#         #newstruct.rc_sites._multiplicities = only_rc_struct.rc_sites._multiplicities
#         #print "HERE", only_rc_struct.rc_sites.wyckoff_symbols
#         # Cell basis can only be constructed from the cif approximately
#         cell_mismatch = sum(sum((newstruct.rc_cell.basis - only_rc_struct.rc_cell.basis))).to_float()
#         #print "CELL MISMATCH:",sum(sum((newstruct.cell.maxnorm_basis - only_rc_struct.cell.maxnorm_basis))).to_float()
#         #only_rc_struct._rc_cell = newstruct.rc_cell
#         # Make sure the hexhash is recomputed
#         #only_rc_struct.rc_sites._hexhash = None
#         #print "CHECK THIS:", newstruct.rc_sites.hexhash, only_rc_struct.rc_sites.hexhash
#         #print "CHECK THIS:", newstruct.cell.to_tuple(), only_rc_struct.cell.to_tuple()
#         if cell_mismatch > 1e-6 or newstruct.rc_sites.hexhash != only_rc_struct.rc_sites.hexhash:
#             print "Cell mismatch:", cell_mismatch
#             print "Structure hashes:", newstruct.rc_sites.hexhash, only_rc_struct.rc_sites.hexhash
#             print "======"
#             print newstruct.to_tuple()
#             print "======"
#             print only_rc_struct.to_tuple()
#             print "======"
#             #print "Structures:", newstruct.rc_sites.to_tuple(), only_rc_struct.rc_sites.to_tuple()
#             raise Exception("isotropy_ext.struct_process_with_isotropy: internal error, structures that absolutely should be the same are not, sorry.")       
        return newstruct
    else:
        print "ISOTROPY STDERR:"
        print inputstr
        print "========"
        print out
        print "========"
        print err
        print "========"

        raise Exception("isotropy_ext: isotropy did not complete.")

