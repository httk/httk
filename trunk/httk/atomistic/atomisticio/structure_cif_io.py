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

import os, hashlib, random, string
from collections import OrderedDict 
import httk, httk.io

from httk.atomistic.data import periodictable, spacegroups
from httk.core import *
from httk.atomistic import Structure, Spacegroup

def cif_to_struct(ioa,backends=['internal','cif2cell','ase','platon']):
    for backend in backends:
        #print "CIF TO STRUCT BACKEND",backend
        if backend == 'internal':
            try:
                cifdata, cifheader = httk.io.read_cif(ioa)
                return cifdata_to_struct(cifdata)
            except ImportError:
                pass
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
            return struct_to_cif_httk(struct,ioa)
        if backend == 'ase':
            try:
                from httk.external import ase_glue
                return ase_glue.ase_write_struct(struct, ioa, 'cif')
            except ImportError:
                pass
    raise Exception("struct_to_cif: None of the requested / available backends available, tried:"+str(backends))



def struct_to_cif_httk(struct, ioa, header=None):
    ioa = IoAdapterFileWriter.use(ioa)
    f = ioa.file

    wyckoffsymbols = None
    if struct.has_rc_repr:
        la = struct.rc_lengths_and_angles
        coordgroups = struct.rc_sites.reduced_coordgroups
        hall = struct.hall_symbol        
        sgnumber = struct.spacegroup_number
        try:
            hmsymbol = spacegroups.get_proper_hm_symbol(hall)
        except Exception:
            hmsymbol = None
        multiplicities = struct.rc_sites.multiplicities
        wyckoffsymbols = struct.rc_sites.wyckoff_symbols
    else:
        la = struct.uc_lengths_and_angles
        coordgroups = struct.uc_sites.reduced_coordgroups
        hall = 'P 1'
        sgnumber = 1
        hmsymbol = 'P 1'

    if header != None:
        f.write(header)
        f.write("\n")
    
    f.write("data_image0\n")
    f.write("\n")
    try:
        if struct.get_tag('name') != None:
            f.write("_chemical_name_systematic '"+struct.get_tag('name').value+"'\n")   
    except Exception:
        pass
    if struct.has_uc_repr:
        f.write("_chemical_formula_sum '"+struct.uc_formula_spaceseparated+"'\n")    
    f.write("\n")
    f.write("_cell_length_a       "+str(float(la[0]))+"\n")
    f.write("_cell_length_b       "+str(float(la[1]))+"\n")
    f.write("_cell_length_c       "+str(float(la[2]))+"\n")
    f.write("_cell_angle_alpha    "+str(float(la[3]))+"\n")
    f.write("_cell_angle_beta     "+str(float(la[4]))+"\n")
    f.write("_cell_angle_gamma    "+str(float(la[5]))+"\n")
    f.write("\n")
    f.write("_symmetry_space_group_name_Hall      '"+str(hall)+"'\n")
    if hmsymbol != None:
        f.write("_symmetry_space_group_name_H-M      '"+str(hmsymbol)+"'\n")
    f.write("_symmetry_Int_Tables_number          "+str(sgnumber)+"\n")
    f.write("\n")
    f.write("loop_\n")
    f.write("_atom_site_label\n")
    f.write("_atom_site_type_symbol\n")
    if wyckoffsymbols != None:
        f.write("_atom_site_symmetry_multiplicity\n")
        f.write("_atom_site_Wyckoff_symbol\n")
    f.write("_atom_site_fract_x\n")
    f.write("_atom_site_fract_y\n")
    f.write("_atom_site_fract_z\n")
    f.write("_atom_site_occupancy\n")
    seen = {}
    
    for i,cg in enumerate(coordgroups):
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
                    seen[symbol]+=1
                    idx = seen[symbol]
                else:
                    seen[symbol]=1
                    idx = 1
                label = symbol+str(idx)
                if wyckoffsymbols != None:
                    multiplicity = multiplicities[i]
                    wyckoffsymbol = wyckoffsymbols[i]
                    f.write("%s   %s  %d %s %.14f %.14f %.14f %.14f\n" % (label, symbol, multiplicity, wyckoffsymbol, float(x), float(y), float(z), float(ratio)))
                else:
                    f.write("%s   %s  %.14f %.14f %.14f %.14f\n" % (label, symbol, float(x), float(y), float(z), float(ratio)))

    ioa.close()

def cif_reader_that_can_only_read_isotropy_cif(ioa):

    def cell_length(results, match):
        results['length_'+match.group(1)]=FracVector.create(match.group(2))

    def cell_angle(results, match):
        results['angle_'+match.group(1)]=FracVector.create(match.group(2))

    def print_hm_and_hall(results):
        grpnbr=results['grpnbr']
        setting=results['setting']
        hmsymb=results['hmfull']
        hallsymb=spacegroups.spacegroup_get_hall(str(grpnbr)+":"+setting)
        results['hall_symbol']=hallsymb

    def hm_symbol_origin(results,match):
        results['out']=True
        results['hmfull']=match.group(1);
        results['hm']=match.group(2);
        if match.group(3)=='hexagonal axes':
            results['setting']='1';
        else:
            results['setting']=str(match.group(3));
        if 'hm' in results and 'grpnbr' in results:
            print_hm_and_hall(results)

    def hm_symbol_no_origin(results,match):
        results['out']=True
        results['hmfull']=match.group(1);
        results['hm']=match.group(1);
        results['setting']="1";
        if 'hm' in results and 'grpnbr' in results:
            print_hm_and_hall(results)

    def groupnbr(results,match):
        results['grpnbr']=match.group(1);
        if 'hm' in results and 'grpnbr' in results:
            print_hm_and_hall(results)
        
    def coords(results,match):
        newcoord = httk.FracVector.create([match.group(5),match.group(6),match.group(7)])
        occup = {'atom':periodictable.atomic_number(match.group(2)),'ratio':FracVector.create(match.group(8)),}
        if match.group(4) == 'alpha':
            wyckoff='&'
        else:
            wyckoff=match.group(4)
        multiplicities = int(match.group(3))            
        if newcoord in results['seen_coords']:
            idx = results['seen_coords'][newcoord]
            results['occups'][idx].append(occup)
        else:
            results['seen_coords'][newcoord] = results['idx']
            results['coords'].append(newcoord)
            results['occups'].append([occup])
            results['wyckoff'].append(wyckoff)      
            results['multiplicities'].append(multiplicities)      
            results['idx'] += 1
        
    results = {'idx':0, 'occups':[], 'wyckoff':[],'multiplicities':[],'coords':[],'seen_coords':{}}
    httk.basic.micro_pyawk(ioa,[
            ['^_cell_length_([^ ]*) (.*) *$',None,cell_length],
            ['^_cell_angle_([^ ]*) (.*) *$',None,cell_angle],           
            ['^_symmetry_Int_Tables_number +(.*)$',None,groupnbr],
            ['^_symmetry_space_group_name_H-M +"(([^()]+) \(origin choice ([0-9]+)\))" *$',None,hm_symbol_origin],
            ['^_symmetry_space_group_name_H-M +"(([^()]+) \((hexagonal axes)\))" *$',None,hm_symbol_origin],
            ['^_symmetry_space_group_name_H-M +"([^()]+)" *$',None,hm_symbol_no_origin],
            ['^ *([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) *$',None,coords],
            ],debug=False,results=results)

    struct = Structure.create(rc_a=results['length_a'],rc_b=results['length_b'],rc_c=results['length_c'],
                              rc_alpha=results['angle_alpha'],rc_beta=results['angle_beta'],rc_gamma=results['angle_gamma'], 
                              rc_reduced_occupationscoords=results['coords'], rc_occupancies=results['occups'], 
                              spacegroup=results['hall_symbol'],wyckoff_symbols=results['wyckoff'],multiplicities=results['multiplicities'])
    return struct

def cif_reader_httk_preprocessed(ioa):
    ioa = IoAdapterStringList.use(ioa)
    for i in range(len(ioa.stringlist)):
        if ioa.stringlist[i].startswith("INPUT"):
            ioa.stringlist[i]=""
    newstruct = cif_to_struct(ioa,backends=['cif2cell_reduce'])        
    for i in range(len(ioa.stringlist)):
        if ioa.stringlist[i].startswith("# Data extracted using the FINDSYM utility follows"):
            ioa.stringlist=ioa.stringlist[i:]
            break
    only_rc_struct = cif_to_struct(ioa,backends=['cif_reader_that_can_only_read_isotropy_cif'])
    if only_rc_struct.assignments.hexhash != newstruct.assignments.hexhash:
        # This happens IF the rc representation is broken due to the use of 
        # different but equivalent sites. In this case we have already lost, and need
        # to return only the "proper" structure in newstruct. This will cause us to loose
        # Wyckoff information, but for now I see now way of rescuing this.
        # This will all be solved when we implement our own cif reader.
        return newstruct
    
    newstruct.rc_sites.wyckoff_symbols=only_rc_struct.rc_sites.wyckoff_symbols
    
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

def cifdata_to_struct(cifdata):
    #import pprint
    #pp = pprint.PrettyPrinter()
    if len(cifdata) > 1:
        raise Exception("httk.atomistic.atomisticio.structure_cif_io: cifdata to struct with more than one image in cifdata.")
    element = cifdata[0][1]
    #del element['symmetry_equiv_pos_as_xyz']
    #pp.pprint(dict(element))

    rc_lengths = FracVector.create([element['cell_length_a'],element['cell_length_b'],element['cell_length_c']])
    rc_angles = FracVector.create([element['cell_angle_alpha'],element['cell_angle_beta'],element['cell_angle_gamma']])

    hall_symbol = None
    hm_symbol = None
    spacegroupnumber = None
    setting = None
    symops = None
    if 'symmetry_space_group_name_hall' in element:
        hall_symbol = element['symmetry_space_group_name_hall']
    elif '_space_group_symop_operation_xyz' in element:
        symops = element['_space_group_symop_operation_xyz']
    elif 'symmetry_space_group_name_h-m' in element:
        hm_symbol = element['symmetry_space_group_name_h-m']
    elif 'symmetry_Int_Tables_number' in element:
        spacegroupnumber = int(element['symmetry_Int_Tables_number'])
        # cif verb symmetry_cell_setting really isn't what it seems, it is useless here
        #if 'symmetry_cell_setting' in element:
        #    setting = element['symmetry_cell_setting']
        #else:
        sys.stderr.write("Warning: reading cif data for structure, only spacegroup number given without setting information. Standard setting assumed.\n")

    spacegroup = Spacegroup.create(hall_symbol=hall_symbol, hm_symbol=hm_symbol, spacegroupnumber=spacegroupnumber, setting=setting, symops=symops)

    rc_occupancies = []
    rc_reduced_occupationscoords = []
    wyckoff_symbols = None
    multiplicities = None
    if 'atom_site_wyckoff_symbol' in element:
        wyckoff_symbols = element['atom_site_wyckoff_symbol']
    if 'atom_site_symmetry_multiplicity' in element:
        multiplicities = [int(x) for x in element['atom_site_symmetry_multiplicity']]
    
    for atom in range(len(element['atom_site_label'])):
        if 'atom_site_occupancy' in element:
            ratio = element['atom_site_occupancy'][atom]
        else:
            ratio = 1
        symbol = element['atom_site_label'][atom].rstrip('1234567890')
        
        occup = {'atom':periodictable.atomic_number(symbol),'ratio':FracVector.create(ratio),}
        coord = [element['atom_site_fract_x'][atom],element['atom_site_fract_y'][atom],element['atom_site_fract_z'][atom]]

        rc_occupancies += [occup]
        rc_reduced_occupationscoords += [coord]

    #print "X",rc_lengths,rc_angles,rc_reduced_occupationscoords,rc_occupancies,spacegroup,setting,wyckoff_symbols,multiplicities

    tags = {}
    if 'chemical_name_common' in element:
        tags['name'] = element['chemical_name_common']
    elif 'chemical_name_systematic' in element:
        tags['name'] = element['chemical_name_systematic']

    authorlist = None
    if 'publ_author_name' in element:
        authorlist = []
        authors = element['publ_author_name']
        if not basic.is_sequence(authors):
            authors = [authors]
        for author in authors:
            authorparts = author.partition(",")
            lastname = authorparts[0].strip()
            givennames = authorparts[2].strip()
            authorlist += [Author.create(lastname,givennames)]

    # I didn't find this in the spec, on the other hand, the publ_ space is "not specified", so, this seems
    # as a logical extension of the author list in case of a cif file that has been published in a book.
    # I see no harm in including it, at least.
    editorlist = None
    if 'publ_editor_name' in element:
        editorlist = []
        editors = element['publ_editor_name']
        if not basic.is_sequence(editors):
            editors = [editors]
        for editor in editors:
            editorparts = editor.partition(",")
            lastname = editorparts[0].strip()
            givennames = editorparts[2].strip()
            editorlist += [Author.create(lastname,givennames)]
        
    refs = None
    if 'journal_name_full' in element or 'journal_name_abbrev' in element:
        journal = None
        journal_page_first = None
        journal_page_last = None    
        journal_volume = None
        journal_title = None
        journal_book_title = None
        journal_issue = None
        journal_publisher=None
        journal_publisher_city = None
        if 'journal_name_abbrev' in element:
            journal = element['journal_name_abbrev']
        if 'journal_name_full' in element:
            journal = element['journal_name_full']
        if 'journal_page_first' in element:
            journal_page_first = element['journal_page_first']
        if 'journal_page_last' in element:
            journal_page_last = element['journal_page_last']
        if 'journal_volume' in element:
            journal_volume = element['journal_volume']
        if 'journal_issue' in element:
            journal_issue = element['journal_issue']
        if 'journal_title' in element:
            journal_title = element['journal_title']
        if 'journal_book_title' in element:
            journal_book_title = element['journal_book_title']
        if 'journal_year' in element:
            journal_year = element['journal_year']
        if 'journal_publisher' in element:
            journal_publisher = element['journal_publisher']
        if 'journal_publisher_city' in element:
            journal_publisher_city = element['journal_publisher_city']
        if 'journal_book_publisher' in element:
            journal_publisher = element['journal_book_publisher']
        if 'journal_book_publisher_city' in element:
            journal_publisher_city = element['journal_book_publisher_city']
        
        refs = [Reference.create(authors=authorlist, editors=editorlist, journal=journal, journal_issue=journal_issue, journal_volume=journal_volume, 
                 page_first=journal_page_first, page_last=journal_page_last, title=journal_title, year=journal_year, book_publisher=journal_publisher,
                 book_publisher_city=journal_publisher_city, book_title=journal_book_title)]

    # This is based on some assumptions... IF a journal_* type tree exists, then we assume this is a 'published' cif, and
    # in that case the only reference we want to keep is the one to the published work. Citations in the citation_* tree is going to be
    # all the citations from that paper, which we do not want, *unless* they mark citation_coordinate_linkage. However, 
    # if no journal_* tree exists, then this is a 'generic' structure cif, where the citations should point to all publications of 
    # this structure; and we don't want to assume 'citation_coordinate_linkage'
    add_all_citations = False
    if refs == None or len(refs) == 0:
        add_all_citations = True

    if 'citation_journal_full' in element or 'citation_journal_abbrev' in element or 'citation_book_title' in element:
        if refs == None:
            refs = []
        if 'citation_journal_full' in element:
            N = len(element['citation_journal_full'])
        elif 'citation_journal_abbrev' in element:
            N = len(element['citation_journal_abbrev'])
        elif 'citation_book_title' in element:
            N = len(element['citation_book_title'])
        for i in range(N):
            if not add_all_citations and ('citation_coordinate_linkage' not in element or (element['citation_coordinate_linkage'].lower() != 'yes' and element['citation_coordinate_linkage'].lower() != 'y')):
                continue
            journal = None
            journal_page_first = None
            journal_page_last = None    
            journal_volume = None
            journal_title = None
            journal_book_title = None
            journal_issue = None
            journal_publisher=None
            journal_publisher_city = None
            if 'citation_journal_full' in element:
                journal = element['citation_journal_full'][i]
            if 'citation_journal_abbrev' in element:
                journal = element['citation_journal_abbrev'][i]
            if 'citation_page_first' in element:
                journal_page_first = element['citation_page_first'][i]
            if 'citation_page_last' in element:
                journal_page_last = element['citation_page_last'][i]
            if 'citation_journal_volume' in element:
                journal_volume = element['citation_journal_volume'][i]
            if 'citation_journal_issue' in element:
                journal_issue = element['citation_journal_issue'][i]
            if 'citation_title' in element:
                journal_title = element['citation_title'][i]
            if 'citation_book_title' in element:
                journal_book_title = element['citation_book_title'][i]
            if 'journal_year' in element:
                journal_year = element['journal_year'][i]
            if 'citation_book_publisher' in element:
                journal_publisher = element['citation_book_publisher'][i]
            if 'citation_book_publisher_city' in element:
                journal_publisher_city = element['citation_book_publisher_city'][i]
            
            refs += [Reference.create(authors=authorlist, editors=editorlist, journal=journal, journal_issue=journal_issue, journal_volume=journal_volume, 
                     page_first=journal_page_first, page_last=journal_page_last, title=journal_title, year=journal_year, book_publisher=journal_publisher,
                     book_publisher_city=journal_publisher_city, book_title=journal_book_title)]

                            
    struct = Structure.create(rc_lengths=rc_lengths,
                              rc_angles=rc_angles, 
                              rc_reduced_occupationscoords=rc_reduced_occupationscoords, 
                              rc_occupancies=rc_occupancies, 
                              spacegroup=spacegroup, setting=setting, 
                              periodicity=0, 
                              wyckoff_symbols=wyckoff_symbols,multiplicities=multiplicities, tags=tags, refs=refs)
    
    return struct
    

def struct_to_cifdata(struct,entryid=None):
    entry = OrderedDict()
        
    wyckoffsymbols = None
    if struct.has_rc_repr:
        la = struct.rc_lengths_and_angles
        coordgroups = struct.rc_sites.reduced_coordgroups
        hall = struct.hall_symbol        
        sgnumber = struct.spacegroup_number
        try:
            hmsymbol = spacegroups.get_proper_hm_symbol(hall)
        except Exception:
            hmsymbol = None
        multiplicities = struct.rc_sites.multiplicities
        wyckoffsymbols = struct.rc_sites.wyckoff_symbols
    else:
        la = struct.uc_lengths_and_angles
        coordgroups = struct.uc_sites.reduced_coordgroups
        hall = 'P 1'
        sgnumber = 1
        hmsymbol = 'P 1'
        
    try:
        if struct.get_tag('name') != None:
            entry["chemical_name_common"]=struct.get_tag('name').value   
    except Exception:
        pass
    if struct.has_uc_repr:
        entry["chemical_formula_sum"]=struct.uc_formula_spaceseparated    

    entry["cell_length_a"]=str(float(la[0]))
    entry["cell_length_b"]=str(float(la[1]))
    entry["cell_length_c"]=str(float(la[2]))
    entry["cell_angle_alpha"]=str(float(la[3]))
    entry["cell_angle_beta"]=str(float(la[4]))
    entry["cell_angle_gamma"]=str(float(la[5]))

    entry["symmetry_space_group_name_hall"] = str(hall)
    if hmsymbol != None:
        entry["symmetry_space_group_name_h-m"] = str(hmsymbol)
        entry["symmetry_Int_Tables_number"] = str(sgnumber)
        # Add setting
        
    entry["symmetry_space_group_name_hall"] = str(hall)

    refs = struct.get_refs()
    if len(refs)>0:
        entry["loop_1"] = ["citation_id",
                           "citation_journal_full","citation_journal_issue","citation_journal_volume",
                           "citation_page_first","citation_page_last",
                           "citation_title","citation_year","citation_book_publisher",
                           "citation_book_publisher_city","citation_book_title","citation_coordinate_linkage"]
        entry["loop_2"] = ["citation_author_citation_id","citation_author_name"]
        entry["loop_3"] = ["citation_editor_citation_id","citation_editor_name"]
        for key in entry["loop_1"] + entry['loop_2'] + entry['loop_3']:
            entry[key] = []
        for i in range(len(refs)):
            data = {}
            ref = refs[i].reference
            data['citation_id'] = str(i)
            data["citation_journal_full"] = ref.journal
            data['citation_journal_issue'] = ref.journal_issue
            data['citation_journal_volume'] = ref.journal_volume
            data['citation_page_first'] = ref.page_first
            data['citation_page_last'] = ref.page_last
            data['citation_title'] = ref.title
            data['citation_year'] = ref.year
            data['citation_book_publisher'] = ref.book_publisher
            data['citation_book_publisher_city'] = ref.book_publisher_city 
            data['citation_book_title'] = ref.book_title
            data['citation_coordinate_linkage'] = "yes"
            for key in entry["loop_1"]:
                entry[key] += [data[key]]
            if ref.authors != None:
                for author in ref.authors:
                    entry['citation_author_citation_id'] += [str(i)]
                    entry['citation_author_name'] += [author.last_name + ", "+author.given_names]
            if ref.editors != None:
                for editor in ref.editors:
                    entry['citation_editor_citation_id'] += [str(i)]
                    entry['citation_author_name'] += [editor.last_name + ", "+editor.given_names]


        if 'citation_author_citation_id' in entry and len(entry['citation_author_citation_id'])==0:
                del entry['citation_author_citation_id']
                del entry['citation_author_name']
                del entry['loop_2']

        if 'citation_editor_citation_id' in entry and len(entry['citation_editor_citation_id'])==0:
                del entry['citation_editor_citation_id']
                del entry['citation_editor_name']
                del entry['loop_3']

    entry["loop_0"] = ["atom_site_label","atom_site_type_symbol"]
    if wyckoffsymbols != None:
        entry["loop_0"] += ["atom_site_symmetry_multiplicity","atom_site_Wyckoff_symbol"]
    entry["loop_0"] += ["atom_site_fract_x","atom_site_fract_y","atom_site_fract_z","atom_site_occupancy"]

    for key in entry["loop_0"]:
        entry[key] = []

    seen = {}
    
    for i,cg in enumerate(coordgroups):
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
                    seen[symbol]+=1
                    idx = seen[symbol]
                else:
                    seen[symbol]=1
                    idx = 1
                label = symbol+str(idx)
                if wyckoffsymbols != None:
                    multiplicity = multiplicities[i]
                    wyckoffsymbol = wyckoffsymbols[i]
                    data = (label, symbol, multiplicity, wyckoffsymbol, float(x), float(y), float(z), float(ratio))
                else:
                    data = (label, symbol, float(x), float(y), float(z), float(ratio))
                for j in range(len(entry["loop_0"])):
                    entry[entry["loop_0"][j]] += [data[j]]


    if entryid == None:
        entryid = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))    
    cifdata = [(entryid, entry)]
    
    return cifdata

