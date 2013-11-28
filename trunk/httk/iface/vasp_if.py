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

import os

from httk.core.htdata import periodictable
from httk.core import *

def get_pseudopotential(species):
    f = open(os.path.expanduser('/opt/vasp/Pseudopotentials.httk/PBE/POTCAR.'+species))
    data = f.read()
    f.close()
    return data

def write_generic_kpoints_file(fio, comment="",mp=True):
    """
    """        
    fio = IoAdapterFileWriter.use(fio)    
    f = fio.file
    f.write(str(comment)+"\n")
    f.write("0\n")
    #if mp:
    #    f.write("Monkhorst-Pack\n")
    #else:
    #    f.write("Gamma\n")
    f.write("Auto\n")
    f.write("100\n")
    fio.close()

def get_magmom(symbol):
    return 8

# def write_generic_incar_file(fio, assignments, counts, comment=""):
#     """
#     """
#     spieces_counts=[]
#     magmoms=[]
#     for i in range(len(assignments)):
#         assignment = assignments[i]
#         count = counts[i]
#         symbol = periodictable.atomic_symbol(assignment)
#         spieces_counts.append(count)
#         magmoms.append(str(count)+"*"+str(get_magmom(symbol)))
# 
#     VASP_SPIECES_COUNTS=" ".join(map(str,spieces_counts))
#     VASP_MAGMOM=" ".join(map(str,magmoms))
# 
#     SYSTEM=$name
#     
#     ALGO=Fast
#     LORBIT=11
#     ISIF=3
#     SYSTEM=$name
#     NELM=100
#     LREAL=Auto
#     IBRION=2
#     EDIFF=1E-6
#     EDIFFG=1E-4
#     NSW=200
#     PREC=high
#     NELMIN=3
#     ISMEAR=-5
#     ICHARG=1
#     ISPIN=2
#     SIGMA=0.05
#     NPAR=1
#     LWAVE=.FALSE.
#     
#     EDIFF=1E-6
#     EDIFFG=1E-4
#     
#     MAGMOM=$(c.VASP_MAGMOM)
# 
#     
#     fio = IoAdapterFileWriter.use(fio)    
#     f = fio.file
#     f.write(str(comment)+"\n")
#     f.write("0\n")
#     #if mp:
#     #    f.write("Monkhorst-Pack\n")
#     #else:
#     #    f.write("Gamma\n")
#     f.write("Auto\n")
#     f.write("100\n")
#     fio.close()

def poscar_to_strs(f):
    """
    Parses a file on VASPs POSCAR format. Returns 
      (cell, scale, vol, coords, coords_reduced, counts, occupations, comment)
    where
      cell: 3x3 nested list of *strings* designating the cell
      scale: *string* representing the overall scale of the cell
      vol: *string* representing the volume of the cell (only one of scale and vol will be set, the other one = None)
      coords: Nx3 nested list of *strings* designating the coordinates
      coords_reduced: bool, true = coords are given in reduced coordinate (in vasp D or Direct), false = coords are given in cartesian coordinates
      counts: how many atoms of each type
      occupations: which species of each atom type (integers), or -1, ... -N if no species are given.
      comment: the comment string given at the top of the file
    """
    fi = iter(f)

    comment = next(fi).strip()
    vol_or_scale = next(fi).strip()
    vol_or_scale_nbr = float(vol_or_scale)
    if vol_or_scale_nbr < 0:
        vol = vol_or_scale[1:]
        scale = None
    else:
        scale = vol_or_scale
        vol = None

    cell = [['','',''],['','',''],['','','']]        
    for i in [0,1,2]:
        cellline = next(fi).strip().split()
        for j,v in enumerate(cellline):
            cell[i][j] = v
   
    symbols_or_count = next(fi).strip().split()

    try:
        counts = map(int,symbols_or_count)
        symbols = None
        occupations = range(-1,-len(counts)-1,-1)
    except Exception:
        symbols = symbols_or_count
        counts = [int(s) for s in next(fi).strip().split()]
        occupations = [periodictable.numbers[symbol] for symbol in symbols]

    N = sum(counts)

    coordtype_or_selectivedynamics = next(fi).strip()
    if coordtype_or_selectivedynamics[0] in 'Ss':       
        # Skip row if selective dynamics specifier
        coordtype = next(fi).strip()        
    else:
        coordtype = coordtype_or_selectivedynamics

    if coordtype[0] in 'CcKk':
        coords_reduced = True
    else:
        coords_reduced = False

    coords = []
    for i in range(N):
        strcoord = next(fi).strip().split()[:3]
        coord = map(lambda x: x.strip(),strcoord)
        coords.append(coord)

    return (cell, scale, vol, coords, coords_reduced, counts, occupations, comment)

def poscar_to_structure(f):
    cell, scale, volume, coords, coords_reduced, counts, occupations, comment = poscar_to_strs(f)

    frac_cell = FracVector.create(cell,simplify=True)
    counts = [int(x) for x in counts]   
        
    if coords_reduced == True:
        #print "WARNING: Input POSCAR with cartesian coordinates. Due to nessecary conversion into reduced coordinates," 
        #print "there is no guarantee of an exactly preserved output on all computer architechtures."
        frac_coords = structure.cartesian_to_reduced(cell, coords)
    else:
        frac_coords = FracVector.create(coords,simplify=True)   

    #frac_coordgroups = FracVector.create(httk.structure.coords_to_coordgroups(frac_coords, counts))

    if volume != None:
        volume = float(volume)

    if scale != None:
        scale = float(scale)

    newoccupations = []
    for occupation in occupations:
        newoccupations.append(periodictable.atomic_number(occupation))

    struct = Structure.create(cell=frac_cell, coords=frac_coords, counts=counts, scale=scale, volume=volume, assignments=newoccupations, tags={'comment':comment})

    return struct

def write_poscar(fio, cell, coords, coords_reduced, counts, occupations,comment="Comment",scale="1",vol=None):
    """
    Writes a file on VASPs POSCAR format. Where it says *string* below, any type that works with str(x) is also ok.

    Input arguments  
      f: file stream to put output on  
      cell: 3x3 nested list of *strings* designating the cell
      coords: Nx3 nested list of *strings* designating the coordinates
      coords_reduced: bool, true = coords are given in reduced coordinate (in vasp D or Direct), false = coords are given in cartesian coordinates
      counts: how many atoms of each type
      occupations: which species of each atom type
      comment: (optional) the comment string given at the top of the file
      scale: (optional) *string* representing the overall scale of the cell
      vol: *string* representing the volume of the cell (only one of scale and vol can be set)
    """        
    fio = IoAdapterFileWriter.use(fio)    
    f = fio.file
    f.write(str(comment)+"\n")
    if vol != None:
        f.write("-"+str(vol)+"\n")
    else:
        f.write(str(scale)+"\n")
    for c1, c2, c3 in cell:  
        f.write(str(c1)+" "+str(c2)+" "+str(c3)+"\n")

    for i in range(len(counts)):
        if occupations == None:
            f.write(periodictable.symbols[i] + " ")
        else:
            f.write(str(occupations[i]) + " ")
    f.write("\n")
 
    for count in counts:
        f.write(str(count) + " ")
    f.write("\n")
    if coords_reduced:
        f.write("D\n")
    else:
        f.write("K\n")
    for c1, c2, c3 in coords:
        f.write(str(c1)+" "+str(c2)+" "+str(c3)+"\n")
    fio.close()

def structure_to_poscar(f, struct):    
    assignments = [periodictable.atomic_symbol(x) for x in struct.p1assignments]
    write_poscar(f, struct.cell.to_floats(), struct.p1coords.to_floats(), True, struct.p1counts, assignments, struct.formula + " " + struct.hexhash + " " + str(struct.tags),scale=struct.scale)

    