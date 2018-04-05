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

import os, shutil, math, re

import httk
from httk import config
from httk.core.template import apply_templates 
from httk.atomistic.data import periodictable
from httk.core.ioadapters import cleveropen 
from httk.core import *
from httk.core.basic import mkdir_p, micro_pyawk
from httk.atomistic import Structure
from httk.atomistic.structureutils import cartesian_to_reduced

def get_pseudopotential(species, poscarspath=None):
    if poscarspath == None:
        try:   
            poscarspath=config.get('paths', 'vasp_pseudolib')
        except Exception:
            #return [name for name in os.listdir(a_dir)
            #        if os.path.isdir(os.path.join(a_dir, name))]    
            poscarspath = None

    if poscarspath == None and "VASP_PSEUDOLIB" in os.environ:
        poscarspath = os.environ['VASP_PSEUDOLIB']

    if poscarspath == None:
        raise Exception("httk.iface.vasp_if.get_pseudopotentials: No path given for where to find VASP pseudopotentials. \
                         Please either set vasp_pseudolib in httk.cfg, or define the VASP_PSEUDOLIB variable, or \
                         pass along a string in your code for the parameter 'poscarspath'")

    poscarspath = os.path.expanduser(poscarspath)

    for priority in ["_3","_2","_d","_pv","_sv","","_h","_s"]:
        basepath = os.path.join(poscarspath,species)
        if os.path.exists(basepath+priority):
            try:
                f = cleveropen(os.path.join(basepath+priority,'POTCAR'),'r')
                data = f.read()
                f.close()
                return data
            except Exception:
                raise
                pass

    raise Exception("httk.iface.vasp_if.get_pseudopotentials: could not find a suitable pseudopotential for "+str(species))            


def write_kpoints_file(fio, kpoints, comment=None,mp=True, gamma_centered=False):
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
    if gamma_centered:
        f.write("Gamma\n")
    else:
        f.write("Monkhorst-Pack\n")
    f.write(" ".join([str(x) for x in kpoints])+"\n")
    fio.close()


def write_generic_kpoints_file(fio, comment=None,mp=True):
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
    f.write("20\n")
    fio.close()

def get_magmom(symbol):
    return 8

#magions = ['Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Y','Zr','Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd','La','Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg','Ce','Pr','Nd','Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu','Th','Pa','U']
# From: A. Jain et al. / Computational Materials Science 50 (2011) 2295-2310
magions = ['Ag','Au','Cd','Ce','Co','Cr','Cu','Dy','Er','Eu','Fe','Gd','Hf','Hg','Ho','Ir','La','Lu','Mn','Mo','Nb','Nd','Ni','Os','Pa','Pd','Pm','Pr','Pt','Re','Rh','Ru','Sc','Sm','Ta','Tb','Tc','Th','Ti','Tm','U','V','W','Y','Yb','Zn','Zr']
dualmag = {'O':['Co'], 'S':['Mn','Fe','Cr','Co']}

def is_dualmagnetic(ion,ionlist):
    for i in range(len(ionlist)):
        if dualmag.has_key(ionlist[i]):
            if ion in dualmag[ionlist[i]]:
                return True
    return False

def magnetization_recurse(basemags,dualmags,high,low):
    if len(dualmags) == 0:
        return [basemags]
    
    index = dualmags.pop()
    basemags[index] = high
    hi_list = magnetization_recurse(list(basemags),list(dualmags),high,low)
    basemags[index] = low
    low_list = magnetization_recurse(list(basemags),list(dualmags),high,low)

    return hi_list + low_list
    

def get_magnetizations(ionlist,high,low):
    basemags = []
    dualmags = []
    for i in range(len(ionlist)):
        if is_dualmagnetic(ionlist[i],ionlist):
            basemags.append(None)
            dualmags.append(i)
        else:
            if ionlist[i] in magions:
                basemags.append(high)
            else:
                basemags.append(low)
                
    return magnetization_recurse(basemags,dualmags,high,low)
    
def copy_template(dirtemplate, dirname, templatename):
    template = os.path.join(dirname,"ht.template."+templatename)
    if os.path.exists(template):
        raise Exception("Template dir already exists.")
    shutil.copytree(dirtemplate, template, True)


def poscar_to_strs(fio):
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
    fio = IoAdapterFileReader.use(fio)    
    f = fio.file
    
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
        frac_coords = cartesian_to_reduced(cell, coords)
    else:
        frac_coords = FracVector.create(coords,simplify=True)   

    if volume != None:
        volume = FracScalar.create(volume)

    if scale != None:
        scale = FracScalar.create(scale)

    newoccupations = []
    for occupation in occupations:
        newoccupations.append(periodictable.atomic_number(occupation))

    struct = Structure.create(uc_cell=frac_cell, uc_volume=volume, uc_scale=scale, uc_reduced_coords=frac_coords, uc_counts=counts, assignments=newoccupations, tags={'comment':comment}, periodicity=0)

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

def structure_to_comment(struct):
    tags =  struct.get_tags().values()
    if len(tags) > 0:
        tagstr = " tags: " + ", ".join([tag.tag+":"+tag.value for tag in tags])        
    else:
        tagstr = ""
    if struct.has_rc_repr and struct.has_uc_repr:
        return struct.formula + " " + struct.hexhash + tagstr
    else:
        return struct.formula + " " + tagstr

def structure_to_poscar(f, struct, fix_negative_determinant=False, comment=None):    
    if comment == None:
        comment = structure_to_comment(struct)
    basis = struct.uc_basis
    coords = struct.uc_reduced_coords
    if basis.det() < 0:
        if fix_negative_determinant:
            basis = -basis
            coords = -coords
    
    write_poscar(f, basis.to_floats(), coords.to_floats(), True, struct.uc_counts, struct.symbols, comment,vol=float(struct.uc_volume))

def calculate_kpoints(struct,dens=20):
    #local KPTSLINE=$(awk -v "LVAL=$LVAL" -v"equalkpts=$EQUAL_KPTS" -v"bumpkpts=$BUMP_KPTS" '
    basis = struct.uc_basis
    
    celldet = basis.det()
    cellvol = abs(celldet)

    if cellvol == 0:
        raise Exception("vasp_if.calculate_kpoints: Error in VASP_KPOINTSLINE: singular cell vectors. POSCAR is broken.")

    recip = basis.reciprocal().simplify()
    half = 0.5
    N1=int(math.ceil(math.sqrt(recip[0].lengthsqr())*dens+half)+0.1)
    N2=int(math.ceil(math.sqrt(recip[1].lengthsqr())*dens+half)+0.1)
    N3=int(math.ceil(math.sqrt(recip[2].lengthsqr())*dens+half)+0.1)
    return max(1,N1), max(1,N2), max(1,N3)

def parse_kpoints(ioa):
    ioa = IoAdapterFileReader.use(ioa)
    fi = iter(ioa)
    comment = next(fi).strip()
    points = int(next(fi).split()[0].strip())
    mode = next(fi).strip()[0].lower()
    if mode != 'l':
        raise Exception("parse_kpoints: Only line-mode supported.")
    cart_or_rec = next(fi).strip()[0].lower()   
    if cart_or_rec != 'r':
        raise Exception("parse_kpoints: Only reciprocal coordinates supported.")
    klines = []
    finished = False
    while not finished:
        kline = {'from_symbol':None, 'to_symbol':None, 'from_rec':None, 'to_rec':None}
        try:
            fromline = next(fi).strip().split()
            toline = next(fi).strip().split()
            #print "FROM",fromline,"TO",toline
        except StopIteration:
            break
        try:
            blankline = next(fi).strip()
            #print "BLANKLINE",blankline
            #if blankline != '':
            #    raise Exception("parse_kpoints: unexpected format.")
        except StopIteration:
            finished = True
        kline['from_symbol'] = "".join(fromline[3:]).lstrip('! ')
        kline['to_symbol'] ="".join(toline[3:]).lstrip('! ')
        kline['from_rec'] = fromline[0:3]
        kline['to_rec'] =  toline[0:3]
        klines += [kline]
    ioa.close()
    return {'klines':klines,'comment':comment,'points':points,'mode':mode,'cart_or_rec':cart_or_rec}

def parse_doscar(ioa): 
    ioa = IoAdapterFileReader.use(ioa)
    fi = iter(ioa)
    dummy = next(fi).strip()
    dummy = next(fi).strip()
    dummy = next(fi).strip()
    dummy = next(fi).strip()
    dummy = next(fi).strip()
    header = next(fi).strip().split()        
    count = int(header[2])
    spins = None
    energies = []
    tdos = None
    idos = None
    for i in range(count):
        dosline = next(fi).strip().split()
        if spins is None:
            if len(dosline) >= 3:
                spins = 2
                tdos=[[],[]]
                idos=[[],[]]
            else:
                spins = 1
                tdos=[[]]
                idos=[[]]
        energies += [dosline[0]]
        if spins == 1:
            tdos[0]+=[dosline[1]]
            idos[0]+=[dosline[2]]
        else:
            tdos[0]+=[dosline[1]]
            tdos[1]+=[dosline[2]]
            idos[0]+=[dosline[3]]
            idos[1]+=[dosline[4]]           
    return {'energies':energies,'tdos':tdos,'idos':idos}
            
def parse_outcar(ioa,get_fermi=True,get_kpts_and_eigvals=True):
    ioa = IoAdapterFileReader.use(ioa)
    spin_regex = re.compile('^ *spin component *([12]) *$')
    kline_regex = re.compile('^ *k-point *([0-9]+) *: *([0-9.]+) *([0-9.]+) *([0-9.]+) *$')
    bandheader_regex = re.compile('^ *band No\. *band energies *occupation *$')
    fermi_regex = re.compile('^ *E-fermi *: *([0-9.-]+) .*$')
    energy_regex = re.compile("^ *energy *without *entropy= *([^ ]+) *energy\(sigma->0\) *= *([^ ]+) *$")
    emptyline_regex = re.compile('^ *$')
    kpts=[]
    banddata = []
    eigvals_present_k = []
    in_band = False
    fermi = None
    spin = 0
    for line in ioa:
        if get_kpts_and_eigvals:
            m = spin_regex.match(line)
            if m is not None:
                spin = int(m.group(1))-1
            if spin == 0:
                m = kline_regex.match(line)
                if m is not None:
                    kpts += [(m.group(2),m.group(3),m.group(4))]
            if bandheader_regex.match(line):
                in_band = True
                continue
            if in_band and emptyline_regex.match(line):
                if len(banddata) < spin+1:
                    banddata += [[]]
                banddata[spin] += [eigvals_present_k]
                eigvals_present_k = []
                in_band = False
            if in_band:
                eigvals_present_k += [line.split()[1]]
        if get_fermi:
            m = fermi_regex.match(line)
            if m is not None:
                fermi = m.group(1)
        m = energy_regex.match(line)
        if m is not None:
            final_energy_with_entropy = m.group(1)
            final_energy=m.group(2)

    ioa.close()
    result = {'final_energy_with_entropy':final_energy_with_entropy,'final_energy':final_energy}
    if get_kpts_and_eigvals:
        result['kpts'] = kpts
        result['banddata'] = banddata
    if get_fermi:
        result['fermi'] = fermi

    return result


def prepare_single_run(dirpath, struct, poscarspath=None, template='t:/vasp/single/static',overwrite=False):
    if overwrite:
        mkdir_p(dirpath)
    else:
        os.mkdir(dirpath)
    structure_to_poscar(os.path.join(dirpath,"POSCAR"),struct,fix_negative_determinant=True)         
    #write_generic_kpoints_file(os.path.join(dirpath,"KPOINTS"),comment=structure_to_comment(struct))
    kpoints = calculate_kpoints(struct)
    write_kpoints_file(os.path.join(dirpath,"KPOINTS"),kpoints,comment=structure_to_comment(struct))
    ioa = IoAdapterFileWriter.use(os.path.join(dirpath,"POTCAR"))
    f = ioa.file			
    spieces_counts=[]
    magmomlist = get_magnetizations(struct.symbols,5,1)
    magmom_per_ion=magmomlist[0]
    magmoms=[]
    nelect=0
    natoms=0
    nmag=0
    for i in range(len(struct.assignments)):
        assignment = struct.assignments[i]
        count = struct.uc_counts[i]
        symbol = periodictable.atomic_symbol(assignment.symbol)
        pp = get_pseudopotential(symbol,poscarspath)
        f.write(pp)
        spieces_counts.append(count)
        #magmoms.append(str(count)+"*"+str(get_magmom(symbol)))    
        magmom = magmom_per_ion[i]
        magmoms.append(str(count)+"*"+str(magmom))    
        
        def zval(results,match):
            results['zval']=float(match.group(1))
        results = micro_pyawk(IoAdapterString(pp),[["^ *POMASS.*; *ZVAL *= *([^ ]+)",None,zval]])
        if not 'zval' in results:
            raise Exception("vasp_if.prepare_simple_static_run: Could not read ZVAL from potcar file")
        nelect += results['zval']*count
        natoms += count
        nmag += count*magmom

    ioa.close()
    nbands1=int(0.6*nelect + 1.0)+int(math.ceil(natoms/2.0)+0.1)
    nbands2=int(0.6*nelect + 1.0)+int(math.ceil(nmag/2.0)+0.1)
    nbands3=int(0.6*nelect + 1.0)+20
    nbands_spin = max(1,nbands1,nbands2,nbands3)
    nbands_spin += nbands_spin % 2
    nbands1=int(nelect/2.0 + 2)+int(math.ceil(natoms/2.0)+0.1)
    nbands2=int(math.ceil(nelect/2.0)+20+0.1)
    nbands_nospin = max(1,nbands1,nbands2)
    nbands_nospin += nbands_spin % 2
    
    data={}	
    data['VASP_SPIECES_COUNTS'] = " ".join(map(str,spieces_counts))
    data['VASP_MAGMOM'] = " ".join(map(str,magmoms))
    data['VASP_NBANDS_SPIN'] = str(nbands_spin)
    data['VASP_NBANDS_NOSPIN'] = str(nbands_nospin)

    if template.startswith('t:'):
        template = os.path.join(httk.httk_dir,'Execution','tasks-templates',template[2:])
    
    apply_templates(template, dirpath, envglobals=data, mkdir=False)


def eigenvalues_to_bandlines(eigenvalues,klist):
    """
    Returns bandlines which is an array per spin per each kline,
    containing a list with one entry per bands of ['relative kpoint
    distance', 'energy'] for each kpoint in that kline
    """
    kcount = len(eigenvalues[0])
    bandcount = len(eigenvalues[0][0])
    if len(eigenvalues)==2:
        spins=[0, 1]
        bandlines = [[None]*len(klist), [None]*len(klist)]
    else:
        bandlines = [[None]*len(klist)]
        spins=[0]

    for spin in spins:
        for i in range(len(klist)):
            bandlines[spin][i] = [None]*bandcount
            for j in range(bandcount):
                bandlines[spin][i][j] = [[None, None] for _x in klist[i]['kpts']]
   
    for spin in spins:
        for band in range(bandcount):
            kcount = 0
            startkdist = 0
            for i in range(len(klist)):
                kline=klist[i]
                startk = kline['kpts'][0]
                endk = kline['kpts'][-1]
                kdist = 0
                for j in range(len(kline['kpts'])):
                    kpos = kline['kpts'][j]
                    kstep = math.sqrt(((startk-kpos).lengthsqr()).to_float())
                    kdist = startkdist + kstep
                    bandlines[spin][i][band][j][0]=kdist
                    bandlines[spin][i][band][j][1]=eigenvalues[spin][kcount][band]                    
                    kcount+=1

                # Continue next band from this relative kdist                
                startkdist += kstep
        
    return FracVector.create(bandlines)

def construct_klists(klines,points,recbasis):
    for kline in klines:
        start=recbasis*kline['from_rec']
        stop=recbasis*kline['to_rec']
        print "KLINE",kline['from_symbol'],kline['to_symbol'],start.to_floats(),stop.to_floats()
        kpts = [None]*points
        for step in range(points):
            kpts[step]=(start + FracVector.create(step,(points-1))*(stop-start)).simplify()
        kline['kpts']=kpts

def gapdata_eigenvalues(eigenvalues, kpts, fermi):

    epsfracvec=FracVector.create(1,1000000)
    
    spins = len(eigenvalues)
    
    spinhomo = [None]*spins
    spinhomo_k = [None]*spins
    spinlumo = [None]*spins
    spinlumo_k = [None]*spins
    homo = [None]*spins
    lumo = [None]*spins
    spingap = [None]*spins
    min_of_spingaps = None
    direct_spingap = [None]*spins
    direct_spingap_k = [None]*spins
    direct_gap = None
    direct_gap_k = None
    
    for k in range(len(kpts)):    
        direct_spingap_this_k = [None]*spins
        for spin in range(spins):
            spinhomo_direct = None
            spinlumo_direct = None
            for band in range(len(eigenvalues[0][0])):
                e = eigenvalues[spin][k][band]
                # the calculation places fermi = highest occupied, so to avoid floating point
                # issues we need to pull the fermi level down epsilon to make sure to get *that* level
                if e <= fermi-epsfracvec:
                    if spinhomo[spin] is None or e > spinhomo[spin]:
                        spinhomo[spin]=e
                        spinhomo_k[spin]=kpts[k]
                    if spinhomo_direct is None or e > spinhomo_direct:
                        spinhomo_direct=e
                else:
                    if spinlumo[spin] is None or e < spinlumo[spin]:
                        spinlumo[spin]=e
                        spinlumo_k[spin]=kpts[k]
                    if spinlumo_direct is None or e < spinlumo_direct:
                        spinlumo_direct=e
            direct_spingap_this_k[spin] = spinlumo_direct - spinhomo_direct
            if direct_spingap[spin] == None or direct_spingap_this_k[spin] < direct_spingap[spin]:
                direct_spingap[spin] = direct_spingap_this_k[spin]
                direct_spingap_k[spin] = kpts[k]
        direct_gap_this_k = min(direct_spingap_this_k)
        if direct_gap == None or direct_gap > direct_gap_this_k:
            direct_gap = direct_gap_this_k
            direct_gap_k = kpts[k]

    for spin in range(spins):
        spingap[spin] = spinlumo[spin] - spinhomo[spin]

    min_of_spingaps = min(spingap)

    if spins > 1 and spinhomo[1] > spinhomo[0]:
        homo = spinhomo[1]
        homo_k = spinhomo_k[1]
    else:
        homo = spinhomo[0]
        homo_k = spinhomo_k[0]
        
    if spins > 1 and spinlumo[1] < spinlumo[0]:
        lumo = spinlumo[1]
        lumo_k = spinlumo_k[1]
    else:
        lumo = spinlumo[0]
        lumo_k = spinlumo_k[1]                    
    gap = lumo - homo

    results = {'gap':gap, 'homo':homo, 'lumo':lumo, 'homo_k':homo_k, 'lumo_k':lumo_k, 
            'direct_gap':direct_gap, 'direct_gap_k':direct_gap_k}
    
    if spins > 1:
        spinresults = {'min_of_spingaps':min_of_spingaps,
                       'spinhomo':spinhomo, 'spinlumo':spinlumo, 'spinhomo_k':spinhomo_k, 'spinlumo_k':spinlumo_k,
                       'spingap':spingap, 'direct_spingap':direct_spingap,
                       'direct_spingap_k':direct_spingap_k}
        results.update(spinresults)
    return results
        
def gapdata_dos(energies, tdos, fermi):
    epsfracvec = FracVector.create(1,1000000)
    
    spins = len(tdos) 

    spinhomo = [None]*spins
    spinlumo = [None]*spins
    spingap = [None]*spins
    
    for spin in range(spins):
        for i in range(len(energies)):
            if energies[i] <= fermi-epsfracvec:
                if tdos[spin][i] > epsfracvec:
                    spinhomo[spin] = energies[i]
            else:
                if spinlumo[spin] == None and tdos[spin][i] > epsfracvec:
                    spinlumo[spin] = energies[i]
                    break
        spingap[spin] = spinlumo[spin]-spinhomo[spin]
    min_of_spingaps = min(spingap)
    homo=max(spinhomo)
    lumo=min(spinlumo)
    gap = lumo-homo
    
    results = {'gap':gap, 'homo':homo, 'lumo':lumo}
    if spins > 1:
        spinresults = {'spinhomo':spinhomo, 'spinlumo':spinlumo, 'spingap':spingap,
                       'min_of_spingaps':min_of_spingaps }
        results.update(spinresults)
    return results        


class PoscarReader():
    def __init__(self, ioa):
        self.ioa = IoAdapterFileReader.use(ioa)  
        self.parse()
        pass

    def parse(self):
        self.structure = poscar_to_structure(self.ioa)
        self.parsed = True


class KpointsReader():
    def __init__(self, ioa):
        self.ioa = IoAdapterFileReader.use(ioa)  
        self.parse()
        pass

    def parse(self):
        result = parse_kpoints(self.ioa)
        for k in result:
            setattr(self, k, result[k])
        for kline in self.klines:
            kline['from_rec']=FracVector.create(kline['from_rec'])
            kline['to_rec']=FracVector.create(kline['to_rec'])
            
        self.parsed = True


class DoscarReader():
    def __init__(self, ioa):
        self.ioa = IoAdapterFileReader.use(ioa)  
        self.parse()

    def parse(self):
        result = parse_doscar(self.ioa)
        for k in result:
            setattr(self, k, result[k])
        self.energies = FracVector.create(self.energies)
        self.tdos = FracVector.create(self.tdos)
        self.idos = FracVector.create(self.idos)
        self.parsed = True
    


class OutcarReader():
    def __init__(self, ioa, get_fermi=True, get_kpts_and_eigvals=True):
        self.ioa = IoAdapterFileReader.use(ioa)  

        self.get_fermi = get_fermi
        self.get_kpts_and_eigvals = get_kpts_and_eigvals
        
        self.parse()
        pass

    def parse(self):
        result = parse_outcar(self.ioa)
        for k in result:
            setattr(self, k, result[k])
        self.fermi = FracScalar.create(self.fermi)
        self.banddata = FracVector.create(self.banddata)
        self.kpts = FracVector.create(self.kpts)
        self.parsed = True
#    def parse(self):
#        results = {'final':False}
#        def set_final(results,match):
#            results['final']=True
#        def read_energy(results,match):
#            self.final_energy_with_entropy=match.group(1)
#            self.final_energy=match.group(2)
#        results = micro_pyawk(self.ioa,[
#             ["^ *energy *without *entropy= *([^ ]+) *energy\(sigma->0\) *= *([^ ]+) *$",None,read_energy],
#             ["FREE ENERGIE",None,set_final],
#             ],results,debug=False)
#        self.parsed = True
 
def read_outcar(ioa):
    return OutcarReader(ioa)

def read_poscar(ioa):
    return PoscarReader(ioa)
    
def read_doscar(ioa):
    return DoscarReader(ioa)

def read_kpoints(ioa):
    return KpointsReader(ioa)
    
    
