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

import string
from fractions import Fraction

from httk.atomistic.data import periodictable
from httk.core import FracVector
import httk  
from httk.atomistic import *


def out_to_struct(ioa):
    """
    Example input::
    
        OUTPUT CELL INFORMATION
        Symmetry information:
        Trigonal crystal system.
        Space group number     : 165
        Hall symbol            : -P 3 2"c
        Hermann-Mauguin symbol : P-3c1
        
        Bravais lattice vectors :
          0.8660254  -0.5000000   0.0000000 
          0.0000000   1.0000000   0.0000000 
          0.0000000   0.0000000   1.0231037 
        All sites, (lattice coordinates):
        Atom           a1          a2          a3 
        La      0.6609000   0.0000000   0.2500000
        La      0.3391000   0.0000000   0.7500000
        ...
        F       0.0000000   0.0000000   0.2500000
        F       0.0000000   0.0000000   0.7500000
        
        Unit cell volume  : 328.6477016 A^3
        Unit cell density :   3.5764559 u/A^3 =   5.9388437 g/cm^3
    """
    results = {}
    results['output_cell'] = []
    results['input_cell'] = []
    results['coords'] = []
    results['sgcoords'] = []
    results['occupancies'] = []
    results['sgoccupancies'] = []
    results['in_output'] = False
    results['in_input'] = False
    results['in_input_coords'] = False
    results['in_coords'] = False
    results['in_cell'] = False
    results['in_input_cell'] = False
    results['in_bib'] = False
    results['bib'] = ""
    results['seen'] = {}
    results['sgseen'] = {}
    results['idx'] = 0
    results['sgidx'] = 0
    
    def read_cell(results, match):
        if results['in_input']:
            results['input_cell'].append([(match.group(1)), (match.group(2)), (match.group(3))])
        elif results['in_output']:
            results['output_cell'].append([(match.group(1)), (match.group(2)), (match.group(3))])

    def read_coords_occs(results, match):
        if results['in_input']:
            coordstr = 'sgcoords'
            occstr = 'sgoccupancies'
            seenstr = 'sgseen'
            idxstr = 'sgidx'
        elif results['in_output']:
            coordstr = 'coords'
            occstr = 'occupancies'
            seenstr = 'seen'
            idxstr = 'idx'
        else:
            return

        newcoord = (match.group(2), match.group(3), match.group(4))
        #newcoord = FracVector.create([match.group(2),match.group(3),match.group(4)]).limit_denominator(5000000).simplify()
        species = match.group(1).split("/")
        occups = match.group(6).split("/")

        for j in range(len(species)):        
            occup = {'atom': periodictable.atomic_number(species[j]), 'ratio': FracVector.create(occups[j]), }
    
            if newcoord in results[seenstr]:
                idx = results[seenstr][newcoord]
                #print "OLD",results[occstr],idx
                results[occstr][idx].append(occup)
            else:
                results[seenstr][newcoord] = results[idxstr]
                results[coordstr].append(newcoord)
                results[occstr].append([occup])
                results[idxstr] += 1
                #print "NEW",results[occstr],results[idxstr]
                          
    def read_coords(results, match):
        if results['in_input']:
            coordstr = 'sgcoords'
            occstr = 'sgoccupancies'
            seenstr = 'sgseen'
            idxstr = 'sgidx'
        elif results['in_output']:
            coordstr = 'coords'
            occstr = 'occupancies'
            seenstr = 'seen'
            idxstr = 'idx'
        else:
            return

        newcoord = (match.group(2), match.group(3), match.group(4))
        #newcoord = FracVector.create([match.group(2),match.group(3),match.group(4)]).limit_denominator(5000000).simplify()
        species = match.group(1)
        occup = {'atom': periodictable.atomic_number(species)}        

        if newcoord in results[seenstr]:
            idx = results[seenstr][newcoord]
            #print "XOLD",results[occstr],idx
            results[occstr][idx].append(occup)
        else:
            results[seenstr][newcoord] = results[idxstr]
            results[coordstr].append(newcoord)
            results[occstr].append([occup])
            results[idxstr] += 1
            #print "XNEW",results[occstr],results['idx']

        #if results['in_input']:
        #    results['sgcoords'].append(newcoord)
        #    results['sgoccupancies'].append(periodictable.atomic_symbol(match.group(1)))
        #elif results['in_output']:
        #    results['coords'].append(newcoord)
        #    results['occupancies'].append(periodictable.atomic_symbol(match.group(1)))
 
    def read_volume(results, match):
        results['volume'] = match.group(1)

    def read_hall(results, match):
        if results['in_input']:
            results['sghall'] = match.group(1)
        elif results['in_output']:
            results['hall'] = match.group(1)

    def read_id(results, match):
        results['id'] = match.group(1)

    def coords_stop(results, match):
        results['in_coords'] = False

    def coords_start(results, match):
        if results['in_input']:
            results['in_input_coords'] = True
        elif results['in_output']:
            results['in_coords'] = True

    def cell_stop(results, match):
        results['in_cell'] = False

    def input_cell_stop(results, match):
        results['in_input_cell'] = False

    def cell_start(results, match):
        results['in_cell'] = True

    def input_cell_start(results, match):
        results['in_input_cell'] = True

    def output_start(results, match):
        results['in_output'] = True        
        results['in_input'] = False

    def read_version(results, match):
        results['version'] = match.group(1)

    def read_name(results, match):
        expr = httk.basic.parse_parexpr(match.group(1))
        # Grab the last, nested, parenthesed expression 
        p = ""
        for x in expr:
            if x[0] == 0:
                p = x[1]
        results['name'] = p

    def read_bib(results, match):
        if match.group(1).strip() != 'Failed to get author information, No journal information':
            results['bib'] += match.group(1).strip()

    def bib_start(results, match):
        results['in_bib'] = True

    def bib_stop_input_start(results, match):
        results['in_bib'] = False
        results['in_input'] = True

    def read_source(results, match):        
        results['source'] = match.group(1).rstrip('.')
                
    out = httk.basic.micro_pyawk(ioa, [
        ['^ *INPUT CELL INFORMATION *$', None, bib_stop_input_start],
        ['^ *CIF2CELL ([0-9.]*)', None, read_version],
        ['^ *Output for (.*\)) *$', None, read_name],
        ['^ *Database reference code: *([0-9]+)', None, read_id],
        ['^ *All sites, (lattice coordinates): *$', lambda results, match: results['in_cell'], cell_stop],
        ['^ *Representative sites *: *$', lambda results, match: results['in_input_cell'], input_cell_stop],
        ['^ *$', lambda results, match: results['in_coords'], coords_stop],
        ['^ *([-0-9.]+) +([-0-9.]+) +([-0-9.]+) *$', lambda results, match: results['in_cell'] or results['in_input_cell'], read_cell],
        ['^ *([a-zA-Z]+) +([-0-9.]+) +([-0-9.]+) +([-0-9.]+) *$', lambda results, match: results['in_coords'] or results['in_input_coords'], read_coords],
        ['^ *([a-zA-Z/]+) +([-0-9.]+) +([-0-9.]+) +([-0-9.]+)( +([-0-9./]+)) *$', lambda results, match: results['in_coords'] or results['in_input_coords'], read_coords_occs],
        #            ['^ *Hermann-Mauguin symbol *: *(.*)$',lambda results,match: results['in_output'],read_spacegroup],
        ['^ *Hall symbol *: *(.*)$', lambda results, match: results['in_output'] or results['in_input'], read_hall],
        ['^ *Unit cell volume *: *([-0-9.]+) +A\^3 *$', lambda results, match: results['in_output'], read_volume],
        ['^ *Bravais lattice vectors : *$', lambda results, match: results['in_output'], cell_start],
        ['^ *Lattice parameters: *$', lambda results, match: results['in_input'], input_cell_start],
        ['^ *Atom +a1 +a2 +a3', lambda results, match: results['in_output'] or results['in_input'], coords_start],
        ['^ *OUTPUT CELL INFORMATION *$', None, output_start],
        ['^([^\n]*)$', lambda results, match: results['in_bib'], read_bib],
        ['^ *BIBLIOGRAPHIC INFORMATION *$', None, bib_start],
        ['CIF file exported from +(.*) *$', None, read_source]
          
    ], debug=False, results=results)

    out['bib'] = out['bib'].strip()

    rc_a, rc_b, rc_c = [float(x) for x in out['input_cell'][0]]
    rc_alpha, rc_beta, rc_gamma = [float(x) for x in out['input_cell'][1]]

    uc_a, uc_b, uc_c = [float(x) for x in out['output_cell'][0]]
    uc_alpha, uc_beta, uc_gamma = [float(x) for x in out['output_cell'][1]]

    rc_cell = FracVector.create(out['input_cell'])
    uc_cell = FracVector.create(out['output_cell'])
    coords = FracVector.create(out['coords']).limit_denominator(5000000).simplify()
    sgcoords = FracVector.create(out['sgcoords']).limit_denominator(5000000).simplify()

    hall_symbol = out['hall']
    sghall_symbol = out['sghall']
    tags = {}
    if 'source' in out:
        tags['source'] = out['source']+":"+out['id']
    if 'bib' in out and out['bib'] != '':
        refs = [out['bib']]
    else:
        refs = None
    if 'name' in out:
        tags['name'] = filter(lambda x: x in string.printable, out['name'])

    # This is to handle a weird corner case, where atoms in a disordered structure
    # are placed on equivalent but different sites in the representative representation; then
    # they will be mapped to the same sites in the filled cell. Our solution in that case is
    # to throw away the rc_cell, since it is incorrect - it has equivalent sites that appear
    # different even though they are the same.
    remaining_filled_sites = list(out['occupancies'])
    for i in range(len(out['sgoccupancies'])):
        if out['sgoccupancies'][i] in remaining_filled_sites:
            remaining_filled_sites = filter(lambda a: a != out['sgoccupancies'][i], remaining_filled_sites)
    if len(remaining_filled_sites) > 0:
        rc_cell_broken = True
    else:
        rc_cell_broken = False

    if not rc_cell_broken:    
        struct = Structure.create(rc_lengths=rc_cell[0],
                                  rc_angles=rc_cell[1], 
                                  rc_reduced_occupationscoords=sgcoords, 
                                  uc_cell=uc_cell,
                                  uc_reduced_occupationscoords=coords, 
                                  uc_volume=out['volume'],
                                  rc_occupancies=out['sgoccupancies'], 
                                  uc_occupancies=out['occupancies'], 
                                  spacegroup=sghall_symbol, 
                                  tags=tags, refs=refs, periodicity=0)
    else:
        struct = Structure.create(uc_cell=uc_cell,
                                  uc_reduced_occupationscoords=coords, 
                                  uc_volume=out['volume'],
                                  uc_occupancies=out['occupancies'], 
                                  spacegroup=sghall_symbol, 
                                  tags=tags, refs=refs, periodicity=0)        

    # A bit of santiy check to trigger on possible bugs from cif2cell
    if len(struct.uc_sites.counts) != len(struct.rc_sites.counts):
        print struct.uc_sites.counts, struct.rc_sites.counts
        raise Exception("cif2cell_if.out_to_struct: non-sensible parsing of cif2cell output.")

    #if 'volume' in out:
    #    vol = FracVector.create(out['volume'])
    #else:
    #    volstruct = httk.Structure.create(a=a,b=b,c=c,alpha=alpha,beta=beta,gamma=gamma, occupancies=out['sgoccupancies'], coords=sgcoords, hall_symbol=sghall_symbol, refs=refs)
    #    vol = volstruct.volume

    #struct = httk.Structure.create(cell,occupancies=out['occupancies'],coords=coords,volume=vol,tags=tags,hall_symbol=hall_symbol, refs=refs)
    #struct._sgstructure = httk.SgStructure.create(a=a,b=b,c=c,alpha=alpha,beta=beta,gamma=gamma, occupancies=out['sgoccupancies'], coords=sgcoords, hall_symbol=sghall_symbol)
    #print "HERE WE ARE:",out['sgoccupancies'],sgcoords,sghall_symbol
    #print "HERE WE ARE:",out['occupancies'],coords
    #struct = httk.Structure.create(cell, volume=vol, unique_occupations=out['sgoccupancies'], uc_occupations=out['occupancies'], unique_reduced_occupationscoords=sgcoords, uc_reduced_occupationscoords=coords, spacegroup=sghall_symbol, tags=tags, refs=refs, periodicity=0)
    #print "HERE",sgcoords, coords
    #counts = [len(x) for x in out['occupancies']]
    #p1structure = httk.Structure.create(cell,occupancies=out['occupancies'],coords=coords,volume=vol,tags=tags, refs=refs, periodicity=0)
    #struct.set_p1structure(p1structure)

    return struct
    


