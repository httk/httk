from httk.core import *
import httk.httkio
from httk.atomistic.simplestructureutils import convert_to_simplestruct
files = ["../../Tutorial/Step2/POSCAR2"]

for i in range(len(files)):
    filename = files[i]
    struct = httk.load(filename)
    simple_struct = convert_to_simplestruct(struct)