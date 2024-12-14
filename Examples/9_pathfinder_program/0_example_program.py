import os, sys
PATH_TO_HTTK = "G:\\amanuens_HT24\\httk-2-testing\\src"
sys.path.insert(1, PATH_TO_HTTK)
PATH_TO_HTTK = "~/Dokument/amanuens_HT24/httk-2-testing/src"
sys.path.insert(1, os.path.expanduser(PATH_TO_HTTK))
import httk
import httk.atomistic.pathfinderprog as pf
from httk.atomistic.simplestructureutils import convert_to_simplestruct
from httk.atomistic.symmetrystructureutils import create_from_simple_struct, create_lower_symmetry_copy
from httk.core import *

start_file = os.path.join("Tutorial", "pathfinder_data", "UGePt_62.poscar")
end_file = os.path.join("Tutorial", "pathfinder_data", "UGePt_44.poscar")

start_struct = httk.load(start_file)
end_struct = httk.load(end_file)

start_simple = convert_to_simplestruct(start_struct)
end_simple = convert_to_simplestruct(end_struct)

start_sym = create_from_simple_struct(start_simple, 1e-05)
start_sym_lower = create_lower_symmetry_copy(start_sym, 31)
#print(start_sym)
#print(start_sym._wyckoffs)
#print(start_sym_lower)
# parameters
search_depth = 6
symprec = 1e-05
sub_type = ["t","k"]
max_path = 99999
max_orig = 999
max_results = 1
steps = 10
subgroups = ["any"]
collision_threshold = 0.1
collision_level = 2

prefix_str, start_orig, end_orig, paths=pf.get_paths(start_simple, end_simple, search_depth, symprec, sub_type, max_path, max_orig, max_results, steps, subgroups, collision_threshold, collision_level)
print(prefix_str)
print(start_orig)
print(end_orig)
for path in paths:
    print(path)
