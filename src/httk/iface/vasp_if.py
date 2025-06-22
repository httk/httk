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

from __future__ import print_function

import os, shutil, math

import httk
from httk import config
from httk.core.template import apply_templates
from httk.atomistic.data import periodictable
from httk.core.ioadapters import cleveropen, IoAdapterFileReader
from httk.core import *
from httk.core.basic import mkdir_p, micro_pyawk
from httk.atomistic import Structure, Cell, PlaneWaveFunctions
from httk.atomistic.wavefunction import expand_gamma_coeffs, reduce_std_coeffs, gen_kgrid
from httk.atomistic.structureutils import cartesian_to_reduced

import struct

def get_pseudopotential(species, poscarspath=None):
    if poscarspath is None:
        try:
            poscarspath = config.get('paths', 'vasp_pseudolib')
        except Exception:
            #return [name for name in os.listdir(a_dir)
            #        if os.path.isdir(os.path.join(a_dir, name))]
            poscarspath = None

    if poscarspath is None and "VASP_PSEUDOLIB" in os.environ:
        poscarspath = os.environ['VASP_PSEUDOLIB']

    if poscarspath is None:
        raise Exception("httk.iface.vasp_if.get_pseudopotentials: No path given for where to find VASP pseudopotentials. \
                         Please either set vasp_pseudolib in httk.cfg, or define the VASP_PSEUDOLIB variable, or \
                         pass along a string in your code for the parameter 'poscarspath'")

    poscarspath = os.path.expanduser(poscarspath)

    for priority in ["_3", "_2", "_d", "_pv", "_sv", "", "_h", "_s"]:
        basepath = os.path.join(poscarspath, species)
        if os.path.exists(basepath+priority):
            try:
                f = cleveropen(os.path.join(basepath+priority, 'POTCAR'), 'r')
                data = f.read()
                f.close()
                return data
            except Exception:
                raise
                pass

    raise Exception("httk.iface.vasp_if.get_pseudopotentials: could not find a suitable pseudopotential for "+str(species))


def write_kpoints_file(fio, kpoints, comment=None, mp=True, gamma_centered=False):
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


def write_generic_kpoints_file(fio, comment=None, mp=True):
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
magions = ['Ag', 'Au', 'Cd', 'Ce', 'Co', 'Cr', 'Cu', 'Dy', 'Er', 'Eu', 'Fe', 'Gd', 'Hf', 'Hg', 'Ho', 'Ir', 'La', 'Lu', 'Mn', 'Mo', 'Nb', 'Nd', 'Ni', 'Os', 'Pa', 'Pd', 'Pm', 'Pr', 'Pt', 'Re', 'Rh', 'Ru', 'Sc', 'Sm', 'Ta', 'Tb', 'Tc', 'Th', 'Ti', 'Tm', 'U', 'V', 'W', 'Y', 'Yb', 'Zn', 'Zr']
dualmag = {'O': ['Co'], 'S': ['Mn', 'Fe', 'Cr', 'Co']}


def is_dualmagnetic(ion, ionlist):
    for i in range(len(ionlist)):
        if ionlist[i] in dualmag:
            if ion in dualmag[ionlist[i]]:
                return True
    return False


def magnetization_recurse(basemags, dualmags, high, low):
    if len(dualmags) == 0:
        return [basemags]

    index = dualmags.pop()
    basemags[index] = high
    hi_list = magnetization_recurse(list(basemags), list(dualmags), high, low)
    basemags[index] = low
    low_list = magnetization_recurse(list(basemags), list(dualmags), high, low)

    return hi_list + low_list


def get_magnetizations(ionlist, high, low):
    basemags = []
    dualmags = []
    for i in range(len(ionlist)):
        if is_dualmagnetic(ionlist[i], ionlist):
            basemags.append(None)
            dualmags.append(i)
        else:
            if ionlist[i] in magions:
                basemags.append(high)
            else:
                basemags.append(low)

    return magnetization_recurse(basemags, dualmags, high, low)


def copy_template(dirtemplate, dirname, templatename):
    template = os.path.join(dirname, "ht.template."+templatename)
    if os.path.exists(template):
        raise Exception("Template dir already exists.")
    shutil.copytree(dirtemplate, template, True)


def poscar_to_strs(fio, included_decimals=''):
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

    cell = [['', '', ''], ['', '', ''], ['', '', '']]
    for i in [0, 1, 2]:
        cellline = next(fi).strip().split()
        for j, v in enumerate(cellline):
            cell[i][j] = v

    symbols_or_count = next(fi).strip().split()

    try:
        counts = list(map(int, symbols_or_count))
        symbols = None
        occupations = range(-1, -len(counts)-1, -1)
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
    if included_decimals == '':
        for i in range(N):
            nxt = next(fi)
            strcoord = nxt.strip().split()[:3]
            coord = list(map(lambda x: x.strip(), strcoord))
            coords.append(coord)
    else:
        for i in range(N):
            nxt = next(fi)
            strcoord = nxt.strip().split()[:3]
            tempcoord = list(map(lambda x: x.strip(), strcoord))
            coord = list(map(lambda x: x[0:2+included_decimals], tempcoord))
            coords.append(coord)

    return (cell, scale, vol, coords, coords_reduced, counts, occupations, comment)

def poscar_to_structure(f, included_decimals='', structure_class=Structure):
    cell, scale, volume, coords, coords_reduced, counts, occupations, comment = poscar_to_strs(f, included_decimals)

    frac_cell = FracVector.create(cell, simplify=True)
    counts = [int(x) for x in counts]

    if coords_reduced:
        frac_coords = cartesian_to_reduced(cell, coords)
    else:
        frac_coords = FracVector.create(coords, simplify=True)

    if volume is not None:
        volume = FracScalar.create(volume)

    if scale is not None:
        scale = FracScalar.create(scale)

    newoccupations = []
    for occupation in occupations:
        newoccupations.append(periodictable.atomic_number(occupation))

    struct = structure_class.create(uc_basis=frac_cell, uc_volume=volume, uc_scale=scale,
            uc_reduced_coords=frac_coords, uc_counts=counts,
            assignments=newoccupations, tags={'comment': comment}, periodicity=0)

    return struct


def write_poscar(fio, cell, coords, coords_reduced, counts, occupations, comment="Comment", scale="1", vol=None):
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
    if vol is not None:
        f.write("-"+str(vol)+"\n")
    else:
        f.write(str(scale)+"\n")
    for c1, c2, c3 in cell:
        f.write(str(c1)+" "+str(c2)+" "+str(c3)+"\n")

    for i in range(len(counts)):
        if occupations is None:
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
    tags = struct.get_tags().values()
    if len(tags) > 0:
        tagstr = " tags: " + ", ".join([tag.tag+":"+tag.value for tag in tags])
    else:
        tagstr = ""
    if struct.has_rc_repr and struct.has_uc_repr:
        return struct.formula + " " + struct.hexhash + tagstr
    else:
        return struct.formula + " " + tagstr


def structure_to_poscar(f, struct, fix_negative_determinant=False, comment=None, primitive_cell=True):
    if comment is None:
        comment = structure_to_comment(struct)
    if primitive_cell:
        basis = struct.pc.uc_basis
        coords = struct.pc.uc_reduced_coords
        vol = struct.pc.uc_volume
        counts = struct.pc.uc_counts
    else:
        #basis = struct.cc.uc_basis
        #coords = struct.cc.uc_reduced_coords
        #vol = struct.cc.uc_volume
        #counts = struct.cc.uc_counts
        basis = struct.uc_basis
        coords = struct.uc_reduced_coords
        vol = struct.uc_volume
        counts = struct.uc_counts

    if basis.det() < 0:
        if fix_negative_determinant:
            basis = -basis
            coords = (-coords).normalize()

    write_poscar(f, basis.to_strings(), coords.to_strings(), True, counts, struct.symbols, comment, vol=vol.to_string())


def calculate_kpoints(struct, dens=20):
    #local KPTSLINE=$(awk -v "LVAL=$LVAL" -v"equalkpts=$EQUAL_KPTS" -v"bumpkpts=$BUMP_KPTS" '
    basis = struct.uc_basis

    celldet = basis.det()
    cellvol = abs(celldet)

    if cellvol == 0:
        raise Exception("vasp_if.calculate_kpoints: Error in VASP_KPOINTSLINE: singular cell vectors. POSCAR is broken.")

    recip = basis.reciprocal().simplify()
    half = 0.5
    N1 = int(math.ceil(math.sqrt(recip[0].lengthsqr())*dens+half)+0.1)
    N2 = int(math.ceil(math.sqrt(recip[1].lengthsqr())*dens+half)+0.1)
    N3 = int(math.ceil(math.sqrt(recip[2].lengthsqr())*dens+half)+0.1)
    return max(1, N1), max(1, N2), max(1, N3)


def prepare_single_run(dirpath, struct, poscarspath=None, template='t:/vasp/single/static', overwrite=False):
    if overwrite:
        mkdir_p(dirpath)
    else:
        os.mkdir(dirpath)
    structure_to_poscar(os.path.join(dirpath, "POSCAR"), struct, fix_negative_determinant=True)
    #write_generic_kpoints_file(os.path.join(dirpath,"KPOINTS"),comment=structure_to_comment(struct))
    kpoints = calculate_kpoints(struct)
    write_kpoints_file(os.path.join(dirpath, "KPOINTS"), kpoints, comment=structure_to_comment(struct))
    ioa = IoAdapterFileWriter.use(os.path.join(dirpath, "POTCAR"))
    f = ioa.file
    spieces_counts = []
    magmomlist = get_magnetizations(struct.symbols, 5, 1)
    magmom_per_ion = magmomlist[0]
    magmoms = []
    nelect = 0
    natoms = 0
    nmag = 0
    for i in range(len(struct.assignments)):
        assignment = struct.assignments[i]
        count = struct.uc_counts[i]
        symbol = periodictable.atomic_symbol(assignment.symbol)
        pp = get_pseudopotential(symbol, poscarspath)
        f.write(pp)
        spieces_counts.append(count)
        #magmoms.append(str(count)+"*"+str(get_magmom(symbol)))
        magmom = magmom_per_ion[i]
        magmoms.append(str(count)+"*"+str(magmom))

        def zval(results, match):
            results['zval'] = float(match.group(1))
        results = micro_pyawk(IoAdapterString(pp), [["^ *POMASS.*; *ZVAL *= *([^ ]+)", None, zval]])
        if not 'zval' in results:
            raise Exception("vasp_if.prepare_simple_static_run: Could not read ZVAL from potcar file")
        nelect += results['zval']*count
        natoms += count
        nmag += count*magmom

    ioa.close()
    nbands1 = int(0.6*nelect + 1.0)+int(math.ceil(natoms/2.0)+0.1)
    nbands2 = int(0.6*nelect + 1.0)+int(math.ceil(nmag/2.0)+0.1)
    nbands3 = int(0.6*nelect + 1.0)+20
    nbands_spin = max(1, nbands1, nbands2, nbands3)
    nbands_spin += nbands_spin % 2
    nbands1 = int(nelect/2.0 + 2)+int(math.ceil(natoms/2.0)+0.1)
    nbands2 = int(math.ceil(nelect/2.0)+20+0.1)
    nbands_nospin = max(1, nbands1, nbands2)
    nbands_nospin += nbands_spin % 2

    data = {}
    data['VASP_SPIECES_COUNTS'] = " ".join(list(map(str, spieces_counts)))
    data['VASP_MAGMOM'] = " ".join(list(map(str, magmoms)))
    data['VASP_NBANDS_SPIN'] = str(nbands_spin)
    data['VASP_NBANDS_NOSPIN'] = str(nbands_nospin)

    if template.startswith('t:'):
        template = os.path.join(httk.httk_root, 'Execution', 'tasks-templates', template[2:])

    apply_templates(template, dirpath, envglobals=data, mkdir=False)


def read_wavecar(file, gamma_mode='x', wavefunc_prec = None):
    """
    Reads the information in a VASP WAVECAR file into a PlaneWaveFunctions object.

    Input
    file: File-like object or io adapter pointing to WAVECAR file
    gamma_mode: Reduction axis in the gamma-point format

    Return
    PlaneWaveObject acting as proxy for the WAVECAR file

    """
    import numpy as np
    file = IoAdapterFilename.use(file)
    filename = file.filename
    file = httk.core.ioadapters.cleveropen(filename, "rb") # make sure to open in byte-mode

    record_len, nspin, rtag, _ = map(int, struct.unpack('d'*4, file.read(8*4)))

    # determine complex number precision from rtag
    if wavefunc_prec is None:
        if rtag == 45200:
            float_size = 4 # single precision
        elif rtag == 45210:
            float_size = 8 # double precision
        else:
            raise ValueError("Unknown RTAG value in WAVECAR. Perhaps unsupported version of VASP was used. Specify floating point precision using wavefunc_prec (= {64,128})")
    else:
        float_size = wavefunc_prec//16

    file.seek(record_len) # move to second record
    header = struct.unpack('d'*12, file.read(8*12))

    nkpts = int(header[0])
    nbands = int(header[1])
    encut = header[2]
    cell_nums = header[3:]
    cell = Cell.create(basis=[[cell_nums[3*j + i] for i in range(3)] for j in range(3)])

    # define function for seeking specific record in WAVECAR
    def rec_pos(spin, kpt, band, record_length = record_len):
        assert 1 <= spin <= nspin, "Spin index {} out of range [1,{}]".format(spin, nspin)
        assert 1 <= kpt <= nkpts, "K-point index {} out of range [1,{}]".format(kpt, nkpts)
        assert 1 <= band <= nbands, "Band index {} out of range [1,{}]".format(band, nbands)

        # return position at the first plane-wave coefficient:
        #### two header records
        #### for s in spin:
        ####    for k in kpts:
        ####        header records with k-point planewave metadata eigenvalues and occupations
        ####        for b in bands:
        ####            coeffs <--- Record position goes at start of this record
        return (2 + (spin - 1) * nkpts * (nbands+1) + (kpt - 1) * (nbands + 1) + band) * record_length

    ### Read occupations and eigenvalues
    eigs = np.zeros((nspin,nkpts,nbands))
    occups = np.zeros((nspin,nkpts,nbands))
    nplw_coeffs = [0]*nkpts
    kpts = [0]*nkpts
    for spin in range(nspin):
        for kpt in range(nkpts):
            seek_pos = rec_pos(spin+1, kpt+1, 1) - record_len # position of spin-kpt header
            file.seek(seek_pos)
            nentries = (4+3*nbands)
            buffer = file.read(8*nentries)
            record = struct.unpack('d'*nentries, buffer)
            if spin == 0:
                # read kpt header info
                nplw_coeffs[kpt] = int(record[0])
                kpts[kpt] = record[1:4]
            eigs[spin, kpt, :] = record[4::3]
            occups[spin, kpt, :] = record[4+2::3]

    wavefuncs = PlaneWaveFunctions.create(file_wrapper=file, encut=encut, cell=cell, kpts=kpts, eigs=eigs, occups=occups, rec_pos_func=rec_pos, double_precision=(float_size == 8), nplws=nplw_coeffs)
    return wavefuncs

def write_wavecar(file_wrapper, planewaves, bands=None, spins=None, ikpts=None, format=None, gamma_half="x", keep_records=False):
    """
    Writes a PlaneWaveFunctions object to specified file.

    Optional arguments are for writing a subset of the plane-wave object, limiting the new file to certain spin-components, k-points or bands. Writing to gamma format or standard format can be specified, when possible.

    Input
    file_wrapper: Filename or file object to new file (will be closed and opened in binary read mode if necessary)
    planewaves: PlaneWaveFunctions object to copy to file
    spins: Indices of spin components to write, default is all, counting from 1
    ikpts: Indices of k-points to write, default is all, counting from 1
    bands: Indices of bands to write, default is all, counting from 1
    format: Output format. Either 'std' or 'gamma', default is same format as planewaves object
    gamma_half: If writing to gamma format, change the axis of reduction, either 'z' or 'x'
    keep_records: If True, the coefficients will be written while keeping their positions in the binary file.
                If only selection of coeffs are to be written, all other coefficients will be set to zero.
    """

    import numpy as np # import numpy for faster routines when writing data

    ### Sanitize arguments
    if not isinstance(planewaves, PlaneWaveFunctions):
        return None

    if keep_records:
        band_to_keep = np.ones(planewaves._nbands, dtype=bool)
        spin_to_keep = np.ones(planewaves._nspins, dtype=bool)
        kpt_to_keep = np.ones(planewaves._nkpts, dtype=bool)
        if bands is not None:
            band_to_keep.fill(False)
            band_to_keep[np.array(bands)-1] = True
        if spins is not None:
            spin_to_keep.fill(False)
            spin_to_keep[np.array(spins)-1] = True
        if ikpts is not None:
            kpt_to_keep.fill(False)
            kpt_to_keep[np.array(ikpts)-1] = True

    if bands is None or keep_records:
        bands = np.arange(1, planewaves._nbands+1)
    else:
        bands = np.array(bands)
    if spins is None or keep_records:
        spins = np.arange(1, planewaves._nspins+1)
    else:
        spins = np.array(spins)
    if ikpts is None or keep_records:
        ikpts = np.arange(1, planewaves._nkpts+1)
    else:
        ikpts = np.array(ikpts)

    assert 1 <= min(spins) and max(spins) <= planewaves._nspins
    assert 1 <= min(ikpts) and max(ikpts) <= planewaves._nkpts
    assert 1 <= min(bands) and max(bands) <= planewaves._nbands

    ### Determine conversion settings based on provided format and wavefunctions

    if format == 'gamma' or format == "gam":
        assert len(ikpts) == 1 and np.allclose(planewaves.kpts[ikpts[0] - 1], np.array([0,0,0])), "Can only write gamma-wavecar at the gamma-point, several k-points or non-gamma point provided"
        to_gamma = True
    elif format == 'std':
        to_gamma = False
    else:
        to_gamma = planewaves._is_gamma

    if to_gamma != planewaves._is_gamma:
        convert = True
        if to_gamma:
            gam_half = gamma_half if gamma_half else "x"
        else:
            gam_half = planewaves._gamma_half
    else:
        convert = False

    # open file for writing
    filename = IoAdapterFilename.use(file_wrapper)
    file_wrapper = cleveropen(filename.filename, 'wb')


    ### Write header
    if not planewaves.double_precision:
        rtag = 45200 # Double-precision vasp tag
        data_size = 8
        data_id = np.complex64
    else:
        rtag = 45210 # Single-precision vasp tag
        data_size = 16
        data_id = np.complex128

    nkpts = len(ikpts)
    nbands = len(bands)
    nspins = len(spins)
    nplws = planewaves._nplws[ikpts-1]
    max_nplws = max(planewaves._nplws)

    ### Determine variable sizes based on desired conversion
    if convert:
        if to_gamma:
            nplws = [(nplw - 1)//2 + 1 for nplw in nplws]
            max_nplws = max(nplws)
        else:
            nplws = [2*nplw - 1 for nplw in nplws]
            max_nplws = max(nplws)
    ## Record should hold at least all wavefunctions and all band+header data
    record_size = int(max(max_nplws*data_size, (4+nbands*3)*8))
    nfloats = record_size // 8
    ncomplex = record_size // data_size
    float_rec = np.zeros(nfloats, dtype=np.float64)
    complex_rec = np.zeros(ncomplex, dtype=data_id)

    # top header
    float_rec[:3] = [record_size, nspins, rtag]
    float_rec.tofile(file_wrapper)

    # second header
    cell_nums = [planewaves.cell.basis[i,j].to_float() for i in range(3) for j in range(3)]
    float_rec[:12] = [nkpts, nbands, planewaves._encut.to_float()] + cell_nums
    float_rec.tofile(file_wrapper)

    ### Write wavefunctions and wavefunction headers
    if convert:
        ## generate k-grid for G-vectors
        if to_gamma:
            gam_half = gamma_half if gamma_half else "x"
        else:
            gam_half = planewaves._gamma_half
        gam_kgrid = gen_kgrid(planewaves.kgrid_size, gamma=True, gamma_half=gam_half)
        std_kgrid = gen_kgrid(planewaves.kgrid_size, gamma=False)

    for s in spins:
        for ki, k in enumerate(ikpts):
            ## generate G-vectors for wavefunction conversion
            if convert:
                gam_gvecs = planewaves.get_gvecs(kpt=planewaves.kpts[k-1], kgrid=gam_kgrid)
                std_gvecs = planewaves.get_gvecs(kpt=planewaves.kpts[k-1], kgrid=std_kgrid)
                nx, ny, nz = [np.max(std_gvecs[:,i]) - np.min(std_gvecs[:,i]) for i in range(3)]
                wave_buffer = np.zeros((nx, ny, nz), dtype=np.complex128)


            float_rec = np.zeros(record_size//8, dtype=np.float64)
            nwaves = nplws[ki]
            # write nplws, k-point, eigenvalues and occupations
            float_rec[0] = nwaves
            float_rec[1:4] = planewaves.kpts[k-1][:]
            float_rec[4:4+len(bands)*3:3] = [planewaves.eigenval(s,k,b) for b in bands]
            float_rec[4+2:4+2+len(bands)*3:3] = [planewaves.occupation(s,k,b) for b in bands]
            float_rec.tofile(file_wrapper)

            for b in bands:
                if keep_records and (not band_to_keep[b-1] or not spin_to_keep[s-1] or not kpt_to_keep[ki-1]):
                    coeffs = np.zeros(record_size, dtype=data_id)
                else:
                    coeffs = planewaves.get_plws(s,k,b, cache=False)
                if convert:
                    if to_gamma:
                        coeffs = reduce_std_coeffs(coeffs, planewaves.kgrid_size, std_gvecs, gam_gvecs, gamma_half)
                    else:
                        coeffs = expand_gamma_coeffs(coeffs, std_gvecs, gam_gvecs, buffer=wave_buffer)

                complex_rec[:nwaves] = coeffs
                complex_rec[nwaves:] = 0j
                complex_rec.tofile(file_wrapper)
    file_wrapper.close()

def save_vesta(filename, structure, isosurface, cols=10):
    filename = IoAdapterFilename.use(filename).filename
    for ext_i, ext in enumerate(["_r.vasp", "_i.vasp"]):
        ext_name = filename + ext
        f = IoAdapterFileWriter.use(ext_name).file
        structure_to_poscar(f, structure, primitive_cell=False)

        iso = isosurface.copy().flatten(order='F')
        if ext_i == 0:
            iso = iso.real
        else:
            iso = iso.imag
        shape = isosurface.shape
        print("\n{} {} {}".format(*shape), file=f)
        remainder = iso.size % cols
        rows = iso.size // cols
        fmt = "%16.8E"

        row_s = [0]*(rows + int(remainder != 0))
        for i in range(rows):
            row_s[i] = ' '.join([fmt % v for v in iso[i*cols:(i+1)*cols]])
        if remainder != 0:
            row_s[i+1] = ' '.join(map(str, iso[-remainder:]))
        print("\n".join(row_s) + "\n", file=f)
        f.close()




class OutcarReader():

    def __init__(self, ioa):
        self.ioa = ioa
        self.parse()
        pass

    def parse(self):
        results = {'final': False}

        def set_final(results, match):
            results['final'] = True

        def read_energy(results, match):
            self.final_energy_with_entropy = match.group(1)
            self.final_energy = match.group(2)

        def read_stress_tensor(results, match):
            # NOTE: Stress tensor values are in a different order in OUTCAR
            # compared to Voigt notation. In terms of Voigt notation OUTCAR
            # stress tensor is ordered as:
            # 1 2 3 6 4 5
            # The unit is kB = 0.1 GPa.
            # Also, OUTCAR gives the stress tensor with a minus sign.
            self.stress_tensor = [match.group(1), match.group(2),
                                  match.group(3), match.group(4),
                                  match.group(5), match.group(6)]
            # Due to these VASP conventions, provide also the stress tensor
            # in the normal Voigt order and in units of GPa:
            self.stress_tensor_voigt_gpa = [
                str(round(-float(self.stress_tensor[0])/10, 5)),
                str(round(-float(self.stress_tensor[1])/10, 5)),
                str(round(-float(self.stress_tensor[2])/10, 5)),
                str(round(-float(self.stress_tensor[4])/10, 5)),
                str(round(-float(self.stress_tensor[5])/10, 5)),
                str(round(-float(self.stress_tensor[3])/10, 5)),
                ]

        results = micro_pyawk(self.ioa, [
                              [r"^ *energy *without *entropy= *([^ ]+) "+
                               r"*energy\(sigma->0\) *= *([^ ]+) *$", None, read_energy],
                              ["FREE ENERGIE", None, set_final],
                              # ["^ *in kB" + " *([^ \n]+)"*6, None, read_stress_tensor]
                              ], results, debug=False)
        self.parsed = True


def read_outcar(ioa):
    return OutcarReader(ioa)


def get_dist_matrix(array):
    from httk.external.numpy_ext import numpy as np
    return np.array([
        [1+array[0], array[5]/2, array[4]/2],
        [array[5]/2, 1+array[1], array[3]/2],
        [array[4]/2, array[3]/2, 1+array[2]]
    ])


def distort(dist_mat, mat):
    """Apply distortion matrix"""
    from httk.external.numpy_ext import numpy as np

    array = np.array(mat)
    for i in range(len(mat)):
        array[i, :] = np.array([np.sum(dist_mat[0, :]*mat[i, :]),
                                np.sum(dist_mat[1, :]*mat[i, :]),
                                np.sum(dist_mat[2, :]*mat[i, :])])
    return array


def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.

    :param axis:
    :type axis:
    :param theta:
    :type theta:
    """
    from httk.external.numpy_ext import numpy as np

    axis = np.asarray(axis)
    theta = np.asarray(theta)
    axis = axis/np.linalg.norm(axis)
    a = np.cos(theta/2.0)
    b, c, d = -axis*np.sin(theta/2.0)
    aa, bb, cc, dd = a*a, b*b, c*c, d*d
    bc, ad, ac, ab, bd, cd = b*c, a*d, a*c, a*b, b*d, c*d
    return np.array([[aa+bb-cc-dd, 2*(bc+ad), 2*(bd-ac)],
                     [2*(bc-ad), aa+cc-bb-dd, 2*(cd+ab)],
                     [2*(bd+ac), 2*(cd-ab), aa+dd-bb-cc]])


def apply_dist(ELASTICSTEP, DELTASTEP, sym, deltas, distortions):
    from httk.external.numpy_ext import numpy as np
    from httk.external import pymatgen_glue
    from pymatgen.core import Structure as pmg_Structure
    from pymatgen.io.vasp import Poscar as pmg_Poscar
    from pymatgen.core.lattice import Lattice as pmg_Lattice

    dist_ind = ELASTICSTEP - 1
    delta_ind = DELTASTEP - 1
    d = deltas[dist_ind][delta_ind]

    # epsilon_array is the distortion in Voigt notation
    epsilon_array = np.array(distortions[dist_ind]) * d
    dist_matrix = get_dist_matrix(epsilon_array)

    struct = pmg_Structure.from_file("POSCAR")
    struct.lattice = pmg_Lattice(distort(dist_matrix, struct._lattice.matrix))

    poscar = pmg_Poscar(struct)
    poscar.write_file("POSCAR", significant_figures=8)


def elastic_config(fn):
    from httk.external.numpy_ext import numpy as np

    config = configparser.ConfigParser()
    config.read(fn)
    # The type of symmetry
    try:
        sym = config.get("elastic", "symmetry").lstrip()
    except:
        sym = "cubic"

    # Use projection technique, i.e. to obtain cubic elastic
    # constants for non-cubic crystals, such as SQS supercells.
    try:
        project = eval(config.get("elastic", "projection"))
    except:
        project = False

    # Delta values:
    tmp = config.get("elastic", "delta").lstrip().split("\n")
    deltas = []
    for line in tmp:
        line = line.split()
        deltas.append([float(x) for x in line])

    # Distortions in Voigt notation:
    distortions = []
    tmp = config.get("elastic", "distortions").lstrip().split("\n")
    for line in tmp:
        line = line.split()
        distortions.append([float(x) for x in line])

    # Generate the additional distortions, if projection is used:
    # For cubic systems, the projected elastic constants are
    # an average of elastic constants calculated along the different
    # permutations of the xyz-axes: xyz -> yzx -> zxy.
    # In terms of Voigt notation, the additional distortions along the two
    # other axes are:
    # 1 2 3 4 5 6 -> 2 3 1 5 6 4 (xyz -> yzx),
    # 1 2 3 4 5 6 -> 3 1 2 6 4 5 (xyz -> zxy).
    # Also, check if the new distortion was already included in the set of
    # distortions.
    if project:
        if sym == "cubic":
            new_distortions = []
            new_deltas = []
            for d, delta in zip(distortions, deltas):
                new_distortions.append(d)
                new_deltas.append(delta)
                xyz_to_yzx = [d[1], d[2], d[0], d[4], d[5], d[3]]
                xyz_to_zxy = [d[2], d[0], d[1], d[5], d[3], d[4]]
                for new_d in (xyz_to_yzx, xyz_to_zxy):
                    include_new_d = True
                    for dd in distortions:
                        if np.allclose(dd, new_d):
                            include_new_d = False
                            break
                    if include_new_d:
                        new_distortions.append(new_d)
                        new_deltas.append(delta)
        else:
            raise NotImplementedError("Projection technique only implemented for cubic systems!")

        distortions = new_distortions
        deltas = new_deltas

    return sym, deltas, distortions, project


def get_elastic_constants(path, settings_path=".."):
    from httk.external.numpy_ext import numpy as np

    elastic_config_file = os.path.join(path, settings_path, "settings.elastic")
    if not os.path.exists(elastic_config_file):
        sys.exit("File {} can not be found!".format(elastic_config_file))
    else:
        sym, delta, distortions, project = elastic_config(elastic_config_file)

    stress_target = []
    epsilon = []
    for i, dist in enumerate(distortions):
        for j, d in enumerate(delta[i]):
            # Collect stress components:
            # outcar = read_outcar(os.path.join(path,
                # 'OUTCAR.cleaned.elastic{}_{}'.format(i+1, j+1)))
            ioa = IoAdapterFileReader.use(os.path.join(path,
                'OUTCAR.cleaned.elastic{}_{}'.format(i+1, j+1)))
            file_lines = ioa.file.read()
            # If atoms were relaxed, there might be multiple "in kB"
            # lines. Use re.findall to get them all and then just take
            # the last match.
            matches = re.findall("in kB" + "\s*([^ \n]+)"*6, file_lines)

            # NOTE: Stress tensor values are in a different order in OUTCAR
            # compared to Voigt notation. In terms of Voigt notation OUTCAR
            # stress tensor is ordered as:
            # 1 2 3 6 4 5
            # The unit is kB = 0.1 GPa.
            # Also, OUTCAR gives the stress tensor with a minus sign.
            try:
                stress_tensor = matches[-1]
                # Due to these VASP conventions, provide also the stress tensor
                # in the normal Voigt order and in units of GPa:
                stress_tensor_voigt_gpa = [
                    str(np.round(-float(stress_tensor[0])/10, 5)),
                    str(np.round(-float(stress_tensor[1])/10, 5)),
                    str(np.round(-float(stress_tensor[2])/10, 5)),
                    str(np.round(-float(stress_tensor[4])/10, 5)),
                    str(np.round(-float(stress_tensor[5])/10, 5)),
                    str(np.round(-float(stress_tensor[3])/10, 5)),
                    ]

                # st = outcar.stress_tensor_voigt_gpa
                st = stress_tensor_voigt_gpa

                eps = np.array(dist) * d
                epsilon.append(eps)
                tmp = []
                for val in st:
                    tmp.append(float(val))
                stress_target.append(tmp)

            except:
                continue

    epsilon = np.array(epsilon)
    stress_target = np.array(stress_target)

    def get_full_C_vector(C, sym="cubic"):
        if sym == "cubic":
            full_C = np.array([C[0], C[0], C[0], C[1], C[1], C[1],
                C[2], C[2], C[2], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            ])

        elif sym == "hexagonal":
            full_C = np.array([C[0], C[0], C[1], C[2], C[2], C[3], C[4],
                C[4], (C[0]-C[3])/2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            ])

        else:
            sys.exit("{}(): ".format(inspect.currentframe().f_code.co_name) +
                "Full cij matrix not implemented for sym = \"{}\"!".format(sym))

        return full_C

    def get_full_cij_matrix(cij):
        """Construct the full elastic matrix from the C-vector
        as defined in Tasnadi PRB (2012)
        """
        return np.array([
            [cij[ 0], cij[ 5], cij[ 4], cij[ 9], cij[13], cij[17]],
            [cij[ 5], cij[ 1], cij[ 3], cij[15], cij[10], cij[14]],
            [cij[ 4], cij[ 3], cij[ 2], cij[12], cij[16], cij[11]],
            [cij[ 9], cij[15], cij[12], cij[ 6], cij[20], cij[19]],
            [cij[13], cij[10], cij[16], cij[20], cij[ 7], cij[18]],
            [cij[17], cij[14], cij[11], cij[19], cij[18], cij[ 8]]
            ])

    def setup_linear_system(epsilon, stress_target, sym="cubic"):
        """Create matrices A and B for a over-determined linear system
        A @ cij = B, where A=epsilon and B=stress_target.
        This system can then be solved by np.linalg.lstsq to obtain
        the symmetry-wise non-zero elastic constants cij.

        Perform a check for the rank of the linear system coefficient matrix,
        because depending on whether we have under-, well- or over-determined
        linear system, the solution strategy should be a little different
        for each of these cases:
            1) Well- and over-determined systems can be solved normally.
            2) Under-determined system means that we have to apply symmetry
               to eliminate some of the cij variables from the linear system
               in order to make the linear system solvable (well- or over-
               determined).
        """

        cij_len = 21
        full_cij_index = [
            [  0,  5,  4,  9, 13, 17],
            [  5,  1,  3, 15, 10, 14],
            [  4,  3,  2, 12, 16, 11],
            [  9, 15, 12,  6, 20, 19],
            [ 13, 10, 16, 20,  7, 18],
            [ 17, 14, 11, 19, 18,  8]
        ]

        A = []
        B = []
        for eq_ind in range(epsilon.shape[0]):
            for j in range(6):
                epsilon_tmp = np.zeros(cij_len)
                for i in range(6):
                    index = full_cij_index[i][j]
                    if index is None:
                        continue
                    elif isinstance(index, int):
                        epsilon_tmp[index] += epsilon[eq_ind,i]
                    elif isinstance(index, dict):
                        for key, val in index.items():
                            epsilon_tmp[key] += val * epsilon[eq_ind,i]

                A.append(epsilon_tmp)
                B.append([stress_target[eq_ind,j]])

        A = np.array(A)
        B = np.array(B)

        Arank = np.linalg.matrix_rank(A)
        # There are enough independent equations to solve all variables:
        if Arank >= cij_len:
            symmetry_reduction = False
            return A, B, symmetry_reduction

        else:
            symmetry_reduction = True
            # Symmetry based elimination of variables required:
            if sym == "cubic":
                cij_len = 3
                full_cij_index = [
                    [   0,    1,    1, None, None, None],
                    [   1,    0,    1, None, None, None],
                    [   1,    1,    0, None, None, None],
                    [None, None, None,    2, None, None],
                    [None, None, None, None,    2, None],
                    [None, None, None, None, None,    2]
                ]

            elif sym == "hexagonal":
                cij_len = 5
                full_cij_index = [
                    [   0,    3,    2, None, None, None],
                    [   3,    0,    2, None, None, None],
                    [   2,    2,    1, None, None, None],
                    [None, None, None,    4, None, None],
                    [None, None, None, None,    4, None],
                    [None, None, None, None, None, {0: 0.5, 1:-0.5}]
                ]

            else:
                sys.exit("{}(): ".format(inspect.currentframe().f_code.co_name) +
                    "Symmetry reduction not implemented for sym = \"{}\"!".format(sym))

            A = []
            B = []
            for eq_ind in range(epsilon.shape[0]):
                for j in range(6):
                    epsilon_tmp = np.zeros(cij_len)
                    for i in range(6):
                        index = full_cij_index[i][j]
                        if index is None:
                            continue
                        elif isinstance(index, int):
                            epsilon_tmp[index] += epsilon[eq_ind,i]
                        elif isinstance(index, dict):
                            for key, val in index.items():
                                epsilon_tmp[key] += val * epsilon[eq_ind,i]

                    A.append(epsilon_tmp)
                    B.append([stress_target[eq_ind,j]])

            A = np.array(A)
            B = np.array(B)
            return A, B, symmetry_reduction

    def get_symmetrized_C_vector(C, sym="cubic"):
        """We follow the notation of Tasnadi2012, PRB 85, 144112
           and Refs [31], [32] of that paper."""

        if sym == "cubic":
            Psym = np.zeros((21,21))
            Psym[0:3,0:3] = 1./3
            Psym[3:6,3:6] = 1./3
            Psym[6:9,6:9] = 1./3

        elif sym == "hexagonal":
            Psym = np.zeros((21,21))
            Psym[0:2, 0:2] = 3./8
            Psym[0:2,5] = 1./(4*np.sqrt(2))
            Psym[0:2,8] = 1./4
            Psym[2,2] = 1.0
            Psym[3:5,3:5] = 1./2
            Psym[5,0:2] = 1./(4*np.sqrt(2))
            Psym[5,5] = 3./4
            Psym[5,8] = -1/(2*np.sqrt(2))
            Psym[6:8,6:8] = 1./2
            Psym[8,0:2] = 1./4
            Psym[8,5] = -1/(2*np.sqrt(2))
            Psym[8,8] = 1./2

        else:
            sys.exit("{}(): ".format(inspect.currentframe().f_code.co_name) +
            "Symmetrized cij matrix not implemented for sym = \"{}\"!".format(sym))

        # Include the normalization factors, because Psym matrix
        # in get_symmetrized_C_vector includes them:
        sq2 = np.sqrt(2.0)
        norm_factors = np.array([1, 1, 1, sq2, sq2, sq2, 2, 2, 2, 2,
            2, 2, 2, 2, 2, 2, 2, 2, 2*sq2, 2*sq2, 2*sq2])

        Csym = np.dot(Psym, C*norm_factors) / norm_factors
        return Csym

    A, B, symmetry_reduction = setup_linear_system(epsilon,
            stress_target, sym)
    # Solve the 21-component C-vector Tasnadi2012, PRB 85, 144112
    try:
        Cvector_nosym, residuals, rank, singular_values = np.linalg.lstsq(A,
            B, rcond=None)
    except:
        Cvector_nosym = np.zeros(21)
    Cvector_nosym = Cvector_nosym.flatten()

    if symmetry_reduction:
        Cvector_nosym = get_full_C_vector(Cvector_nosym, sym)

    # Symmetrize based on the symmetry that the user has defined
    # in settings.elastic:
    Cvector = get_symmetrized_C_vector(Cvector_nosym, sym)

    cij = np.array(get_full_cij_matrix(Cvector))
    cij_nosym = np.array(get_full_cij_matrix(Cvector_nosym))

    # Compute compliance tensor, which is the matrix inverse of cij
    try:
        sij = np.linalg.inv(cij)
    except:
        sij = np.zeros_like(cij)

    elas_dict = {}
    # Compute bulk and shear moduli
    # Voigt
    K_V = (cij[0,0] + cij[1,1] + cij[2,2] + 2*(cij[0,1] + cij[1,2] + cij[2,0])) / 9.
    G_V = (cij[0,0] + cij[1,1] + cij[2,2] - (cij[0,1] + cij[1,2] + cij[2,0])
          + 3*(cij[3,3] + cij[4,4] + cij[5,5]))/15.
    elas_dict['K_V'] = K_V
    elas_dict['G_V'] = G_V

    # Reuss
    K_R = 1. / (sij[0,0] + sij[1,1] + sij[2,2] + 2*(sij[0,1] + sij[1,2] + sij[2,0]))
    G_R = 15. / (4*(sij[0,0] + sij[1,1] + sij[2,2]) -
                4*(sij[0,1] + sij[1,2] + sij[2,0]) +
                3*(sij[3,3] + sij[4,4] + sij[5,5]))
    elas_dict['K_R'] = G_R
    elas_dict['G_R'] = G_R

    # Hill
    K_VRH = (K_V + K_R)/2
    G_VRH = (G_V + G_R)/2
    elas_dict['K_VRH'] = K_VRH
    elas_dict['G_VRH'] = G_VRH

    # Poisson ratio and Young modulus
    mu_VRH = (3*K_VRH - 2*G_VRH) / (6*K_VRH + 2*G_VRH)
    E_VRH = 2*G_VRH * (1 + mu_VRH)
    elas_dict['mu_VRH'] = mu_VRH
    elas_dict['E_VRH'] = E_VRH

    # Flag mechanically unstable structures.
    # The equations can be found in Phys. Rev. B 90, 224104 (2014).
    # We also check whether the mechanical stability holds within a
    # tolerance of 10%: de Jong et. al. "Charting the complete elastic properties of
    # inorganic crystalline compounds"
    # Failing the tolerance check can indicate that the DFT calculation didn't
    # properly converge.
    elas_dict['mechanically_stable'] = True
    elas_dict['mechanically_stable_with_tolerance'] = True
    tolerance = 1.1
    if sym == 'cubic':
        if not ((cij[0,0] > abs(cij[0,1])) and
                (cij[0,0] + 2*cij[0,1] > 0) and
                (cij[3,3] > 0)
               ):
            elas_dict['mechanically_stable'] = False
        if not ((cij[0,0] > tolerance*abs(cij[0,1])) and
                (cij[0,0] + 2*cij[0,1] > 0) and
                (cij[3,3] > 0)
               ):
            elas_dict['mechanically_stable_with_tolerance'] = False
    elif sym == 'hexagonal':
        if not ((cij[0,0] > abs(cij[0,1])) and
                (2*cij[0,2]**2 < cij[2,2]*(cij[0,0] + cij[0,1])) and
                (cij[3,3] > 0) and
                (cij[5,5] > 0)
               ):
            elas_dict['mechanically_stable'] = False
        if not ((cij[0,0] > tolerance*abs(cij[0,1])) and
                (tolerance*2*cij[0,2]**2 < cij[2,2]*(cij[0,0] + cij[0,1])) and
                (cij[3,3] > 0) and
                (cij[5,5] > 0)
               ):
            elas_dict['mechanically_stable_with_tolerance'] = False
    else:
        sys.exit("{}(): ".format(inspect.currentframe().f_code.co_name) +
            "Mechanical instability check not implemented for sym = \"{}\"!".format(sym))

    # Round most quantities to integers, except compliance tensor and Poisson' ratio
    # Convert the tensors first to Python lists and only then round the numbers.
    # Otherwise the rounding might be destroyed in the process of transforming
    # numpy floats to Python floats.
    cij = cij.tolist()
    cij_nosym = cij_nosym.tolist()
    sij = sij.tolist()
    for i in range(len(cij)):
        for j in range(len(cij[i])):
            cij[i][j] = int(np.round(cij[i][j], 0))
            cij_nosym[i][j] = int(np.round(cij_nosym[i][j], 0))
            sij[i][j] = float(np.round(sij[i][j], 8))

    #
    for key, val in elas_dict.items():
        if key == 'mu_VRH':
            elas_dict[key] = float(np.round(val, decimals=4))
        else:
            try:
                elas_dict[key] = int(np.round(val, decimals=0))
            except:
                elas_dict[key] = 0

    return cij, sij, elas_dict, cij_nosym

def get_computation_info(ioa):
    """Finds the VASP version number, values of ENCUT, # of kpoints
    from the OUTCAR.
    """

    vasp_xc_tags = {
        '91': "Perdew - Wang 91 (PW-91)",
        'PE': "Perdew-Burke-Ernzerhof (PBE)",
        'AM': "AM05",
        'HL': "Hedin-Lundqvist",
        'CA': "Ceperley-Alder",
        'PZ': "Ceperley-Alder, parametrization of Perdew-Zunger",
        'WI': "Wigner",
        'RP': "revised Perdew-Burke-Ernzerhof (RPBE) with Pade Approximation",
        'RE': "revPBE",
        'VW': "Vosko-Wilk-Nusair (VWN)",
        'B3': "B3LYP, where LDA part is with VWN3-correlation",
        'B5': "B3LYP, where LDA part is with VWN5-correlation",
        'BF': "BEEF, xc (with libbeef)",
        'CO': "no exchange-correlation",
        'PS': "Perdew-Burke-Ernzerhof revised for solids (PBEsol)",
        'LIBXC': "LDA or GGA from Libxc",
        'LI': "LDA or GGA from Libxc",
        'OR': "optPBE",
        'BO': "optB88",
        'MK': "optB86b",
        'RA': "new RPA Perdew Wang",
        '03': "range-separated ACFDT (LDA - sr RPA) mu = 0.3\u00C5",
        '05': "range-separated ACFDT (LDA - sr RPA) mu = 0.5\u00C5",
        '10': "range-separated ACFDT (LDA - sr RPA) mu = 1.0\u00C5",
        '20': "range-separated ACFDT (LDA - sr RPA) mu = 2.0\u00C5",
        'PL': "new RPA+ Perdew Wang",
    }

    ioa = IoAdapterFileReader.use(ioa)
    outcar = list(ioa.file)

    info = {'version': None, 'ENCUT': None,
            'NKPTS': None, 'XC': None}
    LEXCH = None
    for line in outcar:
        # Every piece of info was already found:
        if not None in info.values():
            break
        line = line.rstrip()
        if info['version'] is None:
            tmp = re.search("vasp\.\d\.\d\.\d", line)
            if tmp is not None:
                info['version'] = line
        if info['ENCUT'] is None:
            tmp = re.search("ENCUT\s*=\s*([\d\.]*)\s*eV", line)
            if tmp is not None:
                info['ENCUT'] = tmp.groups()[0]
        if info['NKPTS'] is None:
            tmp = re.search("NKPTS = \s*(\d+)\s+", line)
            if tmp is not None:
                info['NKPTS'] = tmp.groups()[0]
        if LEXCH is None:
            tmp = re.search("\s*LEXCH\s+=\s*(\w+)", line)
            if tmp is not None:
                LEXCH = tmp.groups()[0]
        if info['XC'] is None:
            tmp = re.search("\s*GGA\s{5}=\s+([\d-]+)\s+", line)
            if tmp is not None:
                # Check if default POSCAR XC is used:
                GGA = tmp.groups()[0]
                if GGA == "--":
                    try:
                        info['XC'] = vasp_xc_tags[LEXCH]
                    except KeyError:
                        info['XC'] = "Unknown XC functional, LEXCH = " + LEXCH
                else:
                    try:
                        info['XC'] = vasp_xc_tags[tmp.groups()[0]]
                    except KeyError:
                        info['XC'] = "Unknown XC functional, LEXCH = " + tmp.groups()[0]

    # Get pseudopot info
    for line in outcar:
        tmp = re.search("TITEL  =\s*(PAW_.*)", line)
        if tmp is not None:
            pseudo_info = tmp.groups()[0].strip()
            if 'pseudopots' not in info.keys():
                info['pseudopots'] = ""
            if pseudo_info not in info['pseudopots']:
                info['pseudopots'] +=  pseudo_info + "|"
        if "POSCAR:" in line:
            break
    info['pseudopots'] = info['pseudopots'].rstrip("|")
    return info

