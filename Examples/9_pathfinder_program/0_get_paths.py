import os
import httk
import httk.atomistic.pathfinderprog as pf
from httk.atomistic.simplestructureutils import convert_to_simplestruct

start_file = os.path.join("Tutorial", "pathfinder_data", "UGePt_62.poscar")
end_file = os.path.join("Tutorial", "pathfinder_data", "UGePt_44.poscar")

# Load example files
start_struct = httk.load(start_file)
end_struct = httk.load(end_file)

# Convert to new SimpleStruct object
start_simple = convert_to_simplestruct(start_struct)
end_simple = convert_to_simplestruct(end_struct)

search_depth = 6 # Maximal depth of the trees generated for subgroup search
symprec = 1e-05 # Symmetry precision used by spglib
sub_type = ["t","k"] # Type of subgroups to limit search to
max_path = 9999 # Maximal number of atoms for a subgroup structure
max_orig = 999 # Maximal number of atoms for an input structure
max_results = 1 # Maximal number of paths generated
steps = 10 # Number of interpolation steps
subgroups = ["any"] # Limit subgroups for paths
collision_threshold = 0.1 # Distance between atoms for program to deem it a collision
collision_level = 2 # Level of collision detection: 0 = ignore, 1 = calculate but don't adjust interpolated structures, 2 = calculate and try to adjust interpolated structures

prefix_str, paths=pf.get_paths(start_simple, end_simple, search_depth, symprec, sub_type, max_path, max_orig, max_results, steps, subgroups, collision_threshold, collision_level)
print(prefix_str)
i = 0
while i < len(paths):
    print(paths[i])
    paths[i].write_to_folder(prefix=prefix_str, folder_name="path_example_"+str(i))
    i += 1