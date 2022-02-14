import os
import sys
import linecache
import math
import re
import time
import httk.task.ht_tasks_api as ht


def VASP_PREPARE_POTCAR(POSCAR=None, POTCAR=None):
    if POSCAR is None:
        POSCAR = "POSCAR"
    if POTCAR is None:
        POTCAR = "POTCAR"

    if "VASP_PSEUDOLIB" not in os.environ:
        print("Error in VASP_PREPARE_POTCAR: must set $VASP_PSEUDOLIB " +
              "to path for VASP pseudopotential library.")
        sys.exit(1)
    else:
        VASP_PSEUDOLIB = os.environ["VASP_PSEUDOLIB"]

    try:
        os.remove(POTCAR)
    except OSError:
        pass

    SPECIESLIST = linecache.getline(POSCAR, 6).rstrip().split()
    for SPECIES in SPECIESLIST:
        pseudo_found = False
        for PRIORITY in ("_3", "_2", "_d", "_pv", "_sv", "", "_h", "_s"):
            if SPECIES + PRIORITY == "Ru_pv":
                PRIORITY = "_sv"  # Ru_pv has probelm converging in the ground state

            pseudo_dir = VASP_PSEUDOLIB + "/{}{}".format(SPECIES, PRIORITY)
            if os.path.isdir(pseudo_dir):
                pseudo_potcar = pseudo_dir + "/POTCAR"
                if os.path.isfile(pseudo_potcar):
                    with open(POTCAR, "a") as f:
                        with open(pseudo_potcar, "r") as ff:
                            f.write(ff.read())
                    pseudo_found = True
                    break

            # TODO: Implement compressed POTCARS
            # if [ -d "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}" ]; then
                # if [ -e "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.Z" ]; then
                    # zcat "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.Z" >> "$POTCAR"
                    # continue 2
                # fi
                # if [ -e "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.gz" ]; then
                    # zcat "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.gz" >> "$POTCAR"
                    # continue 2
                # fi
                # if [ -e "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.bz2" ]; then
                    # bzcat "$VASP_PSEUDOLIB/${SPECIES}${PRIORITY}/POTCAR.bz2" >> "$POTCAR"
                    # continue 2
                # fi
            # fi
        if not pseudo_found:
            print("Error in VASP_PREPARE_POTCAR: could not find pseudopotential for: {}".format(SPECIES))
            print("VASP_PSEUDOLIB was set to: {}".format(VASP_PSEUDOLIB))
            sys.exit(1)


def VASP_POTCAR_SUMMARY(FILE=None):
    if FILE is None:
        FILE = "POTCAR"

    with open(FILE, "r") as f:
        lines = f.read().splitlines()

    text = []
    collect = False
    for i in range(len(lines)):
        line = lines[i]
        if "parameters from PSCTR are:" in line:
            text.append(lines[i - 2] + lines[i - 1] + "1")
            collect = True
        elif "Description" in line:
            collect = False
        if collect:
            text.append(line)

    with open("POTCAR.summary", "w") as f:
        for line in text:
            f.write(line + "\n")


def VASP_PRECLEAN():
    files_to_remove = [
        "WAVECAR", "CONTCAR", "PCDAT", "IBZKPT",
        "EIGENVAL", "XDATCAR", "OSZICAR", "OUTCAR",
        "DOSCAR", "CHG", "CHGCAR", "vasprun.xml",
        "PROCAR"
    ]
    for f in files_to_remove:
        try:
            os.remove(f)
        except:
            pass


def VASP_PREPARE_CALC(ACCURACY=None, lval=None, kpoints_type=None):
    VASP_CHECK_AND_FIX_POSCAR()
    VASP_PREPARE_KPOINTS(lval, kpoints_type)
    VASP_PREPARE_INCAR(ACCURACY)
    VASP_CHECK_PATH_LENGTH()


def VASP_CHECK_PATH_LENGTH():
    if len(os.getcwd()) > 240:
        print("Path is longer than 240 characters!")
        print("This could cause unpredictable errors.")
        ht.HT_TASK_ATOMIC_SECTION_END_BROKEN()


def VASP_CHECK_AND_FIX_POSCAR():
    ht.mv("POSCAR", "ht.tmp.POSCAR")
    with open("ht.tmp.POSCAR", "r") as f_src:
        lines = f_src.read().splitlines()

    with open("POSCAR", "w") as f_dest:
        for i, line in enumerate(lines):
            if i < 1 or i > 4:
                f_dest.write(line + "\n")
            elif i == 1:
                scale = line
            elif i == 2:
                tmp = line.split()
                v1 = [float(tmp[0]), float(tmp[1]), float(tmp[2])]
            elif i == 3:
                tmp = line.split()
                v2 = [float(tmp[0]), float(tmp[1]), float(tmp[2])]
            elif i == 4:
                tmp = line.split()
                v3 = [float(tmp[0]), float(tmp[1]), float(tmp[2])]

                celldet = v1[0] * v2[1] * v3[2] + v1[1] * v2[2] * v3[0] + \
                    v1[2] * v2[0] * v3[1] - v1[2] * v2[1] * v3[0] - \
                    v1[1] * v2[0] * v3[2] - v1[0] * v2[2] * v3[1]

                if celldet < 0:
                    for vec in (v1, v2, v3):
                        for i in range(3):
                            vec[i] = -vec[i] if vec[i] != 0 else vec[i]

                    f_dest.write(scale + "\n")
                    f_dest.write("{0:20.16f} {1:20.16f} {2:20.16f}\n".format(*v1))
                    f_dest.write("{0:20.16f} {1:20.16f} {2:20.16f}\n".format(*v2))
                    f_dest.write("{0:20.16f} {1:20.16f} {2:20.16f}\n".format(*v3))
                else:
                    f_dest.write(lines[1] + "\n")
                    f_dest.write(lines[2] + "\n")
                    f_dest.write(lines[3] + "\n")
                    f_dest.write(lines[4] + "\n")

    os.remove("ht.tmp.POSCAR")


def VASP_PREPARE_KPOINTS(lval=None, kpoints_type=None):
    if lval is None:
        lval = 20

    line = VASP_KPOINTSLINE(lval)

    if line is None or len(line) == 0:
        sys.stderr.write("Error in VASP_PREPARE_KPOINTS: " +
                         "VASP_PREPARE_KPOINTS got empty KPOINTSLINE\n")
        sys.exit(1)

    if kpoints_type is None:
        if ht.find_in_remedy_files("GAMMA_KPTS"):
            kpoints_type = "Gamma"
        else:
            kpoints_type = "Monkhorst-Pack"

    with open("KPOINTS", "w") as f:
        f.write("Automatic mesh generated by run.sh\n")
        f.write("0\n")
        f.write("{}\n".format(kpoints_type))
        f.write("{}\n".format(line))
        f.write("0. 0. 0.\n")


def VASP_KPOINTSLINE(lval=None):
    if lval is None:
        sys.stderr.write("Error in VASP_KPOINTSLINE: must be called with " +
                         "a KPOINT density. (l parameter in VASP manual on " +
                         "automatic KPOINT generation.)\n")
        return ""

    if ht.find_in_remedy_files("EQUAL_KPTS"):
        equalkpts = 1
    else:
        equalkpts = 0

    if ht.find_in_remedy_files("BUMP_KPTS"):
        bumpkpts = 1
    else:
        bumpkpts = 0
    #
    # We do things a bit differently than the corresponding routine in VASP.
    # We always round up (ceiling)
    # We always generate a symmetrix grid N x N x N to wase a lot of computational time
    # but avoid scary warnings about reciprocal grid not matching the real grid
    #
    with open("POSCAR", "r") as f:
        lines = f.read().splitlines()

    for i, line in enumerate(lines):
        if i == 1:
            scale = float(line.split()[0])
        elif i == 2:
            tmp = line.split()
            v1 = [float(tmp[0]), float(tmp[1]), float(tmp[2])]
        elif i == 3:
            tmp = line.split()
            v2 = [float(tmp[0]), float(tmp[1]), float(tmp[2])]
        elif i == 4:
            tmp = line.split()
            v3 = [float(tmp[0]), float(tmp[1]), float(tmp[2])]

    celldet = v1[0] * v2[1] * v3[2] + v1[1] * v2[2] * v3[0] + \
        v1[2] * v2[0] * v3[1] - v1[2] * v2[1] * v3[0] - \
        v1[1] * v2[0] * v3[2] - v1[0] * v2[2] * v3[1]

    cellvol = abs(celldet)
    if cellvol < 1e-6:
        sys.stderr.write("Error in VASP_KPOINTSLINE: singular cell vectors. POSCAR is broken.\n")
        kptsline = ""

    if scale < 0.0:
        scale = (-scale / cellvol)**(1.0 / 3.0)

    b1len = math.sqrt(abs(v2[1] * v3[0] - v2[0] * v3[1])**2 +
                      abs(v2[2] * v3[0] - v2[0] * v3[2])**2 +
                      abs(v2[2] * v3[1] - v2[1] * v3[2])**2) / (celldet * scale)
    b2len = math.sqrt(abs(v1[1] * v3[0] - v1[0] * v3[1])**2 +
                      abs(v1[2] * v3[0] - v1[0] * v3[2])**2 +
                      abs(v1[2] * v3[1] - v1[1] * v3[2])**2) / (celldet * scale)
    b3len = math.sqrt(abs(v1[1] * v2[0] - v1[0] * v2[1])**2 +
                      abs(v1[2] * v2[0] - v1[0] * v2[2])**2 +
                      abs(v1[2] * v2[1] - v1[1] * v3[2])**2) / (celldet * scale)

    N1 = math.ceil(lval * b1len + 0.5)
    if N1 < 3:
        N1 = 3

    N2 = math.ceil(lval * b2len + 0.5)
    if N2 < 3:
        N2 = 3

    N3 = math.ceil(lval * b3len + 0.5)
    if N3 < 3:
        N3 = 3

    if bumpkpts == 1:
        N1 += 1
        N2 += 1
        N3 += 1

    if equalkpts == 1:
        NMAX = N1
        if N2 > NMAX:
            NMAX = N2
        if N3 > NMAX:
            NMAX = N3
        kptsline = "{} {} {}".format(NMAX, NMAX, NMAX)
    else:
        kptsline = "{} {} {}".format(N1, N2, N3)

    if kptsline is None or len(kptsline) == 0:
        sys.stderr.write("Error in VASP_KPOINTSLINE: could not calculate KPOINTS.\n")
        sys.exit(1)
    return kptsline


def VASP_GET_TAG(tag, file=None):
    if file is None:
        file = "INCAR"
    with open(file, "r") as f:
        lines = f.read().splitlines()
    for line in lines:
        # Skip comment lines:
        if line.lstrip().startswith("#"):
            continue
        match = re.search("[\t ]*{}[\t ]*=(.*)".format(tag), line)
        if match is not None:
            return ht.find_type_conversion(match.groups()[0].rstrip())
    return None


def VASP_SET_TAG(tag, value):
    # Control the print format of floats:
    if isinstance(value, float):
        value = "{:.12f}".format(value)
    with open("INCAR", "r") as f:
        lines = f.read().splitlines()

    header = "### BEGIN: PARAMETERS CHANGED BY VASP_SET_TAG ###"
    header_end = "###   END: PARAMETERS CHANGED BY VASP_SET_TAG ###"
    header_found = False
    new_incar = []
    for line in lines:
        line_is_comment = False
        if line.lstrip().startswith("#"):
            line_is_comment = True
        match = re.search("[\t ]*{}[\t ]*=".format(tag), line)
        if match is None or line_is_comment:
            new_incar.append(line)
        else:
            continue
        if line == header:
            header_found = True

    if not header_found:
        # Allow some space for the VASP_SET_TAG block
        if new_incar[-1].strip() != "":
            new_incar.append("")
        new_incar.append(header)
        new_incar.append("{}={}".format(tag, value))
        new_incar.append(header_end)
        new_incar.append("")
    else:
        for i, line in enumerate(new_incar):
            if line == header_end:
                new_incar.insert(i, "{}={}".format(tag, value))
                break

    with open("INCAR", "w") as f:
        for line in new_incar:
            f.write(line + "\n")


def VASP_PREPARE_INCAR(ACCURACY=None, EDIFFMARGIN=None):
    if "HT_NBR_NODES" in os.environ:
        HT_NBR_NODES = int(os.environ["HT_NBR_NODES"])
    else:
        HT_NBR_NODES = None

    if not os.path.exists("POSCAR"):
        sys.stderr.write("VASP_PREPARE_INCAR: Missing POSCAR file\n")
        sys.exit(1)

    if not os.path.exists("INCAR"):
        sys.stderr.write("VASP_PREPARE_INCAR: Need a base INCAR file to start from.\n")
        sys.exit(1)

    POSCAROCCUPATIONLINE = 7
    OCCUPATIONS = linecache.getline("POSCAR", POSCAROCCUPATIONLINE).rstrip().split()
    OCCUPATIONS = list(map(int, OCCUPATIONS))
    NATOMS = sum(OCCUPATIONS)

    if ACCURACY is None:
        if ht.find_in_remedy_files("EDIFF_SMALLER"):
            ACCURACY = 0.0001
        elif ht.find_in_remedy_files("EDIFF_SMALLER_2"):
            ACCURACY = 0.00001
        else:
            ACCURACY = 0.001
        DEFAULT_ACCURACY = 1
    else:
        DEFAULT_ACCURACY = 0

    if EDIFFMARGIN is None:
        NSW = VASP_GET_TAG("NSW")
        if NSW is not None:
            if NSW > 1:
                # Relaxations are typically improved by increasing the electronic convergence,
                # since then more accurate ionic steps are taken
                EDIFFMARGIN = 500
            else:
                EDIFFMARGIN = 33
        else:
            EDIFFMARGIN = 33

    if ACCURACY != -1:
        EDIFF = VASP_GET_TAG("EDIFF")
        EDIFFG = VASP_GET_TAG("EDIFFG")
        if EDIFF is None or DEFAULT_ACCURACY == 0:
            EDIFF = max(ACCURACY * NATOMS / EDIFFMARGIN, 1e-6)
            VASP_SET_TAG("EDIFF", EDIFF)
        if EDIFFG is None or DEFAULT_ACCURACY == 0:
            EDIFFG = max(ACCURACY * NATOMS, 1e-4)
            VASP_SET_TAG("EDIFFG", EDIFFG)

    NPAR = VASP_GET_TAG("NPAR")
    if NPAR is None and HT_NBR_NODES is not None:
        NPAR = int(math.sqrt(HT_NBR_NODES))
        if NPAR < 1:
            NPAR = 1
        VASP_SET_TAG("NPAR", NPAR)

    if ht.find_in_remedy_files("NPARONE"):
        VASP_SET_TAG("NPAR", 1)

    MAGMOMS = VASP_GET_TAG("MAGMOMS")
    if MAGMOMS is None:
        LINE = VASP_MAGMOMLINE()
        if len(LINE) == 0:
            sys.stderr.write("Error in VASP_PREPARE_INCAR: got empty MAGMOM line\n")
            sys.exit(1)
        VASP_SET_TAG("MAGMOM", LINE)

    NBANDS = VASP_GET_TAG("NBANDS")
    if NBANDS is None:
        LINE = VASP_NBANDSLINE()
        if len(LINE) == 0:
            sys.stderr.write("Error in VASP_PREPARE_INCAR: got empty NBANDS line\n")
            sys.exit(1)
        VASP_SET_TAG("NBANDS", LINE)

    if ht.find_in_remedy_files("NOSYM"):
        VASP_SET_TAG("ISYM", 0)

    if ht.find_in_remedy_files("GAUSSMEAR"):
        VASP_SET_TAG("ISMEAR", 0)
        VASP_SET_TAG("SIGMA", 0.05)

    if ht.find_in_remedy_files("LREALFALSE"):
        VASP_SET_TAG("LREAL", ".FALSE.")

    if ht.find_in_remedy_files("SOFTMIX"):
        VASP_SET_TAG("ICHARG", 2)
        VASP_SET_TAG("AMIX", 0.10)
        VASP_SET_TAG("BMIX", 0.01)

    if ht.find_in_remedy_files("SOFTMIX2"):
        VASP_SET_TAG("ICHARG", 2)
        VASP_SET_TAG("BMIX", 3.00)
        VASP_SET_TAG("AMIN", 0.01)

    if ht.find_in_remedy_files("ALGOALL"):
        VASP_SET_TAG("ALGO", "ALL")
        VASP_SET_TAG("TIME", 0.4)

    if ht.find_in_remedy_files("ALGOALL2"):
        VASP_SET_TAG("ALGO", "All")
        VASP_SET_TAG("TIME", 0.05)

    if ht.find_in_remedy_files("ALGODAMPED"):
        VASP_SET_TAG("ALGO", "Damped")
        VASP_SET_TAG("TIME", 0.05)

    if ht.find_in_remedy_files("LOWSYMPREC"):
        VASP_SET_TAG("SYMPREC", 1e-4)

    if ht.find_in_remedy_files("HIGHSYMPREC"):
        VASP_SET_TAG("SYMPREC", 1e-6)

    ICHARG = VASP_GET_TAG("ICHARG")
    if ICHARG is not None:
        if ICHARG == 1:
            # TODO: Make sure the logic here is correct
            if not os.path.exists("CHGCAR"):
                VASP_SET_TAG("ICHARG", 2)
            elif os.path.exists("CHGCAR"):
                if os.path.getsize("CHGCAR") > 0:
                    VASP_SET_TAG("ICHARG", 2)
            else:
                if os.path.exists("ht.controlled.msgs"):
                    if ht.find_in_file("^CHGCAR_INCOMPLETE", "ht.controlled.msgs"):
                        VASP_SET_TAG("ICHARG", 2)

    NEDOS = VASP_GET_TAG("NEDOS")
    if NEDOS is None:
        if ht.find_in_remedy_files("BUMP_NEDOS"):
            VASP_SET_TAG("NEDOS", 1000)


def VASP_MAGMOMLINE():
    POSCAROCCUPATIONLINE = 7

    with open("POSCAR", "r") as f:
        poscar = f.read().splitlines()

    # TODO: This re search should be tested for correctness:
    match = re.search("^.*\[MAGMOM=([^]]*)\]", poscar[0])
    if match is not None:
        return match.groups()[0]

    MAGMOM = ""
    occupations = linecache.getline("POSCAR", POSCAROCCUPATIONLINE).rstrip().split()
    for o in occupations:
        MAGMOM += "{}*5 ".format(o)
    # Remove the last space
    MAGMOM = MAGMOM.rstrip()

    if len(MAGMOM) == 0:
        sys.stderr.write("Error in VASP_MAGMOMLINE: could not calculate MAGMOM.\n")
        sys.exit(1)

    return MAGMOM


def VASP_NBANDSLINE():
    """Reimplementation of the algorithm of cif2cell.
    NBANDS is the max of the default in VASP spin-polarized
    (0.6*nelect + NIONS/2), non-spin: (nelect/2 + NIONS/2),
    occupied bands + 20, or 0.6*nelect + total initalized magnetic moment
    In addition, it must be divisible by NPAR, so we round up to that.
    """

    if not os.path.exists("POSCAR") or not os.path.exists("POTCAR") or not os.path.exists("INCAR"):
        sys.stderr.write("VASP_NBANDSLINE: VASP INPUT FILES MISSING.\n")
        sys.exit(1)

    with open("POTCAR", "r") as f:
        potcar = f.read()

    ZVALS = []
    match = re.findall("[\t ]*POMASS[\t ]*=[\t ]*[\d.]*;[\t ]*ZVAL[\t ]*=[\t ]*([\d.]*)[\t ]*mass and valenz", potcar)
    if match is not None:
        for m in match:
            ZVALS.append(float(m))

    if len(ZVALS) == 0:
        sys.stderr.write("VASP_NBANDSLINE: Could not extract Z-vals from POTCAR\n")
        sys.exit(1)

    POSCAROCCUPATIONLINE = 7
    COUNTS = linecache.getline("POSCAR", POSCAROCCUPATIONLINE).rstrip().split()
    COUNTS = list(map(int, COUNTS))

    if len(COUNTS) == 0:
        sys.stderr.write("VASP_NBANDSLINE: Could not extract atom counts from POSCAR.\n")
        sys.exit(1)

    NATOMS = sum(COUNTS)

    if NATOMS == 0:
        sys.stderr.write("VASP_NBANDSLINE: Could not extract number of atoms from POSCAR.\n")
        sys.exit(1)

    with open("INCAR", "r") as f:
        incar = f.read()
    NMAG = 0
    match = re.search("[\t ]*MAGMOM[\t ]*=(.*)", incar)
    if match is not None:
        moms = match.groups()[0].split()
        for m in moms:
            NMAG += eval(m)

    if NMAG == 0:
        sys.stderr.write("VASP_NBANDSLINE: Could not extract MAGMOM line from INCAR.\n")
        sys.exit(1)

    ISPIN = VASP_GET_TAG("ISPIN")

    if ISPIN is None:
        sys.stderr.write("VASP_NBANDSLINE: Could not extract ISPIN information from INCAR.\n")
        sys.exit(1)

    NELECT = 0
    for zval, count in zip(ZVALS, COUNTS):
        NELECT += zval * count

    NBANDS = 1
    NBANDS2 = 1
    NBANDS3 = 1

    if NATOMS < 6:
        NATOMS = 6

    # TODO: Add support for noncollinear
    if ISPIN == 2:
        NBANDS = int(0.6 * NELECT + 1) + math.ceil(NATOMS / 2)
        NBANDS2 = int(0.6 * NELECT + 1) + math.ceil(NMAG / 2)
        NBANDS3 = int(0.6 * NELECT + 1) + 20

        # echo "GOT: NELECT=$NELECT NATOMS=$NATOMS NMAG=$NMAG $NBANDS $NBANDS2 $NBANDS3" >&2
    else:
        NBANDS = int(NELECT / 2 + 2) + math.ceil(NATOMS / 2)
        NBANDS2 = NBANDS
        NBANDS3 = math.ceil(NELECT / 2) + 20

    if NBANDS2 > NBANDS:
        NBANDS = NBANDS2

    if NBANDS3 > NBANDS:
        NBANDS = NBANDS3

    # Vasp can generally get unhappy with an uneven number of bands...
    if NBANDS % 2 == 1:
        NBANDS += 1
        ADDED = 1
    else:
        ADDED = 0

    NPAR = VASP_GET_TAG("NPAR")
    if NPAR is not None:
        MISMATCH = NBANDS % NPAR
        if MISMATCH != 0:
            NBANDS = NBANDS + MISMATCH

    if ht.find_in_remedy_files("BUMP_BANDS"):
        if ADDED == 1:
            NBANDS -= 1
        else:
            NBANDS += 1

    if NPAR is not None:
        MISMATCH = NBANDS % NPAR
        if MISMATCH != 0:
            NBANDS = NBANDS + MISMATCH

    return str(NBANDS)


# Timeouts: 1 year=31536000, 1 week=604800, 1 day=86400, 6h=21600
def VASP_RUN_CONTROLLED(timeout, command, *args):
    RETURNCODE = ht.HT_TASK_RUN_CONTROLLED(timeout, VASP_STDOUT_CHECKER,
                                           VASP_OSZICAR_CHECKER,
                                           VASP_OUTCAR_CHECKER,
                                           "--", command, *args)
    print("{} EXIT STATUS={}".format(ht.get_bashlike_date(), RETURNCODE))
    if RETURNCODE == 100:
        print("{}: VASP APPEAR TO HAVE STOPPED DUE TO USER SIGNAL (SIGINT), PUT JOB IN BROKEN STATE.".format(ht.get_bashlike_date()))
        ht.HT_TASK_BROKEN()

    if RETURNCODE == 0:
        if ht.find_in_file("^FINISHED", "ht.controlled.msgs"):
            print("{}: VASP APPEAR TO HAVE STOPPED NORMALLY.".format(ht.get_bashlike_date()))
        else:
            print("{}: VASP APPEAR TO HAVE HALTED ** WITH AN ERROR **.".format(ht.get_bashlike_date()))
            RETURNCODE = 2
        if ht.find_in_file("^LAST BADCONV", "ht.controlled.msgs"):
            print("CONVERGENCE PROBLEM IN LAST IONIC STEP.")
            RETURNCODE = 4
    ht.mv("stdout.out", "vasp.out")
    return RETURNCODE


def VASP_STDOUT_CHECKER(MSGFILE, EXITPID, process):
    returncode = 0
    ISYM = VASP_GET_TAG("ISYM")
    if ISYM is None:
        ISYM = 1
    else:
        ISYM = 0

    # Variables that are defined in AWK implicitly
    subherm_count = 0
    star_count = 0
    simple_number = 0
    zbrent = 0

    with open(MSGFILE, "w") as mf:
        print("STDOUT_CHECKER ACTIVE {}".format(EXITPID))
        mf.write("STDOUT_CHECKER ACTIVE {}\n".format(EXITPID))

        with open("stdout.out", "w") as f:
            # The "process.stdout" is an iterator that returns
            # lines whenever the external program prints them to the
            # stdout.
            for line in process.stdout:
                line = line.decode().rstrip()

                # /WARNING: Sub-Space-Matrix is not hermitian in DAV/ && subherm_count>5 { next }
                if "WARNING: Sub-Space-Matrix is not hermitian in DAV" in line and subherm_count > 5:
                    continue

                # /hit a member that was already found in another star/ && star_count>5 { next }
                if "hit a member that was already found in another star" in line and star_count > 5:
                    continue

                # /^ *-?[0-9]+\.[0-9]+(E-?[0-9]+)? *$/ && simple_number>=100 { next }
                if ht.re_line_matches("^ *-?[0-9]+\.[0-9]+(E-?[0-9]+)? *$", line) and simple_number >= 100:
                    continue

                # /WARNING: chargedensity file is incomplete/ {print "CHGCAR_INCOMPLETE" >> msgfile; exit 2}
                if "WARNING: chargedensity file is incomplete" in line:
                    mf.write("CHGCAR_INCOMPLETE\n")
                    returncode = 2
                    break

                # The 4 lines below should be the equivalent of the AWK line:
                # {print $0; system("");}
                f.write(line + "\n")
                f.flush()
                sys.stdout.write(line + "\n")
                sys.stdout.flush()

                # /^ *-?[0-9]+\.[0-9]+(E-?[0-9]+)? *$/ { simple_number+=1; if (simple_number == 99) {print "SPEWS_SINGLE_LINE_VALUES" >> msgfile} }
                if ht.re_line_matches("^ *-?[0-9]+\.[0-9]+(E-?[0-9]+)? *$", line):
                    simple_number += 1
                    if simple_number == 99:
                        mf.write("SPEWS_SINGLE_LINE_VALUES\n")

                # /WARNING: Sub-Space-Matrix is not hermitian in DAV/ { subherm_count += 1 }
                if "WARNING: Sub-Space-Matrix is not hermitian in DAV" in line:
                    subherm_count += 1

                # /hit a member that was already found in another star/ { star_count += 1}
                if "hit a member that was already found in another star" in line:
                    star_count += 1

                # /LAPACK: Routine ZPOTRF failed/ {print "ZPOTRF" >> msgfile; exit 2}
                if "LAPACK: Routine ZPOTRF failed" in line:
                    mf.write("ZPOTRF\n")
                    returncode = 2
                    break

                # /Reciprocal lattice and k-lattice belong to different class of lattices./ { print "KPTSCLASS" >> msgfile; if(ISYM!=0) { exit 2 } }
                if "Reciprocal lattice and k-lattice belong to different class of lattices." in line:
                    mf.write("KPTSCLASS\n")
                    if ISYM != 0:
                        returncode = 2
                        break

                # /ZBRENT: can'"'"'t locate minimum, use default step/ && zbrent!=1 {print "ZBRENT" >> msgfile; zbrent=1}
                if "ZBRENT: can't locate minimum, use default step" in line and zbrent != 1:
                    mf.write("ZBRENT\n")
                    zbrent = 1

                # /ZBRENT: fatal error in bracketing/ {print "ZBRENT_BRACKETING" >> msgfile;}
                if "ZBRENT: fatal error in bracketing" in line:
                    mf.write("ZBRENT_BRACKETING\n")

                # /One of the lattice vectors is very long/ {print "TOOLONGLATTVEC" >> msgfile; exit 2}
                if "One of the lattice vectors is very long" in line:
                    mf.write("TOOLONGLATTVEC\n")
                    returncode = 2
                    break

                # /Tetrahedron method fails for NKPT<4/ {print "TETKPTS" >> msgfile; exit 2}
                # /Fatal error detecting k-mesh/ {print "TETKPTS" >> msgfile; exit 2}
                # /Fatal error: unable to match k-point/ {print "TETKPTS" >> msgfile; exit 2}
                # /Routine TETIRR needs special values/ {print "TETKPTS" >> msgfile; exit 2}
                if "Tetrahedron method fails for NKPT<4" in line or \
                   "Fatal error detecting k-mesh" in line or \
                   "Fatal error: unable to match k-point" in line or \
                   "Routine TETIRR needs special values" in line:
                    mf.write("TETKPTS\n")
                    returncode = 2
                    break

                # /inverse of rotation matrix was not found/ {print "INVROTMATRIX" >> msgfile; exit 2}
                if "inverse of rotation matrix was not found" in line:
                    mf.write("INVROTMATRIX\n")
                    returncode = 2
                    break

                ## BRMIX errors can be recovered from, so let the program run its course.
                # /BRMIX: very serious problems/ {print "BRMIX" >> msgfile;}
                if "BRMIX: very serious problems" in line:
                    mf.write("BRMIX\n")

                # /Routine TETIRR needs special values/ {print "TETIRR" >> msgfile;}
                if "Routine TETIRR needs special values" in line:
                    mf.write("TETIRR\n")

                # /Could not get correct shifts/ {print "SHIFTS" >> msgfile;}
                if "Could not get correct shifts" in line:
                    mf.write("SHIFTS\n")

                # /REAL_OPTLAY: internal error/ {print "REAL_OPTLAY" >> msgfile;}
                if "REAL_OPTLAY: internal error" in line:
                    mf.write("REAL_OPTLAY\n")

                # /internal ERROR RSPHER/ {print "RSPHER" >> msgfile;}
                if "internal ERROR RSPHER" in line:
                    mf.write("RSPHER\n")

                # /RSPHER: internal ERROR:/ {print "RSPHER" >> msgfile; exit 2}
                if "RSPHER: internal ERROR:" in line:
                    mf.write("RSPHER\n")
                    returncode = 2
                    break

                # /WARNING: DENTET: can'"'"'t reach specified precision/ {print "DENTET" >> msgfile;}
                if "WARNING: DENTET: can't reach specified precision" in line:
                    mf.write("DENTET\n")

                # /unoccupied bands, you have included TOO FEW BANDS/ {print "NBANDS" >> msgfile;}
                if "unoccupied bands, you have included TOO FEW BANDS" in line:
                    mf.write("NBANDS\n")

                # /ERROR: the triple product of the basis vectors/ {print "TRIPLEPRODUCT" >> msgfile;}
                if "ERROR: the triple product of the basis vectors" in line:
                    mf.write("TRIPLEPRODUCT\n")

                # /Found some non-integer element in rotation matrix/ {print "ROTMATRIX" >> msgfile;}
                if "Found some non-integer element in rotation matrix" in line:
                    mf.write("ROTMATRIX\n")

                # /BRIONS problems: POTIM should be increased/ {print "BRIONS" >> msgfile;}
                if "BRIONS problems: POTIM should be increased" in line:
                    mf.write("BRIONS\n")

                # /WARNING: small aliasing \(wrap around\) errors must be expected/ {print "ALIASING" >> msgfile}
                if "WARNING: small aliasing (wrap around) errors must be expected" in line:
                    mf.write("ALIASING\n")

                # /The distance between some ions is very small/ {print "TOOCLOSE" >> msgfile; exit 2}
                if "The distance between some ions is very small" in line:
                    mf.write("TOOCLOSE\n")
                    returncode = 2
                    break

                # /Therefore set LREAL=.FALSE. in the  INCAR file/ {print "LREALFALSE" >> msgfile; exit 2}
                if "Therefore set LREAL=.FALSE. in the  INCAR file" in line:
                    mf.write("LREALFALSE\n")
                    returncode = 2
                    break

                # /Sorry, number of cells and number of vectors did not agree./ {print "PRICELL" >> msgfile; exit 2}
                if "Sorry, number of cells and number of vectors did not agree." in line:
                    mf.write("PRICELL\n")
                    returncode = 2
                    break

                # /ERROR FEXCF: supplied exchange-correlation table/ {FEXCF=1; print "FEXCF" >> msgfile;}
                if "ERROR FEXCF: supplied exchange-correlation table" in line:
                    FEXCF = 1
                    mf.write("FEXCF\n")

                # /is too small, maximal index :/ && FEXCF==1 {exit 2;}
                if "is too small, maximal index :" in line and FEXCF == 1:
                    returncode = 2
                    break

                # /internal error in RAD_INT: RHOPS \/= RHOAE/ {print "RADINT" >> msgfile; exit 2;}
                if "internal error in RAD_INT: RHOPS /= RHOAE" in line:
                    mf.write("RADINT\n")
                    returncode = 2
                    break

                # /internal ERROR in NONLR_ALLOC/ {print "NONLR_ALLOC" >> msgfile; exit 2;}
                if "internal ERROR in NONLR_ALLOC" in line:
                    mf.write("NONLR_ALLOC\n")
                    returncode = 2
                    break

                # /Error EDDDAV: Call to ZHEGV failed./ {print "EDDAV_ZHEGV" >> msgfile;}
                if "Error EDDDAV: Call to ZHEGV failed." in line:
                    mf.write("EDDAV_ZHEGV\n")

                # /WARNING: CNORMN: search vector ill defined/ {print "CNORMN" >> msgfile;}
                if "WARNING: CNORMN: search vector ill defined" in line:
                    mf.write("CNORMN\n")

        mf.write("STDOUT_CHECKER END (CODE={})\n".format(returncode))

    if returncode == 2:
        process.terminate()
    return returncode


def VASP_CLEAN_OUTCAR(FILE=None, clean_forces_acting_on_ions=False,
                      clean_avg_electrostatic_pot_at_core=False):
    if FILE is None:
        FILE = "OUTCAR"
    if not os.path.exists(FILE):
        print("VASP_CLEAN_OUTCAR: Missing {} file.".format(FILE))
        sys.exit(1)
    
    dirname = os.path.dirname(FILE)
    if dirname == "":
        dirname = "."
    off = 0
    with open(FILE, "r") as f_src:
        with open(os.path.join(dirname, "OUTCAR.cleaned"), "w") as f_dest:
            for line in f_src:
                newline = None
                if "Following reciprocal coordinates:" in line and off == 0:
                    newline = "VASP_CLEAN_OUTCAR: Removed k-point specification\n"
                    off = 2
                elif "Following cartesian coordinates:" in line and off == 0:
                    newline = "VASP_CLEAN_OUTCAR: Removed k-point specification\n"
                    off = 2
                elif "k-points in units of 2pi/SCALE and weight:" in line and off == 0:
                    newline = "VASP_CLEAN_OUTCAR: Removed k-point listning.\n"
                    off = 2
                elif "k-points in reciprocal lattice and weights" in line and off == 0:
                    newline = "VASP_CLEAN_OUTCAR: Removed k-point specification\n"
                    off = 2
                elif "k-point" in line and "plane waves:" in line and off == 0:
                    newline = "VASP_CLEAN_OUTCAR: Removed k-point plane wave data\n"
                    off = 2
                elif clean_forces_acting_on_ions and "FORCES acting on ions" in line and off == 0:
                    newline = "VASP_CLEAN_OUTCAR: Removed FORCES acting on ions data\n"
                    off = 2
                elif clean_avg_electrostatic_pot_at_core and "average (electrostatic) potential at core" in line and off == 0:
                    newline = "VASP_CLEAN_OUTCAR: Removed average electrostatic potential at core data\n"
                    off = 2
                elif ht.re_line_matches("^ *k-point *[0-9*]* *: +[0-9.-]* +[0-9.-]* +[0-9.-]* *$", line) and off == 0:
                    newline = "VASP_CLEAN_OUTCAR: Removed k-point occupation data\n"
                    off = 1
                elif off == 1 and ht.re_line_matches("^ *----------------------------------- *", line):
                    off = 0
                elif off == 2 and ht.re_line_matches("^ *$", line):
                    off = 0
                elif off == 0:
                    newline = line

                if newline is not None:
                    f_dest.write(newline)


def VASP_OUTCAR_CHECKER(MSGFILE, EXITPID):
    with open(MSGFILE, "w") as f:
        f.write("OUTCAR_CHECKER ACTIVE\n")

    # Do not try to follow a file before there is a file to follow.
    # while not os.path.exists("OUTCAR"):
    #     time.sleep(0.1)

    RETURNCODE = 0
    for line in ht.follow_file("OUTCAR"):
        line = line.rstrip()
        if "total allocation" in line:
            if float(line.split()[3]) > 500000:
                with open(MSGFILE, "a") as f:
                    f.write("REALSPACEALLOCTOOLARGE\n")
                RETURNCODE = 2
                break
        elif "General timing and accounting informations for this job:" in line:
            with open(MSGFILE, "a") as f:
                f.write("FINISHED\n")
            RETURNCODE = 0
            break

    with open(MSGFILE, "a") as f:
        f.write("OUTCAR_CHECKER END\n")

    return RETURNCODE


def VASP_OSZICAR_CHECKER(MSGFILE, EXITPID):
    TIMEOUT = 3600

    # Do not try to follow a file before there is a file to follow.
    # while not os.path.exists("OUTCAR"):
    #     time.sleep(0.1)

    OUTCARPARAMS_STOP = True
    OUTCARPARAMS = {}
    gotNELM = False
    gotNSW = False
    for line in ht.follow_file("OUTCAR", timeout=TIMEOUT, immediate_stop=True):
        line = line.rstrip()
        if "NELM   =" in line:
            nelm = int(line.split()[2].rstrip(";"))
            gotNELM = True
            OUTCARPARAMS['NELM'] = nelm
        elif "NSW    =" in line:
            nsw = int(line.split()[2])
            gotNSW = True
            OUTCARPARAMS['NSW'] = nsw
        if all((gotNELM, gotNSW)):
            OUTCARPARAMS_STOP = False
            break

    if OUTCARPARAMS_STOP:
        with open(MSGFILE, "w") as f:
            f.write("OSZICAR_CHECKER KILLED DURING OUTCARPARAMS CHECK\n")
        return 0

    with open(MSGFILE, "w") as f:
        f.write("OSZICAR_CHECKER ACTIVE WITH PARAMS: {}\n".format(OUTCARPARAMS))

    # Do not try to follow a file before there is a file to follow.
    # while not os.path.exists("OSZICAR"):
    #     time.sleep(0.1)

    RETURNCODE = 0
    istep = 0
    lastrmsc = 0.0
    lastep = False
    lastebad = False
    lastibad = False
    for line in ht.follow_file("OSZICAR", timeout=TIMEOUT):
        line = line.rstrip()
        # Changed the regex so that it matches numbers that have no whitespace between them.
        # E.g. the second line below does not match without the fix:
        # SDA:   6    -0.198310401180E+02   -0.81525E+01   -0.11482E-02  1596   0.503E+02 0.000E+00
        # CGA:   7    -0.337212707899E+02   -0.13890E+02   -0.14223E+02  1596   0.488E+01-0.322E+01
        #
        match = re.search("^[A-Za-z]+: +([0-9]+) +([-+0-9.Ee]+) +([-+0-9.Ee]+) +(-?\d\.\d{5}[Ee][+-]\d{2}) *([0-9]{1,6}) +(-?\d*\.\d*[Ee][+-]\d{2})([\s-]*[+0-9.Ee]+)", line)
        if match is not None:
            # print(match.groups(), flush=True)
            nstep = int(match.groups()[0])
            lastrmsc = float(match.groups()[5])
            continue
        match = re.search("^[A-Za-z]+: +([0-9]+) +([-+0-9.Ee]+) +([-+0-9.Ee]+) +(-?\d\.\d{5}[Ee][+-]\d{2}) *([0-9]{1,6}) +(-?\d*\.\d*[Ee][+-]\d{2})", line)
        if match is not None:
            # print(match.groups(), flush=True)
            nstep = int(match.groups()[0])
            continue
        match = re.search("^ +[0-9]+ F= ([-+0-9.Ee]+)\s+E0= ([-+0-9.Ee]+)\s+d E =([-+0-9.Ee]+)\s+mag=\s*([-+0-9.Ee]+)", line)
        if match is not None:
            istep += 1
            energy = float(match.groups()[1])
            if energy > 0:
                lastep = True
            if lastrmsc >= 0.7:
                with open(MSGFILE, "a") as f:
                    f.write("BADCONV ELEC (RMSC>=0.7)\n")
                lastebad = True
            if nstep >= nelm:
                with open(MSGFILE, "a") as f:
                    f.write("BADCONV ELEC (N>=NELM)\n")
                lastebad = True
            if nsw > 1 and istep >= nsw:
                with open(MSGFILE, "a") as f:
                    f.write("BADCONV ION (ISTEP>=NSW)\n")
                lastibad = True
            if energy < 0:
                lastep = False
            if lastebad and lastrmsc < 0.7 and nstep < nelm:
                with open(MSGFILE, "a") as f:
                    f.write("RECOVERED CONV ELEC\n")
                    lastebad = False
            if lastibad and nsw > 1 and istep < nsw:
                with open(MSGFILE, "a") as f:
                    f.write("RECOVERED CONV ION\n")
                    lastibad = False
            continue
        if "HT_TIMEOUT" in line:
            with open(MSGFILE, "a") as f:
                f.write("OSZICAR_TIMEOUT\n")
                RETURNCODE = 2
                break

    # awk END rules:
    if lastebad:
        with open(MSGFILE, "a") as f:
            f.write("LAST BADCONV ELEC\n")
        # print("LAST BADCONV ELEC", flush=True)
    if lastibad:
        with open(MSGFILE, "a") as f:
            f.write("LAST BADCONV ION\n")
        # print("LAST BADCONV ION", flush=True)
    if lastep:
        with open(MSGFILE, "a") as f:
            f.write("LAST ENERGY IS POSITIVE (E>0)\n")
        # print("LAST ENERGY IS POSITIVE (E>0)", flush=True)
        RETURNCODE = 2

    with open(MSGFILE, "a") as f:
        f.write("OSZICAR_CHECKER END\n")

    return RETURNCODE


def VASP_GET_ENERGY(FILE=None):
    if FILE is None:
        FILE = "./OSZICAR"

    with open(FILE, "r") as f:
        lines = f.read().splitlines()
    # The last energy is what we want, so reverse the file and break
    # after the first match.
    lines = reversed(lines)

    for line in lines:
        match = re.search("^ +[0-9]+ F= ([-+0-9.Ee]+)\s+E0= ([-+0-9.Ee]+)\s+d E =([-+0-9.Ee]+)\s+mag=\s*([-+0-9.Ee]+)", line)
        if match is not None:
            energy = float(match.groups()[1])
            return energy
    return None


def VASP_INPUTS_FIX_ERROR():
    #############################################
    #                                           #
    #  Assumes we are inside an atomic section  #
    #  Returns 3 for give up                    #
    #  Returns 2 for cell is too small          #
    #  Returns 0 for all is well, continue      #
    #                                           #
    #############################################

    print("========= VASP PROBLEM DETECTED ========")
    print("========== ht.controlled.msgs ==========")
    with open("../ht.controlled.msgs", "r") as f:
        lines = sorted(set(f.read().splitlines()))
    for line in lines:
        print(line)
    print("========================================")

    ANYREMEDY = 0
    RETURNCODE = 0
    # In the bash version, sometimes the REMEDY variable is used,
    # e.g., in the TOOCLOSE check even though it is not defined.
    REMEDY = ''

    if ht.find_in_file("^PRICELL.*", "../ht.controlled.msgs"):
        print("PRICELL PROBLEM DETECTED.")
        PROBLEM = "pricell"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        if REMEDYSTEP == 0:
            ANYREMEDY = 1
            REMEDY = "LOWSYMPREC"
        elif REMEDYSTEP == 1:
            ANYREMEDY = 1
            REMEDY = "HIGHSYMPREC"
        elif REMEDYSTEP == 2:
            ANYREMEDY = 1
            REMEDY = "NOSYM"
        else:
            print("GIVING UP")
            return 3
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^ZPOTRF.*", "../ht.controlled.msgs"):
        print("ZPOTRF PROBLEM DETECTED.")
        PROBLEM = "zpotrf"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0
        print("ZPOTRF REMEDYSTEP: {}".format(REMEDYSTEP))

        if REMEDYSTEP == 0:
            ANYREMEDY = 1
            RETURNCODE = 2
        elif REMEDYSTEP == 1:
            ANYREMEDY = 1
            REMEDY = "BUMP_KPTS"
        elif REMEDYSTEP == 2:
            ANYREMEDY = 1
            REMEDY = "BUMP_BANDS"
        elif REMEDYSTEP == 3:
            ANYREMEDY = 1
            REMEDY = "GAUSSMEAR"
        elif REMEDYSTEP == 4:
            ANYREMEDY = 1
            REMEDY = "NOSYM"
        else:
            print("GIVING UP")
            return 3
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^TETKPTS.*", "../ht.controlled.msgs"):
        print("PROBLEM WITH TETRAHEDRON KPOINT METHOD DETECTED")
        PROBLEM = "tetkpts"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        if REMEDYSTEP == 0:
            ANYREMEDY = 1
            REMEDY = "GAUSSMEAR"
        else:
            print("GIVING UP")
            return 3
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^ZBRENT_BRACKETING.*", "../ht.controlled.msgs"):
        print("PROBLEM WITH ZBRENT BRACKETING")
        PROBLEM = "zbrentbracketing"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        if REMEDYSTEP == 0:
            ANYREMEDY = 1
            REMEDY = "EDIFF_SMALLER"
        elif REMEDYSTEP == 1:
            ANYREMEDY = 1
            REMEDY = "EDIFF_SMALLER_2"
        else:
            # Give up!
            print("GIVING UP")
            return 3
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^REAL_OPTLAY.*", "../ht.controlled.msgs"):
        print("REAL_OPTLAY ERROR.")
        PROBLEM = "lrealoptlay"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        if REMEDYSTEP == 0:
            ANYREMEDY = 1
            REMEDY = "LREALFALSE"
        else:
            # Give up!
            print("GIVING UP")
            return 3
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^TOOCLOSE.*", "../ht.controlled.msgs"):
        print("PROBLEM: IONS TOO CLOSE.")
        PROBLEM = "tooclose"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        if 1:
            ANYREMEDY = 1
            RETURNCODE = 2
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^NONLR_ALLOC.*", "../ht.controlled.msgs"):
        print("NONLR_ALLOC PROBLEM; OFTEN LEADING TO VASP ALLOCATING ALL AVAILABLE MEMORY.")
        PROBLEM = "nonlralloc"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        # case *) is the only option.
        if 1:
            # Give up!
            print("GIVING UP")
            return 3
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    # If we didn't find anything to do, lets try this as well
    if ANYREMEDY == 0:
        ANYREMEDY = VASP_INPUTS_ADJUST()

    # If we still didn't find anything to do, we need to give up
    if ANYREMEDY == 0:
        print("UNKNOWN PROBLEM. GIVING UP.")
        return 3

    return RETURNCODE


def VASP_INPUTS_ADJUST():
    # Assumes we are inside an atomic section
    #
    print("========= VASP ADJUSTMENT BASED ON ========")
    print("============ ht.controlled.msgs ===========")
    with open("../ht.controlled.msgs", "r") as f:
        # lines = sorted(set(f.read().splitlines()))
        lines = f.read().splitlines()
    for line in lines:
        print(line)
    print("===========================================")

    ANYREMEDY = 0
    if ht.find_in_file("^KPTSCLASS.*", "../ht.controlled.msgs"):
        print("KPOINT CLASS WARNING DETECTED")
        REMEDY = ""
        PROBLEM = "kptsclass"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0
        print("KPOINT CLASS PROBLEM REMEDYSTEP: {}".format(REMEDYSTEP))

        if REMEDYSTEP == 0:
            ANYREMEDY = 1
            REMEDY = "BUMP_KPTS"
        elif REMEDYSTEP == 1:
            ANYREMEDY = 1
            REMEDY = "GAMMA_KPTS"
        elif REMEDYSTEP == 2:
            ANYREMEDY = 1
            REMEDY = "BUMP_KPTS\nGAMMA_KPTS"
        elif REMEDYSTEP == 3:
            ANYREMEDY = 1
            REMEDY = "EQUAL_KPTS"
        elif REMEDYSTEP == 4:
            ANYREMEDY = 1
            REMEDY = "BUMP_KPTS\nEQUAL_KPTS"
        elif REMEDYSTEP == 5:
            ANYREMEDY = 1
            REMEDY = "NOSYM"
        elif REMEDYSTEP == 6:
            ANYREMEDY = 1
            REMEDY = "NOSYM\nEQUAL_KPTS"
        else:
            REMEDY = "BUMP_KPTS\nEQUAL_KPTS"
            print("NO MORE IDEAS FOR {}".format(PROBLEM))
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^DENTET.*", "../ht.controlled.msgs"):
        print("DENTET WARNING DETECTED", flush=True)
        REMEDY = ""
        PROBLEM = "dentet"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        if REMEDYSTEP == 0:
            ANYREMEDY = 1
            REMEDY = "GAUSSMEAR"
        elif REMEDYSTEP == 1:
            ANYREMEDY = 1
            REMEDY = "BUMP_KPTS"
        elif REMEDYSTEP == 2:
            ANYREMEDY = 1
            REMEDY = "BUMP_KPTS\nGAMMA_KPTS"
        elif REMEDYSTEP == 3:
            ANYREMEDY = 1
            REMEDY = "BUMP_NEDOS"
        else:
            REMEDY = "BUMP_NEDOS"
            print("NO MORE IDEAS FOR {}".format(PROBLEM))
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^SHIFTS.*", "../ht.controlled.msgs"):
        print("COULD NOT GET CORRECT SHIFTS WARNING")
        REMEDY = ""
        PROBLEM = "shifts"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        if REMEDYSTEP == 0:
            ANYREMEDY = 1
            REMEDY = "GAMMA_KPTS"
        else:
            REMEDY = "GAMMA_KPTS"
            print("NO MORE IDEAS FOR {}".format(PROBLEM))
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^LREALFALSE.*", "../ht.controlled.msgs"):
        print("VASP ASKS TO BE RESTARTED WITH LREAL=.FALSE.")
        REMEDY = ""
        PROBLEM = "lreal"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        if REMEDYSTEP == 0:
            ANYREMEDY = 1
            REMEDY = "LREALFALSE"
        else:
            REMEDY = "LREALFALSE"
            print("NO MORE IDEAS FOR {}".format(PROBLEM))
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^INVROTMATRIX.*", "../ht.controlled.msgs"):
        print("PROBLEM WITH FINDING INVERESE ROTATION MATRIX WARNING")
        REMEDY = ""
        PROBLEM = "tetkpts"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        if REMEDYSTEP == 0:
            ANYREMEDY = 1
            REMEDY = "NOSYM"
        else:
            REMEDY = "NOSYM"
            print("NO MORE IDEAS FOR {}".format(PROBLEM))
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^LAST BADCONV ION", "../ht.controlled.msgs"):
        print("PROBLEM: BAD ION RELAXATION CONVERGENCE.")
        REMEDY = ""
        PROBLEM = "ionrelax"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        if REMEDYSTEP == 0:
            if ht.find_in_file("^FINISHED.*", "../ht.controlled.msgs"):
                print("RETRYING RELAXATION STEP, STARTING FROM LAST POSITION")
                ht.cp("../CONTCAR", "POSCAR")
                ANYREMEDY = 1
            else:
                # Give up!
                print("RUN DID NOT FINISH, SO, NO CONTCAR TO CONTINUE FROM")
                print("NO MORE IDEAS FOR {}".format(PROBLEM))
        else:
            print("NO MORE IDEAS FOR {}".format(PROBLEM))
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    if ht.find_in_file("^LAST BADCONV ELEC", "../ht.controlled.msgs") or \
       ht.find_in_file("^FEXCF", "../ht.controlled.msgs"):
        print("PROBLEM: BAD ELECTRONIC RELAXATION CONVERGENCE.")
        REMEDY = ""
        PROBLEM = "elecrelax"
        remedy_file = "../ht.remedy.{}".format(PROBLEM)
        if os.path.exists(remedy_file):
            with open(remedy_file, "r") as f:
                REMEDYSTEP = int(f.readline().rstrip())
            REMEDYSTEP += 1
        else:
            REMEDYSTEP = 0

        if REMEDYSTEP == 0:
            ANYREMEDY = 1
            REMEDY = "SOFTMIX"
        elif REMEDYSTEP == 1:
            ANYREMEDY = 1
            REMEDY = "SOFTMIX2"
        elif REMEDYSTEP == 2:
            ANYREMEDY = 1
            REMEDY = "ALGOALL"
        elif REMEDYSTEP == 3:
            ANYREMEDY = 1
            REMEDY = "ALGOALL2"
        elif REMEDYSTEP == 4:
            ANYREMEDY = 1
            REMEDY = "ALGODAMPED"
        else:
            REMEDY = "ALGODAMPED"
            print("NO MORE IDEAS FOR {}".format(PROBLEM))
        with open(remedy_file, "w") as f:
            f.write("{}\n{}\n".format(REMEDYSTEP, REMEDY))

    return ANYREMEDY


# Vasp cuts the first line in the CONTCAR, this fixes that problem
def VASP_CONTCAR_TO_POSCAR(CONTCAR=None, REFPOSCAR=None):
    if CONTCAR is None:
        CONTCAR = "CONTCAR"
    if REFPOSCAR is None:
        REFPOSCAR = "POSCAR"

    with open(REFPOSCAR, "r") as f:
        FIRSTLINE = f.readline()

    with open("POSCAR", "w") as f_dest:
        with open(CONTCAR, "r") as f_src:
            for i, line in enumerate(f_src):
                if i == 0:
                    f_dest.write(FIRSTLINE)
                else:
                    f_dest.write(line)
