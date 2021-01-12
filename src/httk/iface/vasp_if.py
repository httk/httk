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

import os, shutil, math

import httk
from httk import config
from httk.core.template import apply_templates
from httk.atomistic.data import periodictable
from httk.core.ioadapters import cleveropen
from httk.core import *
from httk.core.basic import mkdir_p, micro_pyawk
from httk.atomistic import Structure
from httk.atomistic.structureutils import cartesian_to_reduced
import configparser
import numpy as np
import subprocess
import inspect


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


def poscar_to_structure(f, included_decimals=''):
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

    struct = Structure.create(uc_basis=frac_cell, uc_volume=volume, uc_scale=scale, uc_reduced_coords=frac_coords, uc_counts=counts, assignments=newoccupations, tags={'comment': comment}, periodicity=0)

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
                str(np.round(-float(self.stress_tensor[0])/10, 5)),
                str(np.round(-float(self.stress_tensor[1])/10, 5)),
                str(np.round(-float(self.stress_tensor[2])/10, 5)),
                str(np.round(-float(self.stress_tensor[4])/10, 5)),
                str(np.round(-float(self.stress_tensor[5])/10, 5)),
                str(np.round(-float(self.stress_tensor[3])/10, 5)),
                ]

        results = micro_pyawk(self.ioa, [
                              ["^ *energy *without *entropy= *([^ ]+) "+
                               "*energy\(sigma->0\) *= *([^ ]+) *$", None, read_energy],
                              ["FREE ENERGIE", None, set_final],
                              ["^ *in kB" + " *([^ \n]+)"*6, None, read_stress_tensor]
                              ], results, debug=False)
        self.parsed = True


def read_outcar(ioa):
    return OutcarReader(ioa)

def elastic_config(fn):
    config = configparser.ConfigParser()
    config.read(fn)
    # The type of symmetry
    try:
        sym = config["elastic"]["symmetry"].lstrip()
    except:
        sym = "cubic"

    # Use projection technique, i.e. to obtain cubic elastic
    # constants for non-cubic crystals, such as SQS supercells.
    try:
        project = eval(config["elastic"]["projection"])
    except:
        project = False

    try:
        force_sym = config["elastic"]["force_symmetry"].lstrip()
    except:
        force_sym = None

    # Delta values:
    tmp = config["elastic"]["delta"].lstrip().split("\n")
    deltas = []
    for line in tmp:
        line = line.split()
        deltas.append([float(x) for x in line])

    # Distortions in Voigt notation:
    distortions = []
    tmp = config["elastic"]["distortions"].lstrip().split("\n")
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
                        if vectors_are_same(dd, new_d):
                            include_new_d = False
                            break
                    if include_new_d:
                        new_distortions.append(new_d)
                        new_deltas.append(delta)
        else:
            raise NotImplementedError("Projection technique only implemented for cubic systems!")

        distortions = new_distortions
        deltas = new_deltas

    return sym, deltas, distortions, project, force_sym

def vectors_are_same(v1, v2):
    """Check whether all elements of two vectors are the same,
    within some tolerance."""
    tol = 1e-5
    max_diff = np.max(np.abs(np.array(v1) - np.array(v2)))
    if max_diff > tol:
        return False
    else:
        return True

def get_elastic_constants(path):
    sym, delta, distortions, project, force_sym = elastic_config(
        os.path.join(path, '../settings.elastic'))

    stress_target = []
    epsilon = []
    for i, dist in enumerate(distortions):
        for j, d in enumerate(delta[i]):
            # Collect stress components:
            outcar = read_outcar(os.path.join(path,
                'OUTCAR.cleaned.elastic{}_{}'.format(i+1, j+1)))
            # Check if the stress tensor was found in the OUTCAR.
            # If not, we can still continue and try to solve elastic
            # constants from the set of linear equations.
            try:
                st = outcar.stress_tensor_voigt_gpa
                eps = np.array(dist) * d
                epsilon.append(eps)
                tmp = []
                for val in st:
                    tmp.append(float(val))
                stress_target.append(tmp)
            except:
                continue

    # epsilon = jnp.array(epsilon).T
    epsilon = np.array(epsilon)
    # Convert to numpy array, negate the OUTCAR minus, and convert to GPa
    # stress_target = jnp.array(stress_target).T
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
            sys.exit(f"{inspect.currentframe().f_code.co_name}(): " +
                f"Full cij matrix not implemented for sym = \"{sym}\"!")

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
                sys.exit(f"{inspect.currentframe().f_code.co_name}(): " +
                    f"Symmetry reduction not implemented for sym = \"{sym}\"!")

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

        if sym == "hexagonal":
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
            sys.exit(f"{inspect.currentframe().f_code.co_name}(): " +
            f"Symmetrized cij matrix not implemented for sym = \"{sym}\"!")

        Csym = np.dot(Psym, C)
        return Csym

    A, B, symmetry_reduction = setup_linear_system(epsilon,
            stress_target, sym)
    print(sym, symmetry_reduction)
    # Solve the 21-component C-vector Tasnadi2012, PRB 85, 144112
    Cvector, residuals, rank, singular_values = np.linalg.lstsq(A,
        B, rcond=None)
    Cvector = Cvector.flatten()

    if symmetry_reduction:
        Cvector = get_full_C_vector(Cvector, sym)
    # if 1: #project:
        # Cvector = get_symmetrized_C_vector(Cvector, sym)

    cij = np.array(get_full_cij_matrix(Cvector))

    for row in cij:
        print(row)

    # Compute compliance tensor, which is the matrix inverse of cij
    sij = np.linalg.inv(cij)

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

    # Round most quantities to integers, except compliance tensor and Poisson' ratio
    # Convert the tensors first to Python lists and only then round the numbers.
    # Otherwise the rounding doesnt
    cij = cij.tolist()
    sij = sij.tolist()
    for i in range(len(cij)):
        for j in range(len(cij[i])):
            cij[i][j] = int(np.round(cij[i][j], 0))
            sij[i][j] = float(np.round(sij[i][j], 8))

    #
    for key, val in elas_dict.items():
        if key == 'mu_VRH':
            elas_dict[key] = float(np.round(val, decimals=4))
        else:
            elas_dict[key] = int(np.round(val, decimals=0))

    return cij, sij, elas_dict
