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

import httk  
from httk.core.basic import is_sequence
from httk.atomistic.data import periodictable, spacegroups
from httk.atomistic import *


def reduced_coordgroups_to_input(coordgroups, cell, comment="FINDSYM input", accuracy=0.001):
    inputstr = comment+"\n"
    # 1
    inputstr += str(accuracy)+"\n"
    # 2
    inputstr += "2\n"  # 3
    inputstr += "%.8f %.8f %.8f %.8f %.8f %.8f\n" % (cell.a, cell.b, cell.c, cell.alpha, cell.beta, cell.gamma)  # 4
    inputstr += "2\n"  # 5
    inputstr += spacegroup+"\n"  # 6
    uc_nbr_atoms = sum([len(x) for x in coordgroups])
    inputstr += str(uc_nbr_atoms)+"\n"
    inputstr += " ".join([str(group+1) for group in range(0, len(coordgroups)) for i in range(0, len(coordgroups[group]))]) + "\n"
    for rows in coordgroups:
        for row in rows:
            inputstr += "%.8f %.8f %.8f\n" % (row[0], row[1], row[2])
    return inputstr


def struct_to_input(struct):
    inputstr = "FINDSYM input for "+struct.formula+"\n"
    # 1
    #inputstr += "0.001\n"; #2
    inputstr += "0.001\n"
    # 2
    inputstr += "2\n"  # 3
    inputstr += "%.8f %.8f %.8f %.8f %.8f %.8f\n" % (struct.uc_a, struct.uc_b, struct.uc_c, struct.uc_alpha, struct.uc_beta, struct.uc_gamma)  # 4
    inputstr += "2\n"  # 5
    inputstr += "P\n"  # 6
    inputstr += str(struct.uc_nbr_atoms)+"\n"
    inputstr += " ".join([str(group+1) for group in range(0, len(struct.uc_reduced_coordgroups)) for i in range(0, len(struct.uc_reduced_coordgroups[group]))]) + "\n"
    for row in struct.uc_reduced_coords:
        inputstr += "%.8f %.8f %.8f\n" % (row[0], row[1], row[2])
    #print "INPUT",struct.formula,len(struct.uc_reduced_coords)
    return inputstr


def out_to_cif(ioa, assignments, getwyckoff=False):

    def cif_start(results, match):
        results['did_start'] = True
        results['on'] = True

    def cif_add(results, match):
        if results['out']:
            results['out'] = False
        else:
            add_groupdata(results)
            results['cif'] += match.group(0)+"\n"
            #results['data']+=match.group(0)+"\n"

    def add_groupdata(results):

        sorteddata = sorted(results['groupdata'], key=lambda data: (data[4], data[5], data[6]))                    
        for data in sorteddata:
            #print "HUH",data[1],data[4],data[5],data[6]
            occustr = data[1]
            if not occustr in results['occucounts']:
                results['occucounts'][occustr] = 0
            results['occucounts'][occustr] += 1
            i = results['occucounts'][occustr]                        
            data[0] = occustr+str(i)
            results['cif'] += " ".join(data)+"\n"
            results['data'] += " ".join(data)+"\n"
        results['groupdata'] = []                   

    def print_hm_and_hall(results):
        grpnbr = results['grpnbr']
        setting = results['setting']
        hmsymb = results['hmfull']
        hallsymb = spacegroups.spacegroup_get_hall(str(grpnbr)+":"+setting)
        results['cif'] += "_symmetry_space_group_name_H-M \""+hmsymb+"\"\n"
        results['cif'] += "_symmetry_space_group_name_Hall '"+hallsymb+"'\n"
        results['data'] += grpnbr+"\nHall symbol:"+hallsymb+"\n"
        results['data'] += "Columns as follows: label element symmetry_multiplicity Wykoff_label fract_x fract_y fact_z occupancy\n"
        #results['cif']+="_[local]_omdb_cod_original_Hall '"+struct.hall_symbol+"'\n"
        #if(struct.hall_symbol != hallsymb):
        #    print >> sys.stderr, "== Hall symbol change!",struct.hall_symbol,hallsymb
        #    with open("symmetry-differences.txt", "a") as myfile:
        #        myfile.write(filename+" :"+struct.hall_symbol+"|"+hallsymb+"\n")
        #else:
        #    print >> sys.stderr, "== Hall symbol the same",struct.hall_symbol,hallsymb

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
        results['out'] = True
        idx = ord(match.group(2)) - 65 
        if results['group'] != idx:
            add_groupdata(results)
        if match.group(4) == 'alpha':
            results['wyckoff'] += ['&']
        else:
            results['wyckoff'] += [match.group(4)]
        results['group'] = idx
        occus = assignments[idx]
        if is_sequence(occus):
            for i in range(len(occus)):
                occu = occus[i]
                try:
                    ratio = str(occu.ratio.to_float())
                except AttributeError:
                    ratio = str(occu.ratio)
                results['groupdata'].append([occu.symbol+str(i), occu.symbol, match.group(3), match.group(4), match.group(5), match.group(6), match.group(7), ratio])
        else:
            ratio = '1'
            results['groupdata'].append([assignments[idx], assignments[idx], match.group(3), match.group(4), match.group(5), match.group(6), match.group(7), ratio])

    def cif_broken(results, match):
        raise Exception("Findsym program error: this program has bombed.")

    results = {'on': False, 'data': '', 'cif': '', 'out': False, 'group': -1, 'groupdata': [], 'occucounts': {}, 'did_start': False, 'wyckoff': []}
    httk.basic.micro_pyawk(ioa, [
        ['This program has bombed', None, cif_broken],
        ['^# CIF file$', None, cif_start],
        ['^_symmetry_Int_Tables_number +(.*)$', None, groupnbr],
        ['^_symmetry_space_group_name_H-M +"(([^()]+) \(origin choice ([0-9]+)\))" *$', None, hm_symbol_origin],
        ['^_symmetry_space_group_name_H-M +"(([^()]+) \((hexagonal axes)\))" *$', None, hm_symbol_origin],
        ['^_symmetry_space_group_name_H-M +"([^()]+)" *$', None, hm_symbol_no_origin],
        ['^ *([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) *$', None, coords],
        ['.*', lambda results, match: results['on'], cif_add],
    ], debug=False, results=results)
    add_groupdata(results)
    if results['did_start'] == False:
        raise Exception("Findsym program error: no cif in output.")
    if getwyckoff:
        return results['cif'], results['wyckoff']
    else:
        return results['cif']
