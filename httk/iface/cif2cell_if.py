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

import string

from httk.core.htdata import periodictable
from httk.core import FracVector
import httk  

def out_to_struct(ioa):
    """
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
    results={}
    results['cell'] = []
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

    def read_cell(results,match):
        if results['in_input']:
            results['input_cell'].append([(match.group(1)),(match.group(2)),(match.group(3))])
        elif results['in_output']:
            results['cell'].append([(match.group(1)),(match.group(2)),(match.group(3))])

    def read_coords_occs(results,match):
        if results['in_input']:
            coordstr = 'sgcoords'
            occstr = 'sgoccupancies'
        elif results['in_output']:
            coordstr = 'coords'
            occstr = 'occupancies'
        else:
            return

        newcoord = httk.FracVector.create([match.group(2),match.group(3),match.group(4)])
        results[coordstr].append(newcoord)
        
        species = match.group(1).split("/")
        occups = match.group(6).split("/")

        occ = []                    
        for j in range(len(species)):        
            occ.append((periodictable.atomic_symbol(species[j]),FracVector.create(occups[j]),))
            
        results[occstr].append(occ)
            
    def read_coords(results,match):
        newcoord = FracVector.create([match.group(2),match.group(3),match.group(4)])
        if results['in_input']:
            results['sgcoords'].append(newcoord)
            results['sgoccupancies'].append(periodictable.atomic_symbol(match.group(1)))
        elif results['in_output']:
            results['coords'].append(newcoord)
            results['occupancies'].append(periodictable.atomic_symbol(match.group(1)))
 
    def read_volume(results,match):
        results['volume'] = match.group(1)

    def read_hall(results,match):
        if results['in_input']:
            results['sghall']=match.group(1)
        elif results['in_output']:
            results['hall']=match.group(1)

    def read_id(results,match):
        results['id']=match.group(1)

    def coords_stop(results,match):
        results['in_coords'] = False
    def coords_start(results,match):
        if results['in_input']:
            results['in_input_coords'] = True
        elif results['in_output']:
            results['in_coords'] = True
    def cell_stop(results,match):
        results['in_cell'] = False
    def input_cell_stop(results,match):
        results['in_input_cell'] = False
    def cell_start(results,match):
        results['in_cell'] = True
    def input_cell_start(results,match):
        results['in_input_cell'] = True
    def output_start(results,match):
        results['in_output'] = True        
        results['in_input'] = False
    def read_version(results,match):
        results['version'] = match.group(1)
    def read_name(results,match):
        expr = httk.utils.parse_parexpr(match.group(1))
        # Grab the last, nested, parenthesed expression 
        p = ""
        for x in expr:
            if x[0] == 0:
                p=x[1]
        results['name'] = p
    def read_bib(results,match):
        results['bib'] += match.group(1)
    def bib_start(results,match):
        results['in_bib'] = True
    def bib_stop_input_start(results,match):
        results['in_bib'] = False
        results['in_input'] = True
    def read_source(results,match):        
        results['source'] = match.group(1).rstrip('.')
                
    out = httk.utils.micro_pyawk(ioa,[
            ['^ *INPUT CELL INFORMATION *$',None,bib_stop_input_start],
            ['^ *CIF2CELL ([0-9.]*)',None,read_version],
            ['^ *Output for (.*\)) *$',None,read_name],
            ['^ *Database reference code: *([0-9]+)',None,read_id],
            ['^ *All sites, (lattice coordinates): *$',lambda results,match: results['in_cell'],cell_stop],
            ['^ *Representative sites *: *$',lambda results,match: results['in_input_cell'],input_cell_stop],
            ['^ *$',lambda results,match: results['in_coords'],coords_stop],
            ['^ *([-0-9.]+) +([-0-9.]+) +([-0-9.]+) *$',lambda results,match: results['in_cell'] or results['in_input_cell'],read_cell],
            ['^ *([a-zA-Z]+) +([-0-9.]+) +([-0-9.]+) +([-0-9.]+) *$',lambda results,match: results['in_coords'] or results['in_input_coords'],read_coords],
            ['^ *([a-zA-Z/]+) +([-0-9.]+) +([-0-9.]+) +([-0-9.]+)( +([-0-9./]+)) *$',lambda results,match: results['in_coords'] or results['in_input_coords'],read_coords_occs],
#            ['^ *Hermann-Mauguin symbol *: *(.*)$',lambda results,match: results['in_output'],read_spacegroup],
            ['^ *Hall symbol *: *(.*)$',lambda results,match: results['in_output'] or results['in_input'],read_hall],
            ['^ *Unit cell volume *: *([-0-9.]+) +A\^3 *$',lambda results,match: results['in_output'],read_volume],
            ['^ *Bravais lattice vectors : *$',lambda results,match: results['in_output'],cell_start],
            ['^ *Lattice parameters: *$',lambda results,match: results['in_input'],input_cell_start],
            ['^ *Atom +a1 +a2 +a3',lambda results,match: results['in_output'] or results['in_input'],coords_start],
            ['^ *OUTPUT CELL INFORMATION *$',None,output_start],
            ['^([^\n]*)$',lambda results,match: results['in_bib'],read_bib],
            ['^ *BIBLIOGRAPHIC INFORMATION *$',None,bib_start],
            ['CIF file exported from +(.*) *$',None,read_source]
          
          ],debug=False,results=results)

    out['bib'] = out['bib'].strip()

    a,b,c = [float(x) for x in out['input_cell'][0]]
    alpha,beta,gamma = [float(x) for x in out['input_cell'][1]]

    cell = FracVector.create(out['cell'])
    coords = FracVector.create(out['coords'])
    sgcoords = FracVector.create(out['sgcoords'])

    hall_symbol = out['hall']
    sghall_symbol = out['sghall']
    tags = {}
    if 'source' in out:
        tags['source']=out['source']
    if 'id' in out:
        tags['source_id']=out['id']
    if 'bib' in out:
        refs=[out['bib']]
    else:
        refs = None
    if 'name' in out:
        tags['name']=filter(lambda x: x in string.printable, out['name'])

    if 'volume' in out:
        vol = FracVector.create(out['volume'])
    else:
        volstruct = httk.Structure.create(a=a,b=b,c=c,alpha=alpha,beta=beta,gamma=gamma, occupancies=out['sgoccupancies'], coords=sgcoords, hall_symbol=sghall_symbol, refs=refs)
        vol = volstruct.volume

    #struct = httk.Structure.create(cell,occupancies=out['occupancies'],coords=coords,volume=vol,tags=tags,hall_symbol=hall_symbol, refs=refs)
    #struct._sgstructure = httk.SgStructure.create(a=a,b=b,c=c,alpha=alpha,beta=beta,gamma=gamma, occupancies=out['sgoccupancies'], coords=sgcoords, hall_symbol=sghall_symbol)
    struct = httk.Structure.create(cell, volume=vol, occupancies=out['sgoccupancies'], coords=sgcoords, spacegroup=sghall_symbol, tags=tags, refs=refs, periodicity=0)
    #counts = [len(x) for x in out['occupancies']]
    p1structure = httk.Structure.create(cell,occupancies=out['occupancies'],coords=coords,volume=vol,tags=tags, refs=refs, periodicity=0)
    struct.set_p1structure(p1structure)

    return struct
    


