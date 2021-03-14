import sys
import numpy as np
import pymatgen as pmg
from pymatgen.io.vasp import Poscar
from pymatgen.core.lattice import Lattice
from utilities import (elastic_config, rotation_matrix,
                       get_dist_matrix, distort)


dist_ind = int(sys.argv[1]) - 1
delta_ind = int(sys.argv[2]) - 1
sym, delta, distortions, project = elastic_config()
d = delta[dist_ind][delta_ind]

# epsilon_array is the distortion in Voigt notation
epsilon_array = np.array(distortions[dist_ind]) * d
dist_matrix = get_dist_matrix(epsilon_array)

struct = pmg.Structure.from_file("POSCAR")
struct.lattice = Lattice(distort(dist_matrix, struct._lattice.matrix))

poscar = Poscar(struct)
poscar.write_file("POSCAR", significant_figures=8)
