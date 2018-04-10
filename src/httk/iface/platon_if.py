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

"""
This module is a mess and in need of heavy cleanup.
"""

import re, sys

from httk.core import FracVector
from httk.atomistic import Structure, Spacegroup
from httk.atomistic.data import periodictable, spacegroups
import httk  

import os, errno


def platon_lis_to_struct_broken(ioa):
    """
    Example input format::
            
                                                               ============
        ====================================================== Crystal Data ================================================================
                                                               ============
                                Input Cell  (Lattice Type: P)   -   Temp =   0K             Reduced Cell     (Acta Cryst.(1976),A32,297-298)
        ---------------------------------------------------------------------------------   ------------------------------------------------
        a =       3.47100  Angstrom                alpha =            90 Degree             a  =    3.471     alpha  =   90.00  V  =    79.6
        b =       3.47100                           beta =            90                    b  =    3.471     beta   =   90.00              
        c =       6.60300                          gamma =            90                    c  =    6.603     gamma  =   90.00              
        
        ...
        
        ------------------------------------------------------------------------------------------------------------------------------------
        Flags Label         Fractional Coordinates (x,y,z)          Orthogonal Coordinates (XO,YO,ZO)   Site SSN*SSOF =    S.O.F   Move Type
        ------------------------------------------------------------------------------------------------------------------------------------
        -     Ag(1)              1/4            1/4        0.61200      0.8677      0.8677      4.0410   4mm  8   1/8          1    -    Met
        -     Zr(2)              1/4            1/4        0.13700      0.8677      0.8677      0.9046   4mm  8   1/8          1    -    Met
        -     Ag(1)a            -1/4           -1/4       -0.61200     -0.8677     -0.8677     -4.0410   4mm  8   1/8          1   5.455 Met
        -     Zr(2)a            -1/4           -1/4       -0.13700     -0.8677     -0.8677     -0.9046   4mm  8   1/8          1   5.455 Met
        -     Ag(1)b            -1/4           -1/4        0.38800     -0.8678     -0.8678      2.5620   4mm  8   1/8          1   5.456 Met
        -     Zr(2)b            -1/4           -1/4        0.86300     -0.8678     -0.8678      5.6984   4mm  8   1/8          1   5.456 Met
        -     Ag(1)c            -1/4            3/4       -0.61200     -0.8677      2.6033     -4.0410   4mm  8   1/8          1   5.465 Met
        -     Zr(2)c            -1/4            3/4       -0.13700     -0.8678      2.6033     -0.9046   4mm  8   1/8          1   5.465 Met
        -     Ag(1)d            -1/4            3/4        0.38800     -0.8678      2.6033      2.5620   4mm  8   1/8          1   5.466 Met
        -     Zr(2)d            -1/4            3/4        0.86300     -0.8678      2.6032      5.6984   4mm  8   1/8          1   5.466 Met
        -     Ag(1)e             3/4           -1/4       -0.61200      2.6033     -0.8677     -4.0410   4mm  8   1/8          1   5.555 Met
        -     Zr(2)e             3/4           -1/4       -0.13700      2.6033     -0.8677     -0.9046   4mm  8   1/8          1   5.555 Met
        -     Ag(1)f             3/4           -1/4        0.38800      2.6033     -0.8678      2.5620   4mm  8   1/8          1   5.556 Met
        -     Zr(2)f             3/4           -1/4        0.86300      2.6032     -0.8678      5.6984   4mm  8   1/8          1   5.556 Met
        -     Ag(1)g             3/4            3/4       -0.61200      2.6033      2.6033     -4.0410   4mm  8   1/8          1   5.565 Met
        -     Zr(2)g             3/4            3/4       -0.13700      2.6033      2.6033     -0.9046   4mm  8   1/8          1   5.565 Met
        -     Ag(1)h             3/4            3/4        0.38800      2.6033      2.6033      2.5620   4mm  8   1/8          1   5.566 Met
        -     Zr(2)h             3/4            3/4        0.86300      2.6032      2.6032      5.6984   4mm  8   1/8          1   5.566 Met
        ====================================================================================================================================
    """        
    ioa = httk.IoAdapterFileReader(ioa)    

    seen_coords = set()

    def read_spacegroup(results, match):
        results['spacegroup'] = match.group(1).strip()

    def read_a_alpha(results, match):
        results['a'] = float(match.group(1).replace('(', '').replace(')', ''))
        results['alpha'] = float(match.group(3).replace('(', '').replace(')', ''))

    def read_b_beta(results, match):
        results['b'] = float(match.group(1).replace('(', '').replace(')', ''))
        results['beta'] = float(match.group(3).replace('(', '').replace(')', ''))

    def read_c_gamma(results, match):
        results['c'] = float(match.group(1).replace('(', '').replace(')', ''))
        results['gamma'] = float(match.group(3).replace('(', '').replace(')', ''))

    def read_coords(results, match):
        sys.stdout.write("\n>>|")
        #for i in range(1,14):
        #    sys.stdout.write(match.group(i)+"|")
        species = periodictable.atomic_number(match.group(1))
        ratio = FracVector.create(re.sub(r'\([^)]*\)', '', match.group(11)))
        
        a1 = re.sub(r'\([^)]*\)', '', match.group(2))
        b1 = re.sub(r'\([^)]*\)', '', match.group(3))
        c1 = re.sub(r'\([^)]*\)', '', match.group(4))

        a = match.group(2).replace('(', '').replace(')', '')
        b = match.group(3).replace('(', '').replace(')', '')
        c = match.group(4).replace('(', '').replace(')', '')
        coord = FracVector.create([a1, b1, c1]).normalize()
        sys.stdout.write(str(species)+" "+str(coord.to_floats()))
        limcoord = FracVector.create([a1, b1, c1]).normalize()
        coordtuple = ((species, ratio.to_tuple()), limcoord.to_tuple())
        if coordtuple in seen_coords:
            return
        results['occupancies'].append((species, float(ratio)))
        results['coords'].append(coord)
        seen_coords.add(coordtuple)

    def in_table(results, match):
        results['in_table'] = True

    def end_table(results, match):
        results['in_table'] = False

    def section(results, match):
        results['section'] = match.group(1)

    results = {}
    results['spacegroup'] = None
    results['section'] = None
    results['in_table'] = None
    results['occupancies'] = []
    results['coords'] = []
    out = httk.basic.micro_pyawk(ioa, [
        ['^ *Space Group +(([^ ]+ )+) +', lambda results, match: results['section'] == 'Space Group Symmetry' and results['spacegroup'] is None, read_spacegroup],
        ['^ *a = +([0-9.()-]+) +(Angstrom)? +alpha = +([0-9.()-]+)', lambda results, match: results['section'] == 'Crystal Data', read_a_alpha],
        ['^ *b = +([0-9.()-]+) +(Angstrom)? +beta = +([0-9.()-]+)', lambda results, match: results['section'] == 'Crystal Data', read_b_beta],
        ['^ *c = +([0-9.()-]+) +(Angstrom)? +gamma = +([0-9.()-]+)', lambda results, match: results['section'] == 'Crystal Data', read_c_gamma],
        ['^ Asymmetric Residue Unit \(= ARU\) Code List *$', lambda results, match: results['in_table'], end_table],
        #['^ *=+ *$',lambda results,match: results['in_table']==True,end_table],
        ['^[^ ]* +[^A-Z]*([a-zA-Z]+)[^ ]* +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([^ ]*) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([^ \n]+) *$', lambda results, match: results['in_table'], read_coords],
        ['^ *Flags Label +Fractional Coordinates \(x,y,z\) +Orthogonal Coordinates \(XO,YO,ZO\) +',
         lambda results, match: results['in_table'] is None and results['section'] == 'Space Group Symmetry', in_table],
        ['^ *=+ ([A-Za-z ]+) =+ *$', None, section],
    ], results=results, debug=False)

    # If we only have =1 occupancy everywhere, drop the occupancy ratio
    simple_occs = []
    for occupancy in out['occupancies']:
        if occupancy[1] > (1-1e-6):
            occupancies = out['occupancies']
            break
        simple_occs.append(occupancy[0])
    else:
        occupancies = simple_occs

    #print "OUT",out['occupancies']
    #exit(0)

    struct = Structure.create(a=out['a'], b=out['b'], c=out['c'], alpha=out['alpha'], beta=out['beta'],
                              gamma=out['gamma'], occupancies=occupancies, coords=out['coords'], tags={'platon_sg': out['spacegroup']}).round()
    return struct


def platon_lis_to_struct_broken2(ioa):
    """
    Example input::

                                                               ============
        ====================================================== Crystal Data ================================================================
                                                               ============
                                Input Cell  (Lattice Type: P)   -   Temp =   0K             Reduced Cell     (Acta Cryst.(1976),A32,297-298)
        ---------------------------------------------------------------------------------   ------------------------------------------------
        a =       3.47100  Angstrom                alpha =            90 Degree             a  =    3.471     alpha  =   90.00  V  =    79.6
        b =       3.47100                           beta =            90                    b  =    3.471     beta   =   90.00              
        c =       6.60300                          gamma =            90                    c  =    6.603     gamma  =   90.00              
        
        ...
        
        ====================================================================================================================================
        10.0 Angstrom Coordination Sphere Around Atom I = Ag(1)  [ARU = 1555.01]             1/4      1/4  0.61200    0.8677  0.8677  4.0410
        ------------------------------------------------------------------------------------------------------------------------------------
         Nr     d(I,J) To  Atom J  Symm_Oper. on Atom J    ARU(J)  Type     Phi     Mu         X        Y        Z        XO      YO      ZO
        ------------------------------------------------------------------------------------------------------------------------------------
         1      2.9615 --  Zr(4)  [                    =         ] Intra-135.00  34.03      -1/4     -1/4  0.86300   -0.8678 -0.8678  5.6984
         2      2.9615 --  Zr(4)n [1+x,1+y,z           =  1665.01] Intra  45.00  34.03       3/4      3/4  0.86300    2.6032  2.6032  5.6984
         3      2.9615 --  Zr(4)j [x,1+y,z             =  1565.01] Intra 135.00  34.03      -1/4      3/4  0.86300   -0.8678  2.6032  5.6984
         4      2.9615 --  Zr(4)l [1+x,y,z             =  1655.01] Intra -45.00  34.03       3/4     -1/4  0.86300    2.6032 -0.8678  5.6984
         5      3.1364 --  Zr(3)  [                    =         ] Intra   0.00 -90.00       1/4      1/4  0.13700    0.8677  0.8677  0.9046
    """        
    ioa = httk.IoAdapterFileReader(ioa)    

    seen_coords = set()

    def read_spacegroup(results, match):
        results['spacegroup'] = match.group(1).strip()

    def read_a_alpha(results, match):
        results['a'] = float(match.group(1).replace('(', '').replace(')', ''))
        results['alpha'] = float(match.group(3).replace('(', '').replace(')', ''))

    def read_b_beta(results, match):
        results['b'] = float(match.group(1).replace('(', '').replace(')', ''))
        results['beta'] = float(match.group(3).replace('(', '').replace(')', ''))

    def read_c_gamma(results, match):
        results['c'] = float(match.group(1).replace('(', '').replace(')', ''))
        results['gamma'] = float(match.group(3).replace('(', '').replace(')', ''))

    def read_coords(results, match):
        sys.stdout.write("\n>>|")
        #for i in range(1,14):
        #    sys.stdout.write(match.group(i)+"|")
        species = periodictable.atomic_number(match.group(1))
        ratio = FracVector.create(re.sub(r'\([^)]*\)', '', match.group(11)))
        
        a1 = re.sub(r'\([^)]*\)', '', match.group(2))
        b1 = re.sub(r'\([^)]*\)', '', match.group(3))
        c1 = re.sub(r'\([^)]*\)', '', match.group(4))

        a = match.group(2).replace('(', '').replace(')', '')
        b = match.group(3).replace('(', '').replace(')', '')
        c = match.group(4).replace('(', '').replace(')', '')
        coord = FracVector.create([a1, b1, c1]).normalize()
        sys.stdout.write(str(species)+" "+str(coord.to_floats()))
        limcoord = FracVector.create([a1, b1, c1]).normalize()
        coordtuple = ((species, ratio.to_tuple()), limcoord.to_tuple())
        if coordtuple in seen_coords:
            return
        results['occupancies'].append((species, float(ratio)))
        results['coords'].append(coord)
        seen_coords.add(coordtuple)

    def in_table(results, match):
        results['in_table'] = True

    def end_table(results, match):
        results['in_table'] = False

    def section(results, match):
        results['section'] = match.group(1)

    results = {}
    results['spacegroup'] = None
    results['section'] = None
    results['in_table'] = None
    results['occupancies'] = []
    results['coords'] = []
    out = httk.basic.micro_pyawk(ioa, [
        ['^ *Space Group +(([^ ]+ )+) +', lambda results, match: results['section'] == 'Space Group Symmetry' and results['spacegroup'] is None, read_spacegroup],
        ['^ *a = +([0-9.()-]+) +(Angstrom)? +alpha = +([0-9.()-]+)', lambda results, match: results['section'] == 'Crystal Data', read_a_alpha],
        ['^ *b = +([0-9.()-]+) +(Angstrom)? +beta = +([0-9.()-]+)', lambda results, match: results['section'] == 'Crystal Data', read_b_beta],
        ['^ *c = +([0-9.()-]+) +(Angstrom)? +gamma = +([0-9.()-]+)', lambda results, match: results['section'] == 'Crystal Data', read_c_gamma],
        ['^ Asymmetric Residue Unit \(= ARU\) Code List *$', lambda results, match: results['in_table'], end_table],
        #['^ *=+ *$',lambda results,match: results['in_table']==True,end_table],
        ['^[^ ]* +[^ ]* +[^ ]* +[^A-Z]*([a-zA-Z]+)[^ ]* +.* +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) *$', lambda results, match: results['in_table'], read_coords],
        ['^ *Angstrom Coordination Sphere Around Atom +',
         lambda results, match: results['in_table'] is None and results['section'] == 'Space Group Symmetry', in_table],
        ['^ *=+ ([A-Za-z ]+) =+ *$', None, section],
    ], results=results, debug=False)

    # If we only have =1 occupancy everywhere, drop the occupancy ratio
    simple_occs = []
    for occupancy in out['occupancies']:
        if occupancy[1] > (1-1e-6):
            occupancies = out['occupancies']
            break
        simple_occs.append(occupancy[0])
    else:
        occupancies = simple_occs

    #print "OUT",out['occupancies']
    #exit(0)

    struct = Structure.create(a=out['a'], b=out['b'], c=out['c'], alpha=out['alpha'], beta=out['beta'],
                              gamma=out['gamma'], occupancies=occupancies, coords=out['coords'], tags={'platon_sg': out['spacegroup']}).round()

    return struct


def platon_styin_to_sgstruct(ioa):
    """
    Example input:
    
        F -4 3 M        id=[0] dblock_code=[44325-ICSD] formula=
        5.5000    5.5000    5.5000   90.0000   90.0000   90.0000
        N
        Sb1       0.25000   0.25000   0.25000
        Al1       0.00000   0.00000   0.00000
        END
        END
    """        
    ioa = httk.IoAdapterFileReader(ioa)    

#     print ioa.file.read()
#     exit()
#     
#     fi = iter(ioa)
# 
#     spg_comment = next(fi).strip()
#     spgsymbol = spg_comment[:15]
#     comment = spg_comment[16:]
#     a,b,c,alpha,beta,gamma = [float(x) for x in next(fi).strip().split()]
# 
#     coords = []
#     occupancies = []
#     for line in fi:
#         strcoord = line.strip().split()
#         if strcoord[0] == 'END':
#             break
#         coord = map(lambda x: float(x.strip()),strcoord[1:4])
#         coords.append(coord)
#         occupation = strcoord[0]
#         occupation = re.sub('[0-9]*#*$', '', occupation)
#         occupancies.append(occupation)        

    def read_spacegroup(results, match):
        results['spacegroup'] = match.group(0).strip()

    def read_cell(results, match):
        results['a'] = float(match.group(1))
        results['b'] = float(match.group(2))
        results['c'] = float(match.group(3))
        results['alpha'] = float(match.group(4))
        results['beta'] = float(match.group(5))
        results['gamma'] = float(match.group(6))
        results['has_cell'] = True

    def read_coords(results, match):
        results['occupancies'].append(periodictable.atomic_number(match.group(1)))
        results['coords'].append([float(match.group(2)), float(match.group(3)), float(match.group(4))])

    def read_end(results, match):
        results['end'] = True

    results = {}
    results['spacegroup'] = None
    results['has_cell'] = False
    results['occupancies'] = []
    results['coords'] = []
    results['end'] = False
    out = httk.basic.micro_pyawk(ioa, [
        ['^ *([a-zA-Z]+)[^ ]* +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) *$', lambda results, match: results['has_cell'] and not results['end'], read_coords],
        ['^ *([0-9.-]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) *$', lambda results, match: results['spacegroup'] is not None and not results['end'], read_cell],
        ['^ *([^ ]+ )+  ', lambda results, match: results['spacegroup'] is None and not results['end'], read_spacegroup],
        ['^ *[Ee][Nn][Dd] *$', lambda results, match: results['has_cell'] and not results['end'], read_end],
    ], results=results, debug=False)

    #spacegroup = "".join(out['spacegroup'].split())
    #spacegroup = spacegroup[0]+(spacegroup[1:].lower())
    #print "GOT SPACEGROUP",spacegroup
    spacegroup = out['spacegroup']

    sgstruct = Structure.create(a=out['a'], b=out['b'], c=out['c'], alpha=out['alpha'], beta=out['beta'],
                                gamma=out['gamma'], occupancies=out['occupancies'], coords=out['coords'], spacegroup=spacegroup, tags={'platon_sg': spacegroup}).round()

    return sgstruct


def platon_styout_to_sgstruct(ioa):
    """
    Example input::
    
        Results for  id=[0] dblock_code=[44325-I New: F-43m 
        =====================================================
        
        Pearson code : cF   8  Sb  4.0  Al  4.0
        Cell parameters :   7.7782  7.7782  7.7782   90.000   90.000   90.000
        Space group symbol : F -4 3 m   Number in IT : 216
        
        Setting x,y,z             Origin ( 0.0000 0.0000 0.0000)  Gamma =  0.4330
        
               Al1       4(c)  1/4     1/4     1/4                             Al   1
              Sb1        4(a)  0       0       0                               Sb   1
        
        Wyckoff sequence : c a                                                                                                         
        
        Volume of Unit Cell :   470.5842
        
        
        OTHER Standardization with Similar Gamma :
        
        Setting -x,-y,-z          Origin ( 0.7500 0.7500 0.7500)  Gamma =  0.4330
        
              Sb1        4(c)  1/4     1/4     1/4                             Sb   1
               Al1       4(a)  0       0       0                               Al   1
        
        Wyckoff sequence : c a                                                                                                         
        
        Volume of Unit Cell :   470.5842
    """        
    results = {}
    results['cell'] = {}
    results['spacegroup'] = {}
    results['setting'] = []
    results['in_setting'] = False

    def cell_params(results, match):
        results['cell']['a'] = float(match.group(1))
        results['cell']['b'] = float(match.group(2))
        results['cell']['c'] = float(match.group(3))
        results['cell']['alpha'] = float(match.group(4))
        results['cell']['beta'] = float(match.group(5))
        results['cell']['gamma'] = float(match.group(6))

    def spacegroup(results, match):
        results['spacegroup']['symbol'] = match.group(1)
        results['spacegroup']['number'] = int(match.group(2))
    #def setting_start(results,match):
    #    results['setting'].append({'coords':[],'occupancies':[],'wycoff':[]})
    #    results['in_setting'] = True

    def setting_stop(results, match):
        results['in_setting'] = False

    def read_coords(results, match):
        if not results['in_setting']:
            results['setting'].append({'coords': [], 'occupancies': [], 'wycoff': []})
            results['in_setting'] = True
        results['setting'][-1]['coords'].append([match.group(4), match.group(5), match.group(6)])
        results['setting'][-1]['occupancies'].append(match.group(1))
        results['setting'][-1]['wycoff'].append([match.group(3)])
        results['in_setting'] = True
    #def debug(results,match):
    #    print "DEBUG",match
        
    out = httk.basic.micro_pyawk(ioa, [
        #['^Wyckoff',None,setting_stop],
        ['^ *$', None, setting_stop],
        ['^Cell parameters : +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([0-9.-]+)', None, cell_params],
        ['^Space group symbol : +(.+) +Number in IT : +([0-9]+)', None, spacegroup],
        ['^ +([a-zA-Z]+)([0-9]*)#* +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+)', None, read_coords],
        #['^Setting',None,setting_start],
    ], results=results, debug=False)

    structdata = dict(out['cell'].items() + 
                      [('coords', out['setting'][0]['coords']),
                       ('occupancies', out['setting'][0]['occupancies']),
                          ('spacegroup', out['spacegroup']['symbol'])
                       ])
    sgstruct = Structure.create(**structdata)
 
    return sgstruct


def structure_to_platon(ioa, struct, precards, postcards):
    """
    Writes a file on PLATONS input format.
    """
    ioa = httk.IoAdapterFileReader(ioa)
    f = ioa.file 
    if 'comment' in struct.get_tags():
        f.write("TITL "+str(struct.comment)+"\n")
    else:
        f.write("TITL structure\n")
    for card in precards:
        f.write(card+"\n")
    f.write("CESD 0.00001 0.00001 0.00001 0.00001 0.00001 0.00001\n")
    f.write("CELL "+str(struct.rc_a)+" "+str(struct.rc_b)+" "+str(struct.rc_c)+" ")
    f.write(str(struct.rc_alpha)+" "+str(struct.rc_beta)+" "+str(struct.rc_gamma)+"\n")
    idx = 1
    for i in range(struct.rc_nbr_atoms):
        species = struct.rc_occupancies[i]
        f.write(species+str(idx)+" ")
        f.write(" ".join([str(float(x)) for x in struct.coords[i]])+"\n")
        #print "X",species+str(idx)+" "+" ".join([str(float(x)) for x in struct.coords[i]])+"\n"
        idx = idx + 1
    for card in postcards:
        f.write(card+"\n")
    f.write("\n")
    ioa.close()


def sites_to_platon(ioa, sites, cell, precards, postcards):
    """
    Writes a file on PLATONS input format.
    """
    ioa = httk.IoAdapterFileWriter(ioa)
    f = ioa.file 
    f.write("TITL structure\n")
    for card in precards:
        f.write(card+"\n")
    f.write("CESD 0.00001 0.00001 0.00001 0.00001 0.00001 0.00001\n")
    f.write("CELL "+str(float(sites.cell.a))+" "+str(float(sites.cell.b))+" "+str(float(sites.cell.c))+" ")
    f.write(str(float(sites.cell.alpha))+" "+str(float(sites.cell.beta))+" "+str(float(sites.cell.gamma))+"\n")
    idx = 1
    for i in range(len(sites.reduced_coords)):
        species = sites.rc_occupancies[i]
        f.write(species+str(idx)+" ")
        f.write(" ".join([str(float(x)) for x in sites.coords[i]])+"\n")
        #print "X",species+str(idx)+" "+" ".join([str(float(x)) for x in struct.coords[i]])+"\n"
        idx = idx + 1
    for card in postcards:
        f.write(card+"\n")
    f.write("\n")
    ioa.close()


def platon_sites_to_styin(ioa, sites, cell):
    """
    Example input::

        P 4 B M              
            5.5179    5.5179    3.9073   90.0000   90.0000   90.0000
        Bi1       0.50000   0.00000   0.54500   0.50000
        Ti1       0.00000   0.00000   0.00000
        Na1       0.50000   0.00000   0.54500   0.50000
        O1        0.00000   0.00000   0.51000
        O2        0.72900   0.22900   0.01500
        END
        END
    """        
    ioa = httk.IoAdapterFileWriter(ioa)   
    f = ioa.file 
    sgsymbol = get_stidy_spacegroup(sites.hall_symbol)
    
    f.write(sgsymbol+"\n")
    f.write(" %9.4f %9.4f %9.4f " % (float(cell.a), float(cell.b), float(cell.c)))
    f.write("%9.4f %9.4f %9.4f\n" % (float(cell.alpha), float(cell.beta), float(cell.gamma)))
    for group in range(len(sites.reduced_coordgroups)):
        for i in range(len(sites.reduced_coordgroups[group])):
            f.write("%-3s" % (httk.basic.int_to_anonymous_symbol(group)+str(i)))
            f.write("     ")
            f.write("%9.5f %9.5f %9.5f\n" % (float(sites.reduced_coordgroups[group][i][0]), float(sites.reduced_coordgroups[group][i][1]), float(sites.reduced_coordgroups[group][i][2])))
    f.write("END\n")
    f.write("END\n")
    f.close()
    

def platon_styout_to_structure(ioa, based_on_struct=None):
    """
    Example input::
    
        Results for  id=[0] dblock_code=[44325-I New: F-43m 
        =====================================================
        
        Pearson code : cF   8  Sb  4.0  Al  4.0
        Cell parameters :   7.7782  7.7782  7.7782   90.000   90.000   90.000
        Space group symbol : F -4 3 m   Number in IT : 216
        
        Setting x,y,z             Origin ( 0.0000 0.0000 0.0000)  Gamma =  0.4330
        
               Al1       4(c)  1/4     1/4     1/4                             Al   1
              Sb1        4(a)  0       0       0                               Sb   1
        
        Wyckoff sequence : c a                                                                                                         
        
        Volume of Unit Cell :   470.5842
        
        
        OTHER Standardization with Similar Gamma :
        
        Setting -x,-y,-z          Origin ( 0.7500 0.7500 0.7500)  Gamma =  0.4330
        
              Sb1        4(c)  1/4     1/4     1/4                             Sb   1
               Al1       4(a)  0       0       0                               Al   1
        
        Wyckoff sequence : c a                                                                                                         
        
        Volume of Unit Cell :   470.5842
    """        
    results = {}
    results['cell'] = {}
    results['spacegroup'] = {}
    results['setting'] = []
    results['in_setting'] = False

    def cell_params(results, match):
        results['cell']['rc_a'] = float(match.group(1))
        results['cell']['rc_b'] = float(match.group(2))
        results['cell']['rc_c'] = float(match.group(3))
        results['cell']['rc_alpha'] = float(match.group(4))
        results['cell']['rc_beta'] = float(match.group(5))
        results['cell']['rc_gamma'] = float(match.group(6))

    def spacegroup(results, match):
        results['spacegroup']['symbol'] = match.group(1).strip()
        results['spacegroup']['number'] = match.group(2).strip()
    #def setting_start(results,match):
    #    results['setting'].append({'coords':[],'occupancies':[],'wycoff':[]})
    #    results['in_setting'] = True

    def setting_stop(results, match):
        results['in_setting'] = False

    def read_coords(results, match):
        if not results['in_setting']:
            results['setting'].append({'coords': [], 'occupancies': [], 'wyckoff': [], 'multiplicities': []})
            results['in_setting'] = True

        newcoord = FracVector.create([match.group(4), match.group(5), match.group(6)]).limit_denominator(5000000).simplify()
        #print "CHECK1",[match.group(4),match.group(5),match.group(6)]
        #print "CHECK2:",newcoord

        results['setting'][-1]['coords'].append([match.group(4), match.group(5), match.group(6)])
        
        if based_on_struct is None:
            results['setting'][-1]['occupancies'].append(match.group(1))
        else:
            abstract_symbol = match.group(1).strip()
            index = httk.basic.anonymous_symbol_to_int(abstract_symbol)
            results['setting'][-1]['occupancies'].append(based_on_struct.assignments[index])

        wyckoff_string = match.group(3)
        wyckoff_symbol = wyckoff_string[wyckoff_string.index("(") + 1:wyckoff_string.rindex(")")]
        multiplicity = int(wyckoff_string[:wyckoff_string.index("(")])
            
        results['setting'][-1]['wyckoff'].append(wyckoff_symbol)
        results['setting'][-1]['multiplicities'].append(multiplicity)
        results['in_setting'] = True
    #def debug(results,match):
    #    print "DEBUG",match
        
    out = httk.basic.micro_pyawk(ioa, [
        #['^Wyckoff',None,setting_stop],
        ['^ *$', None, setting_stop],
        ['^Cell parameters : +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([0-9.-]+)', None, cell_params],
        ['^Space group symbol : +(.+) +Number in IT : +([0-9]+)', None, spacegroup],
        ['^ +([a-zA-Z]+)([0-9]*)#* +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+)', None, read_coords],
        #['^Setting',None,setting_start],
    ], results=results, debug=False)

    #print "HX",out['setting'][0]['wyckoff']

    if based_on_struct is None:
        structdata = dict(out['cell'].items() + 
                          [('rc_reduced_occupationscoords', out['setting'][0]['coords']),
                           ('rc_occupancies', out['setting'][0]['occupancies']),
                              ('spacegroup', out['spacegroup']['symbol']),
                              ('wyckoff_symbols', out['setting'][0]['wyckoff'])
                           ])
        sgstruct = Structure.create(**structdata)        
    else:
        # Handle both normal structures and scaleless structures
        sg = Spacegroup.create(hm_symbol=out['spacegroup']['symbol'], spacegroupnumber=out['spacegroup']['number'])
        try:
            rc_cell = based_on_struct.rc_cell
            structdata = dict(out['cell'].items() + 
                              [('rc_reduced_occupationscoords', out['setting'][0]['coords']),
                               ('rc_occupancies', out['setting'][0]['occupancies']),
                                  ('spacegroup', sg), 
                                  ('rc_cell', rc_cell),
                                  ('wyckoff_symbols', out['setting'][0]['wyckoff']),
                                  ('multiplicities', out['setting'][0]['multiplicities'])
                               ]
                              )   
            sgstruct = based_on_struct.create(**structdata)        
            sgstruct.add_tags(based_on_struct.get_tags())
            sgstruct.add_refs(based_on_struct.get_refs())

        except AttributeError: 
            structdata = dict(out['cell'].items() + 
                              [('rc_reduced_occupationscoords', out['setting'][0]['coords']),
                               ('rc_occupancies', out['setting'][0]['occupancies']),
                                  ('spacegroup', sg),                             
                                  ('wyckoff_symbols', out['setting'][0]['wyckoff']),
                                  ('multiplicities', out['setting'][0]['multiplicities'])
                               ]
                              )
            sgstruct = based_on_struct.create(**structdata)        
            sgstruct.add_tags(based_on_struct.get_tags())
            sgstruct.add_refs(based_on_struct.get_refs())
            sgstruct.add_rc_cells(based_on_struct.get_rc_cells())

    return sgstruct


stidy_spacegroups = {
    1: ("P 1",),
    2: ("P -1",),
    3: ("P 2", "P 2 1 1", "P 1 2 1", "P 1 1 2",),
    4: ("P 21", "P 21 1 1", "P 1 21 1", "P 1 1 21",),
    5: ("C 2", "C 2 1 1", "C 1 2 1",),
    6: ("P m", "P m 1 1", "P 1 m 1", "P 1 1 m",),
    7: ("P c", "P c 1 1", "P 1 c 1",),
    8: ("C m", "C m 1 1", "C 1 m 1",),
    9: ("C c", "C c 1 1", "C 1 c 1",),
    10: ("P 2/m", "P 2/m 1 1", "P 1 2/m 1", "P 1 1 2/m",),
    11: ("P 21/m", "P 21/m 1 1", "P 1 21/m 1", "P 1 1 21/m",),
    12: ("C 2/m", "C 2/m 1 1", "C 1 2/m 1",),
    13: ("P 2/c", "P 2/c 1 1", "P 1 2/c 1",),
    14: ("P 21/c", "P 21/c 1 1", "P 1 21/c 1",),
    15: ("C 2/c", "C 2/c 1 1", "C 1 2/c 1",),
    16: ("P 2 2 2",),
    17: ("P 2 2 21", "P 21 2 2", "P 2 21 2", "P 2 21 2",),
    18: ("P 21 21 2", "P 2 21 21", "P 21 2 21",),
    19: ("P 21 21 21",),
    20: ("C 2 2 21", "A 21 2 2", "B 2 21 2",),
    21: ("C 2 2 2", "A 2 2 2", "B 2 2 2",),
    22: ("F 2 2 2",),
    23: ("I 2 2 2",),
    24: ("I 21 21 21",),
    25: ("P m m 2", "P 2 m m", "P m 2 m",),
    26: ("P m c 21", "P 21 m a", "P b 21 m",),
    27: ("P c c 2", "P 2 a a", "P b 2 b",),
    28: ("P m a 2", "P 2 m b", "P c 2 m",),
    29: ("P c a 21", "P 21 a b", "P c 21 b",),
    30: ("P n c 2", "P 2 n a", "P b 2 n",),
    31: ("P m n 21", "P 21 m n", "P n 21 m",),
    32: ("P b a 2", "P 2 c b", "P c 2 a",),
    33: ("P n a 21", "P 21 n b", "P c 21 n",),
    34: ("P n n 2", "P 2 n n", "P n 2 n",),
    35: ("C m m 2", "A 2 m m", "B m 2 m",),
    36: ("C m c 21", "A 21 m a", "B b 21 m",),
    37: ("C c c 2", "A 2 a a", "B b 2 b",),
    38: ("A m m 2", "B 2 m m", "C m 2 m",),
    39: ("A b m 2", "B 2 c m", "C m 2 a",),
    40: ("A m a 2", "B 2 m b", "C c 2 m",),
    41: ("A b a 2", "B 2 c b", "C c 2 a",),
    42: ("F m m 2", "F 2 m m", "F m 2 m",),
    43: ("F d d 2", "F 2 d d", "F d 2 d",),
    44: ("I m m 2", "I 2 m m", "I m 2 m",),
    45: ("I b a 2", "I 2 c b", "I c 2 a",),
    46: ("I m a 2", "I 2 m b", "I c 2 m",),
    47: ("P m m m",),
    48: ("P n n n",),
    49: ("P c c m", "P m a a", "P b m b",),
    50: ("P b a n", "P n c b", "P c n a",),
    51: ("P m m a", "P b m m", "P m c m",),
    52: ("P n n a", "P b n n", "P n c n",),
    53: ("P m n a", "P b m n", "P n c m",),
    54: ("P c c a", "P b a a", "P b c b",),
    55: ("P b a m", "P m c b", "P c m a",),
    56: ("P c c n", "P n a a", "P b n b",),
    57: ("P b c m", "P m c a", "P b m a",),
    58: ("P n n m", "P m n n", "P n m n",),
    59: ("P m m n", "P n m m", "P m n m",),
    60: ("P b c n", "P n c a", "P b n a",),
    61: ("P b c a", "P c a b",),
    62: ("P n m a", "P b n m", "P m c n",),
    63: ("C m c m", "A m m a", "B b m m",),
    64: ("C m c a", "A b m a", "B b c m",),
    65: ("C m m m", "A m m m", "B m m m",),
    66: ("C c c m", "A m a a", "B b m b",),
    67: ("C m m a", "A b m m", "B m c m",),
    68: ("C c c a", "A b a a", "B b c b",),
    69: ("F m m m",),
    70: ("F d d d",),
    71: ("I m m m",),
    72: ("I b a m", "I m c b", "I c m a",),
    73: ("I b c a", "I c a b",),
    74: ("I m m a", "I b m m", "I m c m",),
    75: ("P 4",),
    76: ("P 41",),
    77: ("P 42",),
    78: ("P 43",),
    79: ("I 4",),
    80: ("I 41",),
    81: ("P -4",),
    82: ("I -4",),
    83: ("P 4/m",),
    84: ("P 42/m",),
    85: ("P 4/n",),
    86: ("P 42/n",),
    87: ("I 4/m",),
    88: ("I 41/a",),
    89: ("P 4 2 2",),
    90: ("P 4 21 2",),
    91: ("P 41 2 2",),
    92: ("P 41 21 2",),
    93: ("P 42 2 2",),
    94: ("P 42 21 2",),
    95: ("P 43 2 2",),
    96: ("P 43 21 2",),
    97: ("I 4 2 2",),
    98: ("I 41 2 2",),
    99: ("P 4 m m",),
    100: ("P 4 b m",),
    101: ("P 42 c m",),
    102: ("P 42 n m",),
    103: ("P 4 c c",),
    104: ("P 4 n c",),
    105: ("P 42 m c",),
    106: ("P 42 b c",),
    107: ("I 4 m m",),
    108: ("I 4 c m",),
    109: ("I 41 m d",),
    110: ("I 41 c d",),
    111: ("P -4 2 m",),
    112: ("P -4 2 c",),
    113: ("P -4 21 m",),
    114: ("P -4 21 c",),
    115: ("P -4 m 2",),
    116: ("P -4 c 2",),
    117: ("P -4 b 2",),
    118: ("P -4 n 2",),
    119: ("I -4 m 2",),
    120: ("I -4 c 2",),
    121: ("I -4 2 m",),
    122: ("I -4 2 d",),
    123: ("P 4/m m m",),
    124: ("P 4/m c c",),
    125: ("P 4/n b m",),
    126: ("P 4/n n c",),
    127: ("P 4/m b m",),
    128: ("P 4/m n c",),
    129: ("P 4/n m m",),
    130: ("P 4/n c c",),
    131: ("P 42/m m c",),
    132: ("P 42/m c m",),
    133: ("P 42/n b c",),
    134: ("P 42/n n m",),
    135: ("P 42/m b c",),
    136: ("P 42/m n m",),
    137: ("P 42/n m c",),
    138: ("P 42/n c m",),
    139: ("I 4/m m m",),
    140: ("I 4/m c m",),
    141: ("I 41/a m d",),
    142: ("I 41/a c d",),
    143: ("P 3",),
    144: ("P 31",),
    145: ("P 32",),
    146: ("R 3",),
    147: ("P -3",),
    148: ("R -3",),
    149: ("P 3 1 2",),
    150: ("P 3 2 1",),
    151: ("P 31 1 2",),
    152: ("P 31 2 1",),
    153: ("P 32 1 2",),
    154: ("P 32 2 1",),
    155: ("R 3 2",),
    156: ("P 3 m 1",),
    157: ("P 3 1 m",),
    158: ("P 3 c 1",),
    159: ("P 3 1 c",),
    160: ("R 3 m",),
    161: ("R 3 c",),
    162: ("P -3 1 m",),
    163: ("P -3 1 c",),
    164: ("P -3 m 1",),
    165: ("P -3 c 1",),
    166: ("R -3 m",),
    167: ("R -3 c",),
    168: ("P 6",),
    169: ("P 61",),
    170: ("P 65",),
    171: ("P 62",),
    172: ("P 64",),
    173: ("P 63",),
    174: ("P -6",),
    175: ("P 6/m",),
    176: ("P 63/m",),
    177: ("P 6 2 2",),
    178: ("P 61 2 2",),
    179: ("P 65 2 2",),
    180: ("P 62 2 2",),
    181: ("P 64 2 2",),
    182: ("P 63 2 2",),
    183: ("P 6 m m",),
    184: ("P 6 c c",),
    185: ("P 63 c m",),
    186: ("P 63 m c",),
    187: ("P -6 m 2",),
    188: ("P -6 c 2",),
    189: ("P -6 2 m",),
    190: ("P -6 2 c",),
    191: ("P 6/m m m",),
    192: ("P 6/m c c",),
    193: ("P 63/m c m",),
    194: ("P 63/m m c",),
    195: ("P 2 3",),
    196: ("F 2 3",),
    197: ("I 2 3",),
    198: ("P 21 3",),
    199: ("I 21 3",),
    200: ("P m -3", "P m 3",),
    201: ("P n -3", "P n 3",),
    202: ("F m -3", "F m 3",),
    203: ("F d -3", "F d 3",),
    204: ("I m -3", "I m 3",),
    205: ("P a -3", "P a 3",),
    206: ("I a -3", "I a 3",),
    207: ("P 4 3 2",),
    208: ("P 42 3 2",),
    209: ("F 4 3 2",),
    210: ("F 41 3 2",),
    211: ("I 4 3 2",),
    212: ("P 43 3 2",),
    213: ("P 41 3 2",),
    214: ("I 41 3 2",),
    215: ("P -4 3 m",),
    216: ("F -4 3 m",),
    217: ("I -4 3 m",),
    218: ("P -4 3 n",),
    219: ("F -4 3 c",),
    220: ("I -4 3 d",),
    221: ("P m -3 m", "P m 3 m",),
    222: ("P n -3 n", "P n 3 n",),
    223: ("P m -3 n", "P m 3 n",),
    224: ("P n -3 m", "P n 3 m",),
    225: ("F m -3 m", "F m 3 m",),
    226: ("F m -3 c", "F m 3 c",),
    227: ("F d -3 m", "F d 3 m",),
    228: ("F d -3 c", "F d 3 c",),
    229: ("I m -3 m", "I m 3 m",),
    230: ("I a -3 d", "I a 3 d",)                     
}


def get_stidy_spacegroup(parse):
    idx = spacegroups.find_index(parse)
    symbols = spacegroups.spacegroups[idx][3]
    number = spacegroups.spacegroups[idx][0]
    for stidysymb in stidy_spacegroups[number]:
        for symb in symbols:
            if stidysymb.replace(" ", "") == symb:
                return stidysymb.upper()
    raise Exception("Cannot find matching stidy spacegroup symbol")
