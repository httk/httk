import os
import httk
import httk.atomistic.pathfinderprog as pf
from httk.atomistic.simplestructureutils import convert_to_simplestruct
from httk.atomistic.symmetrystructureutils import generate_interpolation

start_file = os.path.join("Tutorial", "pathfinder_data", "UGePt_62.poscar")
end_file = os.path.join("Tutorial", "pathfinder_data", "UGePt_44.poscar")

start_struct = httk.load(start_file)
end_struct = httk.load(end_file)

start_simple = convert_to_simplestruct(start_struct)
end_simple = convert_to_simplestruct(end_struct)

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

prefix_str, paths=pf.get_paths(start_simple, end_simple, search_depth, symprec, sub_type, max_path, max_orig, max_results, steps, subgroups, collision_threshold, collision_level)
print(prefix_str)
for path in paths:
    # Generate extra interpolation, now ignoring collisions and with more interpolated structures
    generate_interpolation(path, steps=20, collision_threshold=collision_threshold, collision_level=0)
    print(path)
