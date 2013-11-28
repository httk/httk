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

import re, sys
from StringIO import StringIO

from httk.core import FracVector
from httk.core.htdata import periodictable
import httk  

import os, errno

def platon_lis_to_struct_broken(ioa):
    """
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
    def read_spacegroup(results,match):
        results['spacegroup']=match.group(1).strip()

    def read_a_alpha(results,match):
        results['a'] = float(match.group(1).replace('(','').replace(')',''))
        results['alpha'] = float(match.group(3).replace('(','').replace(')',''))

    def read_b_beta(results,match):
        results['b'] = float(match.group(1).replace('(','').replace(')',''))
        results['beta'] = float(match.group(3).replace('(','').replace(')',''))

    def read_c_gamma(results,match):
        results['c'] = float(match.group(1).replace('(','').replace(')',''))
        results['gamma'] = float(match.group(3).replace('(','').replace(')',''))

    def read_coords(results,match):
        sys.stdout.write("\n>>|")
        #for i in range(1,14):
        #    sys.stdout.write(match.group(i)+"|")
        species = periodictable.atomic_number(match.group(1))
        ratio = FracVector.create(re.sub(r'\([^)]*\)', '', match.group(11)))
        
        a1 = re.sub(r'\([^)]*\)', '',  match.group(2))
        b1 = re.sub(r'\([^)]*\)', '',  match.group(3))
        c1 = re.sub(r'\([^)]*\)', '',  match.group(4))

        a = match.group(2).replace('(','').replace(')','')
        b = match.group(3).replace('(','').replace(')','')
        c = match.group(4).replace('(','').replace(')','')
        coord = FracVector.create([a1,b1,c1]).normalize()
        sys.stdout.write(str(species)+" "+str(coord.to_floats()))
        limcoord = FracVector.create([a1,b1,c1]).normalize()
        coordtuple = ((species,ratio.to_tuple()),limcoord.to_tuple())
        if coordtuple in seen_coords:
            return
        results['occupancies'].append((species,float(ratio)))
        results['coords'].append(coord)
        seen_coords.add(coordtuple)

    def in_table(results,match):
        results['in_table'] = True

    def end_table(results,match):
        results['in_table'] = False

    def section(results,match):
        results['section'] = match.group(1)

    results={}
    results['spacegroup']=None
    results['section']=None
    results['in_table']=None
    results['occupancies']=[]
    results['coords']=[]
    out = httk.utils.micro_pyawk(ioa,[
            ['^ *Space Group +(([^ ]+ )+) +',lambda results,match: results['section']=='Space Group Symmetry' and results['spacegroup']==None,read_spacegroup],
            ['^ *a = +([0-9.()-]+) +(Angstrom)? +alpha = +([0-9.()-]+)',lambda results,match: results['section']=='Crystal Data',read_a_alpha],
            ['^ *b = +([0-9.()-]+) +(Angstrom)? +beta = +([0-9.()-]+)',lambda results,match: results['section']=='Crystal Data',read_b_beta],
            ['^ *c = +([0-9.()-]+) +(Angstrom)? +gamma = +([0-9.()-]+)',lambda results,match: results['section']=='Crystal Data',read_c_gamma],
            ['^ Asymmetric Residue Unit \(= ARU\) Code List *$',lambda results,match: results['in_table']==True,end_table],
            #['^ *=+ *$',lambda results,match: results['in_table']==True,end_table],
            ['^[^ ]* +[^A-Z]*([a-zA-Z]+)[^ ]* +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([^ ]*) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([^ \n]+) *$',lambda results,match: results['in_table']==True,read_coords],
            ['^ *Flags Label +Fractional Coordinates \(x,y,z\) +Orthogonal Coordinates \(XO,YO,ZO\) +',
                    lambda results,match: results['in_table']==None and results['section']=='Space Group Symmetry',in_table],
            ['^ *=+ ([A-Za-z ]+) =+ *$',None,section],
          ],results=results,debug=False)

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

    struct = httk.Structure.create(a=out['a'],b=out['b'],c=out['c'],alpha=out['alpha'],beta=out['beta'],
                                       gamma=out['gamma'],occupancies=occupancies,coords=out['coords'], tags={'platon_sg':out['spacegroup']}).round()

    return struct



def platon_lis_to_struct_broken2(ioa):
    """
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
    def read_spacegroup(results,match):
        results['spacegroup']=match.group(1).strip()

    def read_a_alpha(results,match):
        results['a'] = float(match.group(1).replace('(','').replace(')',''))
        results['alpha'] = float(match.group(3).replace('(','').replace(')',''))

    def read_b_beta(results,match):
        results['b'] = float(match.group(1).replace('(','').replace(')',''))
        results['beta'] = float(match.group(3).replace('(','').replace(')',''))

    def read_c_gamma(results,match):
        results['c'] = float(match.group(1).replace('(','').replace(')',''))
        results['gamma'] = float(match.group(3).replace('(','').replace(')',''))

    def read_coords(results,match):
        sys.stdout.write("\n>>|")
        #for i in range(1,14):
        #    sys.stdout.write(match.group(i)+"|")
        species = periodictable.atomic_number(match.group(1))
        ratio = FracVector.create(re.sub(r'\([^)]*\)', '', match.group(11)))
        
        a1 = re.sub(r'\([^)]*\)', '',  match.group(2))
        b1 = re.sub(r'\([^)]*\)', '',  match.group(3))
        c1 = re.sub(r'\([^)]*\)', '',  match.group(4))

        a = match.group(2).replace('(','').replace(')','')
        b = match.group(3).replace('(','').replace(')','')
        c = match.group(4).replace('(','').replace(')','')
        coord = FracVector.create([a1,b1,c1]).normalize()
        sys.stdout.write(str(species)+" "+str(coord.to_floats()))
        limcoord = FracVector.create([a1,b1,c1]).normalize()
        coordtuple = ((species,ratio.to_tuple()),limcoord.to_tuple())
        if coordtuple in seen_coords:
            return
        results['occupancies'].append((species,float(ratio)))
        results['coords'].append(coord)
        seen_coords.add(coordtuple)

    def in_table(results,match):
        results['in_table'] = True

    def end_table(results,match):
        results['in_table'] = False

    def section(results,match):
        results['section'] = match.group(1)

    results={}
    results['spacegroup']=None
    results['section']=None
    results['in_table']=None
    results['occupancies']=[]
    results['coords']=[]
    out = httk.utils.micro_pyawk(ioa,[
            ['^ *Space Group +(([^ ]+ )+) +',lambda results,match: results['section']=='Space Group Symmetry' and results['spacegroup']==None,read_spacegroup],
            ['^ *a = +([0-9.()-]+) +(Angstrom)? +alpha = +([0-9.()-]+)',lambda results,match: results['section']=='Crystal Data',read_a_alpha],
            ['^ *b = +([0-9.()-]+) +(Angstrom)? +beta = +([0-9.()-]+)',lambda results,match: results['section']=='Crystal Data',read_b_beta],
            ['^ *c = +([0-9.()-]+) +(Angstrom)? +gamma = +([0-9.()-]+)',lambda results,match: results['section']=='Crystal Data',read_c_gamma],
            ['^ Asymmetric Residue Unit \(= ARU\) Code List *$',lambda results,match: results['in_table']==True,end_table],
            #['^ *=+ *$',lambda results,match: results['in_table']==True,end_table],
            ['^[^ ]* +[^ ]* +[^ ]* +[^A-Z]*([a-zA-Z]+)[^ ]* +.* +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) +([/0-9.()-]+) *$',lambda results,match: results['in_table']==True,read_coords],
            ['^ *Angstrom Coordination Sphere Around Atom +',
                    lambda results,match: results['in_table']==None and results['section']=='Space Group Symmetry',in_table],
            ['^ *=+ ([A-Za-z ]+) =+ *$',None,section],
          ],results=results,debug=False)

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

    struct = httk.Structure.create(a=out['a'],b=out['b'],c=out['c'],alpha=out['alpha'],beta=out['beta'],
                                       gamma=out['gamma'],occupancies=occupancies,coords=out['coords'], tags={'platon_sg':out['spacegroup']}).round()

    return struct




def platon_styin_to_sgstruct(ioa):
    """
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

    def read_spacegroup(results,match):
        results['spacegroup']=match.group(0).strip()

    def read_cell(results,match):
        results['a'] = float(match.group(1))
        results['b'] = float(match.group(2))
        results['c'] = float(match.group(3))
        results['alpha'] = float(match.group(4))
        results['beta'] = float(match.group(5))
        results['gamma'] = float(match.group(6))
        results['has_cell'] = True

    def read_coords(results,match):
        results['occupancies'].append(periodictable.atomic_number(match.group(1)))
        results['coords'].append([float(match.group(2)),float(match.group(3)),float(match.group(4))])

    def read_end(results,match):
        results['end'] = True

    results={}
    results['spacegroup']=None
    results['has_cell']=False
    results['occupancies']=[]
    results['coords']=[]
    results['end']=False
    out = httk.utils.micro_pyawk(ioa,[
            ['^ *([a-zA-Z]+)[^ ]* +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) *$',lambda results,match: results['has_cell'] and not results['end'],read_coords],
            ['^ *([0-9.-]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) +([0-9.-]+) *$',lambda results,match: results['spacegroup']!=None and not results['end'],read_cell],
            ['^ *([^ ]+ )+  ',lambda results,match: results['spacegroup']==None and not results['end'],read_spacegroup],
            ['^ *[Ee][Nn][Dd] *$',lambda results,match: results['has_cell'] and not results['end'],read_end],
          ],results=results,debug=False)

    #spacegroup = "".join(out['spacegroup'].split())
    #spacegroup = spacegroup[0]+(spacegroup[1:].lower())
    #print "GOT SPACEGROUP",spacegroup
    spacegroup = out['spacegroup']

    sgstruct = httk.Structure.create(a=out['a'],b=out['b'],c=out['c'],alpha=out['alpha'],beta=out['beta'],
                                       gamma=out['gamma'],occupancies=out['occupancies'],coords=out['coords'], spacegroup=spacegroup, tags={'platon_sg':spacegroup}).round()

    return sgstruct

def platon_styout_to_sgstruct(ioa):
    """
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
    results={}
    results['cell'] = {}
    results['spacegroup'] = {}
    results['setting'] = []
    results['in_setting'] = False
    def cell_params(results,match):
        results['cell']['a'] = float(match.group(1))
        results['cell']['b'] = float(match.group(2))
        results['cell']['c'] = float(match.group(3))
        results['cell']['alpha'] = float(match.group(4))
        results['cell']['beta'] = float(match.group(5))
        results['cell']['gamma'] = float(match.group(6))
    def spacegroup(results,match):
        results['spacegroup']['symbol'] = match.group(1)
        results['spacegroup']['number'] = int(match.group(2))
    #def setting_start(results,match):
    #    results['setting'].append({'coords':[],'occupancies':[],'wycoff':[]})
    #    results['in_setting'] = True
    def setting_stop(results,match):
        results['in_setting'] = False
    def read_coords(results,match):
        if not results['in_setting']:
            results['setting'].append({'coords':[],'occupancies':[],'wycoff':[]})
            results['in_setting'] = True
        results['setting'][-1]['coords'].append([match.group(4),match.group(5),match.group(6)])
        results['setting'][-1]['occupancies'].append(match.group(1))
        results['setting'][-1]['wycoff'].append([match.group(3)])
        results['in_setting'] = True
    #def debug(results,match):
    #    print "DEBUG",match
        
    out = httk.utils.micro_pyawk(ioa,[
            #['^Wyckoff',None,setting_stop],
            ['^ *$',None,setting_stop],
            ['^Cell parameters : +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([0-9.-]+)',None,cell_params],
            ['^Space group symbol : +(.+) +Number in IT : +([0-9]+)',None,spacegroup],
            ['^ +([a-zA-Z]+)([0-9]*)#* +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+)',None,read_coords],
            #['^Setting',None,setting_start],
          ],results=results,debug=False)

    structdata=dict(out['cell'].items() + 
                    [('coords', out['setting'][0]['coords']),
                     ('occupancies',out['setting'][0]['occupancies']),
                     ('spacegroup',out['spacegroup']['symbol'])
                     ])
    sgstruct = httk.Structure.create(**structdata)
 
    return sgstruct


def structure_to_platon(ioa,struct,precards,postcards):
    """
    Writes a file on PLATONS input format.
    """        
    ioa = httk.IoAdapterFileReader(ioa)
    f=ioa.file 
    if 'comment' in struct.tags:
        f.write("TITL "+str(struct.comment)+"\n")
    else:
        f.write("TITL structure\n")
    for card in precards:
        f.write(card+"\n")
    f.write("CESD 0.0000001 0.0000001 0.0000001 0.0000001 0.0000001 0.0000001\n")
    f.write("CELL "+str(struct.sa)+" "+str(struct.sb)+" "+str(struct.sc)+" ")
    f.write(str(struct.alpha)+" "+str(struct.beta)+" "+str(struct.gamma)+"\n")
    idx=1
    for i in range(struct.N):
        species = periodictable.atomic_symbol(struct.occupancies[i])
        f.write(species+str(idx)+" ")
        f.write(" ".join([str(float(x)) for x in struct.coords[i]])+"\n")
        #print "X",species+str(idx)+" "+" ".join([str(float(x)) for x in struct.coords[i]])+"\n"
        idx = idx + 1
    for card in postcards:
        f.write(card+"\n")
    f.write("\n")
    ioa.close()



    
