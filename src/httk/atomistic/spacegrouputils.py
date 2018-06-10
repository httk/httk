# -*- coding: utf-8 -*-
#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2015 Rickard Armiento
#    Some parts imported from cif2cell, (C) Torbjörn Björkman 
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
import pickle, re
from fractions import Fraction

from httk.core import citation, FracVector

# Load data extracted from cctbx
citation.add_src_citation("imported spacegroup data", "Computational Crystallography Toolbox, http://cctbx.sourceforge.net/")
f = open(__file__.rstrip('.pyc').rstrip('.py')+".pkl",'rb')
allspacegroupdata = pickle.load(f)
f.close()

spacegroupdata = allspacegroupdata['data']
itcnbr_index = allspacegroupdata['itc_nbr_index']
hm_index = allspacegroupdata['hm_index']
symops_hash_index = allspacegroupdata['symops_hash_index']
all_symops = allspacegroupdata['symops']

def symopshash(symops):
    data = [symopstuple(x) for x in symops]
    hashes = tuple(sorted([(hash(x[0]), hash(x[1])) for x in data]))
    return hash(hashes)


def val_to_tuple(val):
    frac = Fraction(val)
    if frac.denominator != 1:
        return (frac.numerator, frac.denominator)
    else:
        return frac.numerator


def symopstuple(symop, val_transform=val_to_tuple):
    symop = symop.replace(" ", "")
    transl = [0, 0, 0]
    transf = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    row = symop.split(",")

    for i in range(len(row)):

        parts = [x for x in re.split("([xyz+-])", row[i]) if x != '']
        if parts[0] not in ['+', '-']:
            parts.insert(0, '+')

        if parts.pop(0) == '-':
            sign = "-"
        else:
            sign = ""
        val = None
        var = None
        while len(parts) > 0:
            data = parts.pop(0)
            if data in ('+', '-'):
                if var is not None:
                    if val is None:
                        val = '1'
                    transf[i][var] = val_transform(sign + val)
                else:
                    if val is None:
                        val = '0'
                    if val == '1':  # why?!, who does this?
                        val = '0'
                    transl[i] = val_transform(val)
                val = None
                var = None
                sign = None
            if data == '+':
                sign = ""
            elif data == '-':
                sign = "-"
            elif data == 'x':
                var = 0
            elif data == 'y':
                var = 1
            elif data == 'z':
                var = 2
            else:
                val = data
                fval = Fraction(val)
                if fval > 1:
                    fval -= (fval.numerator // fval.denominator)
                    val = str(fval.numerator) + '/' + str(fval.denominator)
                if sign == '-':
                    if val == '3/4':
                        val = '1/4'
                    elif val == '1/4':
                        val = '3/4'
                    elif val == '1/2':
                        pass
                    elif val == '1/6':
                        val = '5/6'
                    elif val == '1':
                        val = '0'
                    else:
                        raise Exception("Spacegrouputil: symopstuple: misformed data:"+str(val))
                    sign = ''

        if var is not None:
            if val is None:
                val = '1'
            transf[i][var] = val_transform(sign + val)
        else:
            if val is None:
                val = '0'
            if val == '1':  # why?!, who does this?
                val = '0'
            transl[i] = val_transform(val)

    return tuple([tuple(x) for x in transf]), tuple(transl)


# Valid settings, from: http://www.mx.iucr.org/iucr-top/cif/cif_core/definitions/Cdata_symmetry_cell_setting.html
# These are really crystal systems...
crystal_system = [
    'triclinic',
    'monoclinic',
    'orthorhombic',
    'tetragonal',
    'rhombohedral',
    'trigonal',
    'hexagonal',
    'cubic'
]

# Valid origin, from: http://www.iucr.org/__data/iucr/cif/software/ciftools/ciftools/dict/cif_sym_1.0.dic
settings = [['b1', 'monoclinic unique axis b, cell choice 1, abc'],
            ['b2', 'monoclinic unique axis b, cell choice 2, abc'],
            ['b3', 'monoclinic unique axis b, cell choice 3, abc'],
            ['-b1', 'monoclinic unique axis b, cell choice 1, c-ba'],
            ['-b2', 'monoclinic unique axis b, cell choice 2, c-ba'],
            ['-b3', 'monoclinic unique axis b, cell choice 3, c-ba'],
            ['c1', 'monoclinic unique axis c, cell choice 1, abc'],
            ['c2', 'monoclinic unique axis c, cell choice 2, abc'],
            ['c3', 'monoclinic unique axis c, cell choice 3, abc'],
            ['-c1', 'monoclinic unique axis c, cell choice 1, ba-c'],
            ['-c2', 'monoclinic unique axis c, cell choice 2, ba-c'],
            ['-c3', 'monoclinic unique axis c, cell choice 3, ba-c'],
            ['a1', 'monoclinic unique axis a, cell choice 1, abc'],
            ['a2', 'monoclinic unique axis a, cell choice 2, abc'],
            ['a3', 'monoclinic unique axis a, cell choice 3, abc'],
            ['-a1', 'monoclinic unique axis a, cell choice 1, -acb'],
            ['-a2', 'monoclinic unique axis a, cell choice 2, -acb'],
            ['-a3', 'monoclinic unique axis a, cell choice 3, -acb'],
            ['abc', 'orthorhombic'],
            ['ba-c', 'orthorhombic'],
            ['cab', 'orthorhombic'],
            ['-cba', 'orthorhombic'],
            ['bca', 'orthorhombic'],
            ['a-cb', 'orthorhombic'],
            ['1abc', 'orthorhombic origin choice 1'],
            ['1ba-c', 'orthorhombic origin choice 1'],
            ['1cab', 'orthorhombic origin choice 1'],
            ['1-cba', 'orthorhombic origin choice 1'],
            ['1bca', 'orthorhombic origin choice 1'],
            ['1a-cb', 'orthorhombic origin choice 1'],
            ['2abc', 'orthorhombic origin choice 2'],
            ['2ba-c', 'orthorhombic origin choice 2'],
            ['2cab', 'orthorhombic origin choice 2'],
            ['2-cba', 'orthorhombic origin choice 2'],
            ['2bca', 'orthorhombic origin choice 2'],
            ['2a-cb', 'orthorhombic origin choice 2'],
            ['1', 'tetragonal or cubic origin choice 1'],
            ['2', 'tetragonal or cubic origin choice 2'],
            ['h', 'trigonal using hexagonal axes'],
            ['r', 'trigonal using rhombohedral axes']]


def symopsmatrix(symop):
    transf, transl = symopstuple(symop, val_transform=lambda x: x)
    return FracVector.create(transf), FracVector.create(transl)


def get_hall(hall):
    if hall in spacegroupdata:
        return hall
    return None


def get_symops(hall):
    if hall in spacegroupdata:
        return [symopsmatrix(x) for x in spacegroupdata[hall]['symops_mtrx']]
    return None


def get_symopshash(hall):
    if hall in spacegroupdata:
        return spacegroupdata[hall]['symops_hash']
    return None


def get_symops_strs(hall):
    if hall in spacegroupdata:
        return spacegroupdata[hall]['symops_mtrx']
    return None


def get_nonstandard_hall(nonstd_hall):
    #TODO: Get back list of nonstandard hall symbols in new structure
    if nonstd_hall in spacegroupdata:
        return nonstd_hall
    #for hall in spacegroupdata:
    #    if nonstd_hall in spacegroupdata[hall][3]:
    #        return hall
    return None


def get_itcnbr_setting(itcnbr, setting):
    try:
        itcnbr = int(itcnbr)
    except Exception:
        return None
    for hall in spacegroupdata:
        if itcnbr == spacegroupdata[hall]['itc_nbr'] and setting == spacegroupdata[hall]['setting']:
            return hall
    return None


def get_hm_setting(hm, setting):
    halls = hm_index[hm]
    for hall in halls:
        if spacegroupdata[hall]['setting'] == setting:
            return hall
    return None


def filter_itcnbr_setting(itcnbr, setting=None, halls=None):
    try:
        itcnbr = str(int(itcnbr))
    except Exception:
        return []
    if halls is None:
        halls = spacegroupdata.keys()
    if setting is not None:
        result = get_itcnbr_setting(itcnbr, setting)
        if result in halls:
            return [result]
        else:
            return []
    if itcnbr in itcnbr_index:
        possible_halls = itcnbr_index[itcnbr]
        return list(set(halls) & set(possible_halls))

    return []


def filter_hm(hm, setting=None, halls=None):
    # Note, this one works a bit differently than the other filters. If we do not recognize the hm symbol,
    # the filter does no filtering. This is since there are many non-standard hm symbols.
    if halls is None:
        halls = spacegroupdata.keys()
    if setting is not None:
        try:
            result = get_hm_setting(hm.strip(), setting.strip())
            if result in halls:
                return [result]
            else:
                return halls
        except KeyError:
            pass
    if hm in hm_index:
        possible_halls = hm_index[hm] 
        return list(set(halls) & set(possible_halls))
    return halls


def filter_sf(sf, halls=None):
    if halls is None:
        halls = spacegroupdata.keys()
    outhalls = []
    for hall in halls:
        if sf == spacegroupdata[hall]['sf_symb']:
            outhalls.append(hall)
    return outhalls


def filter_symops(symops, halls=None):
    global symopsindex

    if halls is None:
        halls = spacegroupdata.keys()

    symops_hash = symopshash(symops)

    if symops_hash in symops_hash_index:
        symop_hall = symops_hash_index[symops_hash] 
        if symop_hall in halls:
            return [symop_hall]

    #print "FAILED?", halls, symops_hash, spacegroupdata[halls[0]]['symops_hash']
    #print "************"
    #print sorted([(x,symopstuple(x)) for x in symops])
    #print "************"
    #print sorted([(x,symopstuple(x)) for x in spacegroupdata[halls[0]]['symops_mtrx']])
    #print "************"

    return []


def spacegroup_filter(parse):
    parse = str(parse).strip().replace("_", " ")

    # 1. Is this a proper hall symbol?
    hallparse = parse
    if hallparse[0] == '-':
        hallparse = "-"+hallparse[1].upper() + (hallparse[2:].lower())
    else:
        hallparse = hallparse[0].upper() + (hallparse[1:].lower())
    hall = get_hall(hallparse)
    if hall is not None:
        return [hall]

    # 2. Is this a non-standard hall symbol?
    hall = get_nonstandard_hall(hallparse)
    if hall is not None:
        return [hall]

    p = parse.partition(':')
    data = p[0]
    if p[2].strip() == '':
        setting = None
    else:
        setting = p[2].tolower()

    if setting is None:
        for s in settings:
            if s[1] in data:
                setting = s[0]
                data = data.replace(s[1], "").strip()

    # 3. ITC number (and setting)
    halls = filter_itcnbr_setting(data, setting)
    if len(halls) > 0:
        return halls

    # 4. HM symbol (and setting)
    halls = filter_hm(data, setting)
    if len(halls) > 0:
        return halls

    # 5. sf symbol
    halls = filter_sf(data)
    if len(halls) > 0:
        return halls

    return []


def spacegroup_filter_specific(hall=None, hm=None, itcnbr=None, setting=None, symops=None, halls=None):
    if halls is None:
        halls = spacegroupdata.keys()

    # 1. Is this a proper hall symbol?
    if hall is not None:
        hallparse = str(hall).strip().replace("_", " ")
        if hallparse[0] == '-':
            hallparse = "-"+hallparse[1].upper() + (hallparse[2:].lower())
        else:
            hallparse = hallparse[0].upper() + (hallparse[1:].lower())
            
        # Sometimes a commment, e.g., about the setting follows the hall symbol
        # But some hall symbols should have paranthesis...
        #if '(' in hallparse:
        #    hallparse, _dummy1, _dummy2 = hallparse.partition('(')
        #    hallparse = hallparse.strip()

        hall = get_hall(hallparse)
        if hall in halls or halls is None:
            halls = [hall]

        # 2. Is this a non-standard hall symbol?
        hall = get_nonstandard_hall(hallparse)
        if hall in halls or halls is None:
            halls = [hall]

    if itcnbr is not None:
        itcnbr = str(itcnbr)
        if setting is None:
            p = itcnbr.partition(':')
            data = p[0]
            if p[2].strip() == '':
                setting = None
            else:
                setting = p[2].tolower()

        if setting is None:
            for s in settings:
                if s[1] in data:
                    setting = s[0]
                    data = data.replace(s[1], "").strip()

        # 3. ITC number (and setting)
        halls = filter_itcnbr_setting(data, setting, halls=halls)

    if hm is not None:
        p = hm.partition(':')
        data = p[0]
        if p[2].strip() == '':
            setting = None
        else:
            setting = p[2].lower()

        # 4. HM symbol (and setting)
        halls = filter_hm(data, setting, halls=halls)

    if symops is not None:
        halls = filter_symops(symops, halls)

    return halls


def spacegroup_parse(parse):
    result = spacegroup_filter(parse)
    if len(result) == 1:
        return result[0]
    elif len(result) == 0:
        raise Exception("No matching spacegroup found from given information:"+str(parse))
    raise Exception("Spacegroup not uniquely defined from given information:"+str(parse)+" found "+str(len(result))+" candidates:"+str(result))


def spacegroup_get_schoenflies(parse):
    return spacegroupdata[spacegroup_parse(parse)]['sf_symb']


def spacegroup_get_hm(parse):
    return spacegroupdata[spacegroup_parse(parse)][2]['hm_symb']


def spacegroup_get_hall(parse):
    return spacegroup_parse(parse)


def spacegroup_get_number(parse):
    val = spacegroupdata[spacegroup_parse(parse)]['itc_nbr']
    if val is not None:
        return int(val)
    else:
        return None


def spacegroup_get_number_and_setting(parse):
    hall = spacegroup_parse(parse)
    val = spacegroupdata[spacegroup_parse(parse)]['itc_nbr']
    if val is not None:
        val = int(val)
    return val, spacegroupdata[hall]['setting']


citation.add_src_citation("imported code from cif2cell", "Torbjörn Björkman")
# Imported from cif2cell by Torbjörn Björkman, spacegroupdata.py


def crystal_system_from_spacegroupnbr(spacegroupnr):
    # Determine crystal system
    if 0 < spacegroupnr <= 2:
        return "triclinic"
    elif 2 < spacegroupnr <= 15:
        return "monoclinic"
    elif 15 < spacegroupnr <= 74:
        return "orthorhombic"
    elif 74 < spacegroupnr <= 142:
        return "tetragonal"
    elif 142 < spacegroupnr <= 167:
        return "trigonal"
    elif 167 < spacegroupnr <= 194:
        return "hexagonal"
    elif 194 < spacegroupnr <= 230:
        return "cubic"
    else:
        return "unknown"

lattice_types = {'P': 'primitive', 'I': 'body-centered', 
                 'F': 'face-centered', 'A': 'base-centered',
                 'B': 'base-centered', 'C': 'base-centered',
                 'R': 'rhombohedral'}


def lattice_symbol_from_hall(hall):
    return hall.lstrip("-")[0][0]


def lattice_system_from_hall(hall):
    crystal_system = crystal_system_from_hall(hall)
    if crystal_system != 'triclinic':
        return crystal_system
    lattice_symbol = lattice_symbol_from_hall(hall)
    if lattice_symbol == 'R':
        return 'rhombohedral'
    else:
        return 'hexagonal'
    

def lattice_type_from_hall(hall):
    return lattice_types[lattice_symbol_from_hall(hall)]


def crystal_system_from_hall(hall_symb):
    numb = spacegroup_get_number(hall_symb)
    return crystal_system_from_spacegroupnbr(numb)


def check_symop(coordgroups, symopv):
    for coordgroup in coordgroups:
        for coord in coordgroup:
            transformed_coord = (symopv[0]*coord + symopv[1]).normalize()
            if transformed_coord not in coordgroup:
                return False
    return True


def wyckoff_symbol_matcher(wyckoffs, coord):
    for spec, letter in wyckoffs:
        parts = spec.split(',')
        spec = re.sub('([0-9]+)/([0-9]+)', r'Fraction(\1,\2)', spec)
        x, y, z = (0, 0, 0)
        if parts[0] == 'x':
            x = coord[0]
        if parts[1] == 'x':
            x = coord[1]
        if parts[1] == 'x':
            x = coord[2]
        if parts[1] == 'y':
            y = coord[1]
        if parts[1] == 'y':
            y = coord[2]
        if parts[2] == 'z':
            z = coord[2]
        check_coord = eval('['+spec+']', {'Fraction': Fraction}, {'x': x, 'y': y, 'z': z})
        if coord == check_coord:
            return letter
    return wyckoffs[-1][1]


def reduce_by_symops(coordgroups, symopvs, hall_symbol):
    letters = spacegroupdata[hall_symbol]['wyckoff_letter']
    mults = spacegroupdata[hall_symbol]['wyckoff_mult']
    wyckoffs = []
    for letter, spec in sorted(zip(letters, spacegroupdata[hall_symbol]['wyckoff_rep_spec_pos_op'])):
        wyckoffs += [(spec, letter)]
    
    reduced_coordgroups = []
    wyckoff_symbols = []
    for coordgroup in coordgroups:
        keep_coords = []
        for coord in coordgroup:
            for symopv in symopvs:
                transformed_coord = (symopv[0]*coord + symopv[1]).normalize()
                if transformed_coord in keep_coords:
                    break
            else:
                keep_coords += [coord]
                wyckoff_symbols += [wyckoff_symbol_matcher(wyckoffs, coord)]
        reduced_coordgroups += [keep_coords]
    
    #wyckoff_symbols = ['a']*sum([len(x) for x in coordgroups])
    #multiplicities = [1]*sum([len(x) for x in coordgroups])

    multiplicities = [mults[letters.index(x)] for x in wyckoff_symbols]
    
    return reduced_coordgroups, wyckoff_symbols, multiplicities


def trivial_symmetry_reduce(coordgroups):
    """
    Looks for 'trivial' ways to reduce the coordinates in the given coordgroups by a standard set of symmetry operations.
    This is not a symmetry finder (and it is not intended to be), but for a standard primitive cell taken from a standard
    conventional cell, it reverses the primitive unit cell coordgroups into the symmetry reduced coordgroups.
    """    
    # TODO: Actually implement, instead of this placeholder that just gives up and returns P 1

    symops = []
    symopvs = []
    for symop in all_symops:
        symopv = FracVector.create(symop)
        if check_symop(coordgroups, symopv):
            symops += [all_symops[symop]]
            symopvs += [symopv]

    shash = symopshash(symops)
    if shash in symops_hash_index:
        hall_symbol = symops_hash_index[shash]
        rc_reduced_coordgroups, wyckoff_symbols, multiplicities = reduce_by_symops(coordgroups, symopvs, hall_symbol)
        return rc_reduced_coordgroups, hall_symbol, wyckoff_symbols, multiplicities
    
    rc_reduced_coordgroups = coordgroups
    hall_symbol = 'P 1'
    wyckoff_symbols = ['a']*sum([len(x) for x in coordgroups])
    multiplicities = [1]*sum([len(x) for x in coordgroups])
    
    return rc_reduced_coordgroups, hall_symbol, wyckoff_symbols, multiplicities


def main():
    print allspacegroupdata['symops']

    #result = spacegroup_filter('134')
    #print result

    pass


if __name__ == "__main__":
    main()
