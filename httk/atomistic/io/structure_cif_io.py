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

import os, hashlib
import httk

from httk.atomistic.data import periodictable, spacegroups
from httk.core import *
from httk.atomistic import Structure


def cif_to_struct(ioa, backends=['cif2cell', 'ase', 'platon']):
    for backend in backends:
        if backend == 'ase':
            try:
                from httk.external import ase_ext
                return ase_ext.ase_read(ioa)
            except ImportError:
                pass
        if backend == 'platon':
            try:
                from httk.external import platon_ext
                sgstruct = platon_ext.cif_to_sgstructure(ioa)
                return sgstruct.to_structure()
                #return platon_if.cif_to_structure(ioa)
            except ImportError:
                pass
        if backend == 'cif2cell':
            try:
                from httk.external import cif2cell_ext
                return cif2cell_ext.cif_to_structure_reduce(ioa)
            except ImportError:
                pass
        if backend == 'cif2cell_reduce':
            try:
                from httk.external import cif2cell_ext
                return cif2cell_ext.cif_to_structure_reduce(ioa)
            except ImportError:
                pass
        if backend == 'cif2cell_noreduce':
            try:
                from httk.external import cif2cell_ext
                return cif2cell_ext.cif_to_structure_noreduce(ioa)
            except ImportError:
                pass
        if backend == 'cif_reader_that_can_only_read_isotropy_cif':
            try:
                return cif_reader_that_can_only_read_isotropy_cif(ioa)
            except ImportError:
                pass
        if backend == 'cif_reader_httk_preprocessed':
            try:
                return cif_reader_httk_preprocessed(ioa)
            except ImportError:
                pass
    raise Exception("cif_to_struct: None of the requested / available backends available, tried:"+str(backends))


def struct_to_cif(struct, ioa, backends=['httk']):
    for backend in backends:
        if backend == 'httk':
            return struct_to_cif_httk(struct, ioa)
        if backend == 'ase':
            try:
                from httk.external import ase_glue
                return ase_glue.ase_write_struct(struct, ioa, 'cif')
            except ImportError:
                pass
    raise Exception("struct_to_cif: None of the requested / available backends available, tried:"+str(backends))


def struct_to_cif_httk(struct, ioa):
    ioa = IoAdapterFileWriter.use(ioa)
    f = ioa.file

    if struct.has_rc_repr:
        la = struct.rc_lengths_and_angles
        coordgroups = struct.rc_sites.reduced_coordgroups
        hall = struct.hall_symbol        
        sgnumber = struct.spacegroup_number
        try:
            hmsymbol = spacegroups.get_proper_hm_symbol(hall)
        except Exception:
            hmsymbol = None
    else:
        la = struct.uc_lengths_and_angles
        coordgroups = struct.uc_sites.reduced_coordgroups
        hall = 'P 1'
        sgnumber = 1
        hmsymbol = 'P 1'
    
    f.write("data_image0\n")
    f.write("_cell_length_a       "+str(float(la[0]))+"\n")
    f.write("_cell_length_b       "+str(float(la[1]))+"\n")
    f.write("_cell_length_c       "+str(float(la[2]))+"\n")
    f.write("_cell_angle_alpha    "+str(float(la[3]))+"\n")
    f.write("_cell_angle_beta     "+str(float(la[4]))+"\n")
    f.write("_cell_angle_gamma    "+str(float(la[5]))+"\n")
    f.write("\n")
    f.write("_symmetry_space_group_name_Hall      '"+str(hall)+"'\n")
    if hmsymbol is not None:
        f.write("_symmetry_space_group_name_H-M      '"+str(hmsymbol)+"'\n")
    f.write("_symmetry_Int_Tables_number          "+str(sgnumber)+"\n")
    f.write("\n")
    f.write("loop_\n")
    f.write("_atom_site_label\n")
    f.write("_atom_site_type_symbol\n")
    f.write("_atom_site_fract_x\n")
    f.write("_atom_site_fract_y\n")
    f.write("_atom_site_fract_z\n")
    f.write("_atom_site_occupancy\n")
    seen = {}
    
    for i, cg in enumerate(coordgroups):
        for coord in cg:
            x = coord[0]
            y = coord[1]
            z = coord[2]
            symbols = struct.assignments.symbollists[i]
            ratios = struct.assignments.ratioslist[i]
            for occ in range(len(symbols)):
                symbol = symbols[occ]
                ratio = ratios[occ]
                if symbol in seen:
                    seen[symbol] += 1
                    idx = seen[symbol]
                else:
                    seen[symbol] = 1
                    idx = 1
                label = symbol+str(idx)
                f.write("%s   %s  %.14f %.14f %.14f %.14f\n" % (label, symbol, float(x), float(y), float(z), float(ratio)))

    ioa.close()


def cif_reader_that_can_only_read_isotropy_cif(ioa):

    def cell_length(results, match):
        results['length_'+match.group(1)] = FracVector.create(match.group(2))

    def cell_angle(results, match):
        results['angle_'+match.group(1)] = FracVector.create(match.group(2))

    def print_hm_and_hall(results):
        grpnbr = results['grpnbr']
        setting = results['setting']
        hmsymb = results['hmfull']
        hallsymb = spacegroups.spacegroup_get_hall(str(grpnbr)+":"+setting)
        results['hall_symbol'] = hallsymb

    def hm_symbol_origin(results, match):
        results['out'] = True
        results['hmfull'] = match.group(1)
        results['hm'] = match.group(2)
        if match.group(3) == 'hexagonal axes':
            results['setting'] = '1'
        else:
            results['setting'] = str(match.group(3))
        if 'hm' in results and 'grpnbr' in results:
            print_hm_and_hall(results)

    def hm_symbol_no_origin(results, match):
        results['out'] = True
        results['hmfull'] = match.group(1)
        results['hm'] = match.group(1)
        results['setting'] = "1"
        if 'hm' in results and 'grpnbr' in results:
            print_hm_and_hall(results)

    def groupnbr(results, match):
        results['grpnbr'] = match.group(1)
        if 'hm' in results and 'grpnbr' in results:
            print_hm_and_hall(results)
        
    def coords(results, match):
        newcoord = httk.FracVector.create([match.group(5), match.group(6), match.group(7)])
        occup = {'atom': periodictable.atomic_number(match.group(2)), 'ratio': FracVector.create(match.group(8)), }
        if match.group(4) == 'alpha':
            wyckoff = '&'
        else:
            wyckoff = match.group(4)
        if newcoord in results['seen_coords']:
            idx = results['seen_coords'][newcoord]
            results['occups'][idx].append(occup)
        else:
            results['seen_coords'][newcoord] = results['idx']
            results['coords'].append(newcoord)
            results['occups'].append([occup])
            results['wyckoff'].append(wyckoff)      
            results['idx'] += 1
        
    results = {'idx': 0, 'occups': [], 'wyckoff': [], 'coords': [], 'seen_coords': {}}
    httk.basic.micro_pyawk(ioa, [
        ['^_cell_length_([^ ]*) (.*) *$', None, cell_length],
            ['^_cell_angle_([^ ]*) (.*) *$', None, cell_angle],           
            ['^_symmetry_Int_Tables_number +(.*)$', None, groupnbr],
            ['^_symmetry_space_group_name_H-M +"(([^()]+) \(origin choice ([0-9]+)\))" *$', None, hm_symbol_origin],
            ['^_symmetry_space_group_name_H-M +"(([^()]+) \((hexagonal axes)\))" *$', None, hm_symbol_origin],
            ['^_symmetry_space_group_name_H-M +"([^()]+)" *$', None, hm_symbol_no_origin],
            ['^ *([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) *$', None, coords],
    ], debug=False, results=results)

    struct = Structure.create(rc_a=results['length_a'], rc_b=results['length_b'], rc_c=results['length_c'],
                              rc_alpha=results['angle_alpha'], rc_beta=results['angle_beta'], rc_gamma=results['angle_gamma'], 
                              rc_reduced_occupationscoords=results['coords'], rc_occupancies=results['occups'], 
                              spacegroup=results['hall_symbol'], wyckoff_symbols=results['wyckoff'])
    return struct


def cif_reader_httk_preprocessed(ioa):
    ioa = IoAdapterStringList.use(ioa)
    for i in range(len(ioa.stringlist)):
        if ioa.stringlist[i].startswith("INPUT"):
            ioa.stringlist[i] = ""
    newstruct = cif_to_struct(ioa, backends=['cif2cell_reduce'])        
    for i in range(len(ioa.stringlist)):
        if ioa.stringlist[i].startswith("# Data extracted using the FINDSYM utility follows"):
            ioa.stringlist = ioa.stringlist[i:]
            break
    only_rc_struct = cif_to_struct(ioa, backends=['cif_reader_that_can_only_read_isotropy_cif'])
    if only_rc_struct.assignments.hexhash != newstruct.assignments.hexhash:
        # This happens IF the rc representation is broken due to the use of 
        # different but equivalent sites. In this case we have already lost, and need
        # to return only the "proper" structure in newstruct. This will cause us to loose
        # Wyckoff information, but for now I see now way of rescuing this.
        # This will all be solved when we implement our own cif reader.
        return newstruct
    
    newstruct.rc_sites.wyckoff_symbols = only_rc_struct.rc_sites.wyckoff_symbols
    
    # Cell basis can only be constructed from the cif approximately
    only_rc_struct._rc_cell = newstruct._rc_cell
    # Make sure the hexhash is recomputed
    only_rc_struct.rc_sites._hexhash = None
    #print "CHECK THIS:", newstruct.rc_sites.hexhash, only_rc_struct.rc_sites.hexhash
    #print "CHECK THIS:", newstruct.cellobj.to_tuple(), only_rc_struct.cellobj.to_tuple()
    if newstruct.rc_sites.hexhash != only_rc_struct.rc_sites.hexhash:
        #print "Cell mismatch:",cell_mismatch
        print "Structure hashes:", newstruct.rc_sites.hexhash, only_rc_struct.rc_sites.hexhash
        #print "Structures:", newstruct.rc_sites.to_tuple(), only_rc_struct.rc_sites.to_tuple()
        raise Exception("isotropy_ext.struct_process_with_isotropy: internal error, structures that absolutely should be the same are not, sorry.")       
    return newstruct

    
