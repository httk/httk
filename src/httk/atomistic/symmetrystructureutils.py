from httk.atomistic.symmetrystructure import SymmetryStructure
import numpy as np
import spglib, json, sys
from os.path import join, dirname, abspath
from httk.atomistic.data.symmetry_wyckoff import Spacegroup
import httk.atomistic.data.bilbaoDatasetAPI as bilbaoAPI
from diffpy.structure.lattice import Lattice
from ase.neighborlist import primitive_neighbor_list
from httk.atomistic.symmetrypath import SymmetryPath
from httk.atomistic.interpolation import Interpolation

with open(join(dirname(abspath(__file__)), "data", "spglib_standard_hall.json"), "r") as f:
    spglib_hall_nums = json.load(f)
def create_from_simple_struct(simple_struct, symprec_val):
    lattice = simple_struct._cell_lattice_vectors
    positions = simple_struct._sites_fractional
    numbers = simple_struct._species_sites_numbers
    cell = (lattice, positions, numbers)
    dataset = spglib.get_symmetry_dataset(cell, symprec=symprec_val)
    if str(dataset["number"]) in spglib_hall_nums:
        hall_num = spglib_hall_nums[str(dataset["number"])]
    else:
        hall_num = 0
    new_struct = (dataset["std_lattice"], dataset["std_positions"], dataset["std_types"])
    dataset2 = spglib.get_symmetry_dataset(new_struct, symprec=symprec_val, hall_number=hall_num)
    new_struct2 = (dataset2["std_lattice"], dataset2["std_positions"], dataset2["std_types"])
    dataset3 = spglib.get_symmetry_dataset(new_struct2, symprec=symprec_val, hall_number=hall_num)
    new_wyckoff = calc_wyckoff_basis_coords(new_struct2,
                                                    dataset3["wyckoffs"],
                                                    dataset3["equivalent_atoms"],
                                                    dataset3["number"])
    if len(new_wyckoff) == 0:
        print("Could not identify any wyckoff orbits.")
        sys.exit()
    num_of_atoms = len(dataset3["std_positions"])
    new_species_sites = get_species_sites_from_numbers(simple_struct, dataset2["std_types"])
    return SymmetryStructure(cell_lattice_vectors=dataset2["std_lattice"],
                             cell_parameters=None,
                             cell_niggli=None,
                             cell_metric=None,
                             scale=1,
                             sites_fractional=dataset2["std_positions"],
                             sites_cartesian=None,
                             species=simple_struct.get_species_copy(),
                             species_sites=new_species_sites,
                             species_sites_numbers=dataset2["std_types"],
                             wyckoffs=new_wyckoff,
                             space_number=dataset3["number"],
                             num_of_atoms=num_of_atoms)

def calc_wyckoff_basis_coords(struct, wyckoffs, equivalent, space_group):
    """Identify the Wyckoff orbits and find suitable values for degrees of freedom.

    Args:
        struct (list): list or tuple with lattice, positions and atom numbers.
        wyckoffs (list): list of Wyckoff letters corresponding to the letter of each position.
        equivalent (list): list of numbers corresponding to the Wyckoff orbit of each position.
        space_group (int): Space group number of structure.
    
    Returns:
        list: list of dictionaries describing each Wyckoff position. Each dictionary contains
            atom - atom number.
            multiplicity - number of atoms in the Wyckoff orbit.
            letter - The Wyckoff letter.
            basis - Set of values for the degrees of freedom.
            freedom_degr - The degrees of freedom, which axes can be changed.
    """
    # Generate wyckoff orbits of subgroup
    new_wyckoff = []
    s = Spacegroup(space_group)
    for orbit_id in set(equivalent):
        multiplicity = np.count_nonzero(equivalent == orbit_id)
        coords = [struct[1][i] for i in np.where(equivalent == orbit_id)[0]]
        wyck_letter = wyckoffs[np.where(equivalent == orbit_id)[0][0]]
        atom_num = struct[2][np.where(equivalent == orbit_id)[0][0]]
        try:
            degr_freedom = repr(s[wyck_letter])
        except Exception as e:
            print(e)
            print(space_group)
            print(wyckoffs)
            print(equivalent)
            sys.exit()
        degr_freedom = degr_freedom[degr_freedom.find("["):]
        degr_freedom = [x.strip() == "True" for x in degr_freedom.strip("[]").split(",")]
        final_coord = None
        got_final_coord = False
        for coordinate in coords:
            calc_pos = np.mod(s[wyck_letter].affinedot(coordinate), 1.0)
            if compare_list_of_coords(coords, calc_pos):
                final_coord = calc_pos[0]
                got_final_coord = True
                break
        if got_final_coord:
            new_wyckoff.append({"atom": atom_num,
                                "multiplicity": multiplicity,
                                "letter": wyck_letter,
                                "basis": final_coord,
                                "freedom_degr": degr_freedom})
    new_wyckoff.sort(key=lambda a: "{atom:03d}+{l}".format(l=a["letter"], atom=a["atom"]))
    i = 0
    while i < len(new_wyckoff):
        new_wyckoff[i]["id"] = i
        i += 1
    return new_wyckoff

def compare_list_of_coords(list_1, list_2):
    found_match = True
    for pos_1 in list_1:
        found_match = False
        for pos_2 in list_2:
            if (np.round(pos_1, 8) == np.round(pos_2, 8)).all():
                found_match = True
                break
        if not found_match:
            break
    return found_match

def create_lower_symmetry_copy(sym_struct, new_space_number, transformation_info=None, size_increase=None, transformation_id=None):
    if transformation_info is None:
        subgroup_info = bilbaoAPI.get_max_subgroups(sym_struct._space_number, subgroup_restriction=[new_space_number])
        chosen_size_increase = 999999
        chosen_id = ""
        for info in subgroup_info:
            if size_increase:
                if int(info["size_increase"]) == int(size_increase):
                    chosen_size_increase = info["size_increase"]
                    chosen_id = info["id"]
                    break
            elif transformation_id:
                if info["id"] == transformation_id:
                    chosen_size_increase = info["size_increase"]
                    chosen_id = info["id"]
                    break
            else:
                if int(info["size_increase"]) < int(chosen_size_increase):
                    chosen_size_increase = info["size_increase"]
                    chosen_id = info["id"]
        transformation_info = bilbaoAPI.get_best_trans_matrix(sym_struct._space_number, chosen_id)
        transformation_info["size_increase"] = chosen_size_increase
    new_wyckoffs = get_next_wyckoffs(new_space_number, sym_struct._wyckoffs, transformation_info["wp_splitting"])
    new_lattice = np.matmul(np.array([x[0:3] for x in transformation_info["trans_matrix"][0:3]]).T, np.array(sym_struct._cell_lattice_vectors)).tolist()
    new_positions = []
    new_numbers = []
    for wyckoff in new_wyckoffs:
        pos, num = get_pos_from_wyckoff(new_space_number, wyckoff)
        new_positions += list(pos)
        new_numbers += list(num)
    new_species_sites = get_species_sites_from_numbers(sym_struct, new_numbers)
    new_num_of_atoms = sym_struct._num_of_atoms*transformation_info["size_increase"]
    new_cart_positions = fractional_to_cartesian(new_lattice, new_positions)
    return SymmetryStructure(cell_lattice_vectors=new_lattice,
                             cell_parameters=None,
                             cell_niggli=None,
                             cell_metric=None,
                             scale=1,
                             sites_fractional=new_positions,
                             sites_cartesian=new_cart_positions,
                             species=sym_struct.get_species_copy(),
                             species_sites=new_species_sites,
                             species_sites_numbers=new_numbers,
                             wyckoffs=new_wyckoffs,
                             space_number=new_space_number,
                             num_of_atoms=new_num_of_atoms)

def create_from_wyckoffs(lattice, space_number, wyckoffs, species=None):
    positions = []
    numbers = []
    for wyckoff in wyckoffs:
        pos, num = get_pos_from_wyckoff(space_number, wyckoff)
        positions += list(pos)
        numbers += list(num)
    num_of_atoms = len(numbers)
    cart_pos = fractional_to_cartesian(lattice, positions)
    return SymmetryStructure(cell_lattice_vectors=lattice,
                             cell_parameters=None,
                             cell_niggli=None,
                             cell_metric=None,
                             scale=1,
                             sites_fractional=positions,
                             sites_cartesian=cart_pos,
                             species=species,
                             species_sites=None,
                             species_sites_numbers=numbers,
                             wyckoffs=wyckoffs,
                             space_number=space_number,
                             num_of_atoms=num_of_atoms)

def get_next_wyckoffs(next_space_group, curr_wyckoffs, wp_splitting):
    """Get new Wyckoff positions and calculate the new values for the degrees of freedom.
    
    Args:
        next_space_group (int): Space group number for subgroup structure.
        curr_wyckoffs (list): List of Wyckoff orbits for current structure.
        wp_splitting (list): Excerpt from MAXSUB database containing the Wyckoff splitting information for group-subgroup transformation.
    
    Returns:
        list: List of Wyckoff orbits for the subgroup structure. Same data layout as curr_wyckoffs.
    """
    next_wyckoffs = []
    s = Spacegroup(next_space_group)
    for elem in curr_wyckoffs:
        wp_splitting_info = get_orbits(wp_splitting, elem["letter"])
        new_basis_pos = None
        i = 0
        while i < len(wp_splitting_info["orbits"]):
            if wp_splitting_info["orbits"][i]["new_basis"]:
                new_basis_pos = calc_new_wyckoff_pos(elem["basis"], wp_splitting_info["orbits"][i]["subgroup_basis"])
            if i == len(wp_splitting_info["orbits"]) - 1:
                wyck_letter = wp_splitting_info["orbits"][i]["name"].split("_")[0][-1]
                degr_freedom = repr(s[wyck_letter])
                degr_freedom = degr_freedom[degr_freedom.find("["):]
                degr_freedom = [x.strip() == "True" for x in degr_freedom.strip("[]").split(",")]
                next_wyckoffs.append({"atom": elem["atom"], "letter": wyck_letter, "basis": new_basis_pos, "multiplicity": int(wp_splitting_info["orbits"][i]["name"].split("_")[0][:-1]), "freedom_degr": degr_freedom})
            elif wp_splitting_info["orbits"][i + 1]["name"] != wp_splitting_info["orbits"][i]["name"]:
                wyck_letter = wp_splitting_info["orbits"][i]["name"].split("_")[0][-1]
                degr_freedom = repr(s[wyck_letter])
                degr_freedom = degr_freedom[degr_freedom.find("["):]
                degr_freedom = [x.strip() == "True" for x in degr_freedom.strip("[]").split(",")]
                next_wyckoffs.append({"atom": elem["atom"], "letter": wyck_letter, "basis": new_basis_pos, "multiplicity": int(wp_splitting_info["orbits"][i]["name"].split("_")[0][:-1]), "freedom_degr": degr_freedom})
            i += 1
    next_wyckoffs.sort(key=lambda a: "{atom:03d}+{l}".format(l=a["letter"], atom=a["atom"]))
    i = 0
    while i < len(next_wyckoffs):
        next_wyckoffs[i]["id"] = i
        i += 1
    return next_wyckoffs

def get_orbits(wyckoffs, wyckoff_letter):
    """Get orbits for specific Wyckoff splitting.
    
    Args:
        wyckoffs (list): List of Wyckoff splittings. Excerpt from MAXSUB database.
        wyckoff_letter: Wyckoff letter of current Wyckoff position to be split.
    """
    for wyckoff in wyckoffs:
        if wyckoff_letter in wyckoff["group"]:
            return wyckoff

def calc_new_wyckoff_pos(group_values, subgroup_formula):
    """Calculate values of formulas given input values.

    Args:
        group_values (list): list of input values for x, y and z.
        subgroup_formula (str): string describing the formulas to be calculated. In the form (f1(x,y,z), f2(x,y,z), f3(x,y,z)).

    Returns:
        list: the three calculated values, moved to the unit cell and rounded to 8 decimals.
    """
    var_dict = {"x": group_values[0], "y": group_values[1], "z": group_values[2]}
    subgroup_formula = subgroup_formula[1:-1].split(",")
    position = [eval(subgroup_formula[i], var_dict) for i in range(0, 3)]
    return np.round([i - np.floor(i) for i in position], 8)

def get_pos_from_wyckoff(space_group, wyckoff_info, other_basis=None, move_to_unit=True):
    s = Spacegroup(space_group)
    if other_basis is not None:
        if move_to_unit:
            positions = np.mod(np.round(s[wyckoff_info["letter"]].affinedot(other_basis), 8), 1.0)
        else:
            positions = np.round(s[wyckoff_info["letter"]].affinedot(other_basis), 8)
    else:
        if move_to_unit:
            positions = np.mod(np.round(s[wyckoff_info["letter"]].affinedot(wyckoff_info["basis"]), 8), 1.0)
        else:
            positions = np.round(s[wyckoff_info["letter"]].affinedot(wyckoff_info["basis"]), 8)
    if "atom" in wyckoff_info:
        atoms = [wyckoff_info["atom"]] * len(positions)
        return positions, atoms
    else:
        return positions

def get_species_sites_from_numbers(sym_struct, new_numbers=None):
    species_sites = []
    atom_nums_to_symbols = dict(zip([str(x["atomic_numbers"][0]) for x in sym_struct._species], [x["chemical_symbols"][0] for x in sym_struct._species]))
    numbers = new_numbers if new_numbers is not None else sym_struct._species_sites_numbers
    for atom_num in numbers:
        species_sites.append(atom_nums_to_symbols[str(atom_num)])
    return species_sites

def get_numbers_from_species_sites(sym_struct, new_species_sites=None):
    species_sites_numbers = []
    atom_symbols_to_nums = dict(zip([x["chemical_symbols"][0] for x in sym_struct._species], [x["atomic_numbers"][0] for x in sym_struct._species]))
    species_sites = new_species_sites if new_species_sites is not None else sym_struct._species_sites
    for atom_symbol in species_sites:
        species_sites_numbers.append(atom_symbols_to_nums[str(atom_symbol)])
    return species_sites_numbers

def compare_wyckoffs(struct1, struct2):
    """Compare two sets of wyckoff orbits, return True if they have the same sets of letters and atoms."""
    if len(struct1._wyckoffs) == len(struct2._wyckoffs):
        struct1._wyckoffs.sort(key=lambda a: a["letter"] + str(a["atom"]))
        struct2._wyckoffs.sort(key=lambda a: a["letter"] + str(a["atom"]))
        i = 0
        while i < len(struct1._wyckoffs):
            if (struct1._wyckoffs[i]["atom"] != struct2._wyckoffs[i]["atom"]) or (struct1._wyckoffs[i]["letter"] != struct2._wyckoffs[i]["letter"]):
                return False
            i += 1
        return True
    return False

def check_path_compatibility(struct1, struct2, max_orig):
    """Check if two structures are compatible and have the same stochiometry.

    Args:
        f1_info (dict): Info about starting structure.
        f2_info (dict): Info about ending structure.
        max_orig (int): Maximum number of atoms allowed in provided structures.

    Returns:
        str: Formula describing atomic composition, returned if the two structures match.
    """

    if struct1._num_of_atoms > max_orig:
        print("Start point structure is too large: " + str(struct1._num_of_atoms) + " > " + str(max_orig))
        sys.exit(0)
    if struct2._num_of_atoms > max_orig:
        print("End point structure is too large: " + str(struct2._num_of_atoms) + " > " + str(max_orig))
        sys.exit(0)
    if struct1._space_number == struct2._space_number and compare_wyckoffs(struct1._wyckoffs, struct2._wyckoffs):
        print("Structures are identical")
    if len(set(struct1._species_sites_numbers)) != len(set(struct2._species_sites_numbers)):
        print("Structures' atomic composition does not match")
        sys.exit(0)
    for atom in set(struct1._species_sites_numbers):
        if atom not in struct2._species_sites_numbers:
            print("Structures' atomic composition does not match")
            sys.exit(0)
    if struct1.get_atomic_formula(reduced=True, ones=True, sorted=True) != struct2.get_atomic_formula(reduced=True, ones=True, sorted=True):
        print("Structures' atomic composition does not match")
        sys.exit(0)
    return struct1.get_atomic_formula(reduced=True, ones=False, sorted=True)

def generate_interpolation(sym_path, steps, collision_threshold, collision_level):
    wyckoffs1 = sym_path._start_common_struct._wyckoffs
    wyckoffs2 = sym_path._end_common_struct._wyckoffs
    complete_structures = []
    done_atom_letter = []
    pair_dict = {}
    interpolated_matrices = get_interpolated_matrices(sym_path._start_common_struct, sym_path._end_common_struct, steps)
    total_dist = 0
    i = 0
    while i < len(wyckoffs1):
        if str(wyckoffs1[i]["atom"]) + wyckoffs1[i]["letter"] not in done_atom_letter:
            curr_wyckoffs_1 = [x for x in wyckoffs1 if str(x["atom"]) + x["letter"] == str(wyckoffs1[i]["atom"]) + wyckoffs1[i]["letter"]]
            curr_wyckoffs_2 = [x for x in wyckoffs2 if str(x["atom"]) + x["letter"] == str(wyckoffs1[i]["atom"]) + wyckoffs1[i]["letter"]]
            pair_dict_add, corr_msg_list, part_dist = get_best_vector_pairs(sym_path._start_common_struct, sym_path._end_common_struct, curr_wyckoffs_1, curr_wyckoffs_2, sym_path._common_subgroup_number, interpolated_matrices, steps, collision_threshold, collision_level)
            total_dist += part_dist
            pair_dict.update(pair_dict_add)
            done_atom_letter.append(str(wyckoffs1[i]["atom"]) + wyckoffs1[i]["letter"])
        i += 1
    interpolated_wyckoffs = {}
    for pair, pair_info in pair_dict.items():
        #degr_free = wyckoffs1[pair[0]]["freedom_degr"]
        wyckoffs2[pair[1]]["basis"] = pair_info[4]
        interpolated_basis = interpolate_between_coords(wyckoffs1[pair[0]]["basis"], wyckoffs2[pair[1]]["basis"], steps)
        i = 0
        while i < steps:
            new_wyckoff = copy_wyckoff(wyckoffs1[pair[0]])
            new_wyckoff["basis"] = interpolated_basis[i]
            if i in interpolated_wyckoffs:
                interpolated_wyckoffs[i].append(new_wyckoff)
            else:
                interpolated_wyckoffs[i] = [new_wyckoff]
            i += 1
    i = 0
    while i < steps:
        interpolated_struct = create_from_wyckoffs(lattice=interpolated_matrices[i], space_number=sym_path._common_subgroup_number, wyckoffs=interpolated_wyckoffs[i])
        complete_structures.append(interpolated_struct)
        i += 1
    if collision_level > 0:
        i = 0
        while i < steps:
            if check_collision_in_pos_ase(np.array(complete_structures[i]._sites_fractional), collision_threshold, np.array(complete_structures[i]._cell_lattice_vectors)):
                corr_msg_list.append(str(i))
            i += 1
    dist_per_atom = total_dist/complete_structures[0]._num_of_atoms
    interpolation_obj = Interpolation(space_number=sym_path._common_subgroup_number,
                         collision_detection_level=collision_level,
                         structs_with_collision=corr_msg_list,
                         interpolated_structs=complete_structures,
                         dist_per_atom=dist_per_atom,
                         total_dist=total_dist)
    sym_path._interpolations.append(interpolation_obj)

def interpolate_between_coords(start_pos, end_pos, steps):
    return [np.array(start_pos) + (np.array(end_pos) - np.array(start_pos)) * i * (1 / (steps + 1)) for i in range(1, steps + 1)]

def lattice_matrix_to_parameters(matrix):
    lattice_obj = Lattice(base=matrix)
    return lattice_obj.abcABG()

def lattice_parameters_to_matrix(parameter_list):
    lattice_obj = Lattice(a=parameter_list[0], b=parameter_list[1], c=parameter_list[2], alpha=parameter_list[3], beta=parameter_list[4], gamma=parameter_list[5])
    return lattice_obj.base

def fractional_to_cartesian(lattice, coords):
    if type(coords) == list:
        coords = np.array(coords)
    if type(lattice) == list:
        lattice = np.array(lattice)
    return (lattice.T @ coords.T).T

def copy_wyckoff(wyckoff):
    new_wyckoff = {}
    for key, val in wyckoff.items():
        if key == "freedom_degr":
            new_wyckoff[key] = []
            for x in wyckoff["freedom_degr"]:
                new_wyckoff[key].append(x)
        elif key == "basis":
            new_wyckoff[key] = []
            for x in wyckoff["basis"]:
                new_wyckoff[key].append(x)
        else:
            new_wyckoff[key] = val
    return new_wyckoff

def get_interpolated_matrices(start_struct, end_struct, steps):
    start_parameters = lattice_matrix_to_parameters(start_struct._cell_lattice_vectors)
    end_parameters = lattice_matrix_to_parameters(end_struct._cell_lattice_vectors)
    intermediate_parameters = interpolate_between_coords(start_parameters, end_parameters, steps)
    matrices = [lattice_parameters_to_matrix(x) for x in intermediate_parameters]
    return matrices

def get_best_vector_pairs(start_struct, end_struct, curr_wyckoffs_start, curr_wyckoffs_end, space_group, matrices, steps, collision_threshold, collision_level):
    start_matrix = start_struct._cell_lattice_vectors
    end_matrix = end_struct._cell_lattice_vectors
    result_list = {}
    distances = {}
    dist_list = []
    coll_msg = []
    i = 0
    while i < len(curr_wyckoffs_start):
        j = 0
        while j < len(curr_wyckoffs_end):
            wyckoff2_pos, wyckoff2_atoms = get_pos_from_wyckoff(space_group, curr_wyckoffs_end[j])
            possible_free_degr = []
            for pos in wyckoff2_pos:
                pos_works = True
                for k in range(0, 3):
                    if not curr_wyckoffs_end[j]["freedom_degr"][k]:
                        if np.round(curr_wyckoffs_end[j]["basis"][k], 8) != np.round(pos[k], 8):
                            pos_works = False
                if pos_works:
                    candidate_pos, temp_atoms = get_pos_from_wyckoff(space_group, curr_wyckoffs_end[j], pos)
                    if compare_list_of_coords(wyckoff2_pos, candidate_pos):
                        possible_free_degr.append(pos)
            for possible_val in possible_free_degr:
                dist, new_end, coll_warning = calc_dist_with_boundary(curr_wyckoffs_start[i]["basis"], possible_val, curr_wyckoffs_start[i]["freedom_degr"], space_group, curr_wyckoffs_start[i]["letter"], matrices, steps, collision_threshold, collision_level, start_matrix, end_matrix, (curr_wyckoffs_start[i]["id"], curr_wyckoffs_end[j]["id"]))
                if coll_warning:
                    coll_msg.append(coll_warning)
                distances[(curr_wyckoffs_start[i]["id"], curr_wyckoffs_end[j]["id"])] = [dist, curr_wyckoffs_start[i]["id"], curr_wyckoffs_end[j]["id"], curr_wyckoffs_start[i]["basis"], new_end, curr_wyckoffs_start[i]]
                dist_list.append([dist, curr_wyckoffs_start[i]["id"], curr_wyckoffs_end[j]["id"], curr_wyckoffs_start[i]["basis"], new_end, curr_wyckoffs_start[i]])
            j += 1
        i += 1
    dist_list.sort(key=lambda x: x[0])
    # get optimal pairs
    for dist_info in dist_list:
        if (dist_info[1] not in [x[0] for x in list(result_list.keys())]) and (dist_info[2] not in [x[1] for x in list(result_list.keys())]):
            result_list[(dist_info[1], dist_info[2])] = dist_info
    # avoid collisions
    if collision_level > 0:
        for k in range(0, 5):
            key_list = list(result_list.keys())
            already_switched = []
            i = 0
            while i < len(key_list):
                j = i + 1
                while j < len(key_list):
                    if i not in already_switched and j not in already_switched:
                        start1_cart = fractional_to_cartesian(start_matrix, result_list[key_list[i]][3])
                        start2_cart = fractional_to_cartesian(start_matrix, result_list[key_list[j]][3])
                        end1_cart = fractional_to_cartesian(end_matrix, result_list[key_list[i]][4])
                        end2_cart = fractional_to_cartesian(end_matrix, result_list[key_list[j]][4])
                        collision_bool = check_if_vectors_get_close(start1_cart,
                                                                            end1_cart,
                                                                            start2_cart,
                                                                            end2_cart,
                                                                            collision_threshold)
                        if collision_bool:
                            coll_msg.append(str(key_list[i]) + "; " + str(key_list[j]))
                            if collision_level == 2:
                                already_switched.append(i)
                                already_switched.append(j)
                                new_pair_1 = (key_list[i][0], key_list[j][1])
                                new_pair_2 = (key_list[j][0], key_list[i][1])
                                del result_list[key_list[i]]
                                del result_list[key_list[j]]
                                result_list[new_pair_1] = distances[new_pair_1]
                                result_list[new_pair_2] = distances[new_pair_2]
                    j += 1
                i += 1
    total_dist = 0
    for key, val in result_list.items():
        total_dist += val[0]
    return result_list, coll_msg, total_dist

def check_collision_in_pos_ase(positions, coll_dist, lattice=[[1, 0, 0], [0, 1, 0], [0, 0, 1]]):
    neighbor_list = primitive_neighbor_list("ijd", [True, True, True], lattice, positions, coll_dist, numbers=None, self_interaction=False, use_scaled_positions=False, max_nbins=1000)
    return len(neighbor_list[0]) > 0

def check_collision_between_coords(start_pos, end_pos, space_group, letter, matrices, steps, coll_threshold):
    interpolated_coords = interpolate_between_coords(start_pos, end_pos, steps)
    frac_positions = [get_pos_from_wyckoff(space_group, {"letter": letter}, x) for x in interpolated_coords]
    cart_positions = [fractional_to_cartesian(matrices[i], frac_positions[i]) for i in range(0, steps)]
    for struct_pos in cart_positions:
        if check_collision_in_pos_ase(struct_pos, coll_threshold):
            return True
    return False

def calc_dist_between_set_of_coords(start_pos, end_pos, space_group, letter, start_matrix, end_matrix):
    start_positions = fractional_to_cartesian(start_matrix, get_pos_from_wyckoff(space_group, {"letter": letter}, start_pos, False))
    end_positions = fractional_to_cartesian(end_matrix, get_pos_from_wyckoff(space_group, {"letter": letter}, end_pos, False))
    total_dist = 0
    i = 0
    while i < len(start_positions):
        total_dist += np.linalg.norm(start_positions[i] - end_positions[i])
        i += 1
    return total_dist

def calc_dist_with_boundary(start_pos, end_pos, free_degr, space_group, letter, matrices, steps, coll_threshold, coll_level, start_matrix, end_matrix, wyckoff_ids):
    if type(start_pos) == list:
        start_pos = np.array(start_pos)
    if type(end_pos) == list:
        end_pos = np.array(end_pos)
    pos_to_compare = [end_pos]
    coll_msg = None
    for i in range(0, 3):
        if free_degr[i]:
            temp_array = [1 if x == i else 0 for x in range(0, 3)]
            j = 0
            curr_len = len(pos_to_compare)
            while j < curr_len:
                pos_to_compare.append(pos_to_compare[j] + temp_array)
                pos_to_compare.append(pos_to_compare[j] - temp_array)
                j += 1
    shortest_dist = 99999
    return_pos = None
    for pos in pos_to_compare:
        if coll_level > 0:
            coll_comp = check_collision_between_coords(start_pos, pos, space_group, letter, matrices, steps, coll_threshold)
            if coll_comp:
                coll_msg = str(wyckoff_ids)
            if (not coll_comp) or coll_level == 1:
                dist = calc_dist_between_set_of_coords(start_pos, pos, space_group, letter, start_matrix, end_matrix)
                if dist < shortest_dist:
                    shortest_dist = dist
                    return_pos = pos
        else:
            dist = calc_dist_between_set_of_coords(start_pos, pos, space_group, letter, start_matrix, end_matrix)
            if dist < shortest_dist:
                shortest_dist = dist
                return_pos = pos
    if shortest_dist == 99999:
        for pos in pos_to_compare:
            dist = calc_dist_between_set_of_coords(start_pos, pos, space_group, letter, start_matrix, end_matrix)
            if dist < shortest_dist:
                shortest_dist = dist
                return_pos = pos
    return shortest_dist, return_pos, coll_msg

def check_if_vectors_get_close(pos1_start, pos1_end, pos2_start, pos2_end, coll_threshold):
    pos1_direction = pos1_end - pos1_start
    pos2_direction = pos2_end - pos2_start
    # a will always be positive
    a = ((pos1_direction[0] - pos2_direction[0])**2 + (pos1_direction[1] - pos2_direction[1])**2 + (pos1_direction[2] - pos2_direction[2])**2)
    b = ((pos1_direction[0] - pos2_direction[0]) * (pos1_start[0] - pos2_start[0]) + (pos1_direction[1] - pos2_direction[1]) * (pos1_start[1] - pos2_start[1]) + (pos1_direction[2] - pos2_direction[2]) * (pos1_start[2] - pos2_start[2]))
    c = ((pos1_start[0] - pos2_start[0])**2 + (pos1_start[1] - pos2_start[1])**2 + (pos1_start[2] - pos2_start[2])**2)
    d = coll_threshold**2
    comp_value = (2*b)**2 - 4 * a * (c - d)
    if a != 0:
        if comp_value < 0:
            return False
        elif comp_value == 0:
            return (0 <= -b / (2 * a) <= 1)
        else:
            if (a + 2 * b + c - d <= 0) or (c - d <= 0):
                return True
            else:
                sol1 = (-b + np.sqrt(comp_value)) / (2 * a)
                sol2 = (-b - np.sqrt(comp_value)) / (2 * a)
                return (0 <= sol1 <= 1 and 0 <= sol2 <= 1)
    else:
        return (c - d <= 0 or 2 * b + c - d <= 0)