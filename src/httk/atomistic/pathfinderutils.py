"""This module contains the class with tools used by the path finding program."""
from ase import io, Atoms
from ase.io import vasp
import spglib
import sys
import os
import json
import re
import numpy as np
from httk.atomistic.data.symmetry_wyckoff import Spacegroup
from diffpy.structure.lattice import Lattice
from ase.neighborlist import primitive_neighbor_list


with open(os.path.join(sys.path[0], "correct_hall_nums.json"), "r") as f:
    hall_nums = json.load(f)

def read_file(file_path, symprec_val):
    """Read crystal structure and returns extra information on symmetry properties.

    Args:
        file_path (str): File path for a file that can be read using the ase.io.read() function.
        symprec_val (float): Precision used by spglib when finding space group of the provided crystal structure.
    
    Returns:
        dict: Dictionary containing extra information on the crystal structure.
            space_number - The space group number.
            wyckoffs - List of Wyckoff positions and information about them.
            orig_struct - The provided structure, as used by spglib.
            new_struct - Symmetrized structure as provided by spglib.
            num_of_atoms - The number of atoms in the symmetrized structure, its size.
            formula - The atomic formula of the structure, used as a prefix for the output files.
    """
    atoms_obj = io.read(file_path)
    positions = atoms_obj.get_scaled_positions()
    numbers = atoms_obj.get_atomic_numbers()
    lattice = atoms_obj.get_cell()
    atomic_formula = atoms_obj.get_chemical_formula()
    if re.search("[A-Za-z]$", atomic_formula):
        atomic_formula += "1"
    needs_1 = re.findall("[A-Za-z]{1}[A-Z]{1}", atomic_formula)
    for s in needs_1:
        atomic_formula = atomic_formula.replace(s, s[0] + "1" + s[1])
    cell = (lattice, positions, numbers)
    dataset = spglib.get_symmetry_dataset(cell, symprec=symprec_val)
    if str(dataset["number"]) in hall_nums:
        hall_num = hall_nums[str(dataset["number"])]
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
    return {"space_number": dataset3["number"],
            "wyckoffs": new_wyckoff,
            "orig_struct": cell,
            "new_struct": new_struct2,
            "num_of_atoms": num_of_atoms,
            "formula": atomic_formula}

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

def calc_new_lattice(curr_lattice, trans_matrix):
    """Calculate new lattice given current lattice and transformation matrix.
    
    Args:
        curr_lattice (list): 3x3 matrix describing current structure lattice.
        trans_matrix (list): 4x4 matrix describing transformation matrix to subgroup structure.
    Returns:
        list: 3x3 matrix describing subgroup structure lattice.
    """
    return np.matmul(np.array([x[0:3] for x in trans_matrix[0:3]]).T, np.array(curr_lattice)).tolist()

def get_best_trans_matrix(matrices):
    """Get first transformation matrix with no origin shift, or the one with the smallest.

    Args:
        matrices (list): List of dictionaries each containing a transformation matrix and corresponding Wyckoff splittings.
    """
    best_matrix = None
    lowest_translation_sum = 9999
    for matrix in matrices:
        translation_sum = sum([abs(x[3]) for x in matrix["trans_matrix"][0:3]])
        if translation_sum == 0:
            return matrix
        else:
            if translation_sum < lowest_translation_sum:
                lowest_translation_sum = translation_sum
                best_matrix = matrix
    return best_matrix

def get_orbits(wyckoffs, wyckoff_letter):
    """Get orbits for specific Wyckoff splitting.
    
    Args:
        wyckoffs (list): List of Wyckoff splittings. Excerpt from MAXSUB database.
        wyckoff_letter: Wyckoff letter of current Wyckoff position to be split.
    """
    for wyckoff in wyckoffs:
        if wyckoff_letter in wyckoff["group"]:
            return wyckoff

def write_struct_to_file(file_name, struct, format_name):
    """Write crystal structure to file.
    
    Args:
        file_name (str): File name including path.
        struct (list): List containing lattice, positions and atom numbers of crystal structure.
        format_name (str): Name of format the structure file should be written to.
    """
    atoms_obj = Atoms(cell=struct[0], scaled_positions=struct[1], numbers=struct[2])
    if format_name == "poscar":
        vasp.write_vasp(file_name, atoms_obj, direct=True)
    else:
        io.write(file_name, atoms_obj)

def write_transition(file_name, struct):
    """Write interpolation info to file.
    
    Args:
        file_name (str): File name including path.
        struct (dict): Dictionary containing the transformation matrix and information on the Wyckoff orbits from the old and new structures.
    """
    with open(file_name, "w") as f:
        f.write("Transformation matrix and wyckoff positions of structures\n")
        if "matrix" in struct:
            for matrix_line in struct["matrix"]:
                f.write("\t".join([str(x) for x in matrix_line]) + "\n")
        f.write(", ".join(["id", "atomic_number", "wyckoff_letter", "multiplicity", "position", "freedom_degrees"]) + "\n")
        for key, val in struct.items():
            if key != "matrix":
                f.write(key + ": " + "\n")
                f.write(str(val["space_num"]) + "\n")
                for wyckoff in val["wyckoff"]:
                    f.write(", ".join([str(wyckoff["id"]), str(wyckoff["atom"]), wyckoff["letter"], str(wyckoff["multiplicity"]), str(wyckoff["basis"]), str(wyckoff["freedom_degr"])]) + "\n")

def write_interpolation_info(file_name, info):
    """Write interpolation info to file.
    
    Args:
        file_name (str): File name including path.
        info (dict): Dictionary containing information on the interpolation.
    """
    with open(file_name, "w") as f:
        f.write("start_id:end_id\n")
        for key, val in info.items():
            f.write(str(key[0]) + ":" + str(key[1]) + "\n")
            if val:
                for degr, interpolated_values in val.items():
                    f.write(degr + ": " + ", ".join([str(x) for x in interpolated_values]) + "\n")
            else:
                f.write("No degrees of freedom\n")

def compare_wyckoffs(wyckoffs1, wyckoffs2):
    """Compare two sets of wyckoff orbits, return True if they have the same sets of letters and atoms."""
    if len(wyckoffs1) == len(wyckoffs2):
        wyckoffs1.sort(key=lambda a: a["letter"] + str(a["atom"]))
        wyckoffs2.sort(key=lambda a: a["letter"] + str(a["atom"]))
        i = 0
        while i < len(wyckoffs1):
            if (wyckoffs1[i]["atom"] != wyckoffs2[i]["atom"]) or (wyckoffs1[i]["letter"] != wyckoffs2[i]["letter"]):
                return False
            i += 1
        return True
    return False

def check_struct_compatibility(f1_info, f2_info, max_orig):
    """Check if two structures are compatible and have the same stochiometry.

    Args:
        f1_info (dict): Info about starting structure.
        f2_info (dict): Info about ending structure.
        max_orig (int): Maximum number of atoms allowed in provided structures.

    Returns:
        str: Formula describing atomic composition, returned if the two structures match.
    """
    if f1_info["num_of_atoms"] > max_orig:
        print("Start point structure is too large: " + str(f1_info["num_of_atoms"]) + " > " + str(max_orig))
        sys.exit(0)
    if f2_info["num_of_atoms"] > max_orig:
        print("End point structure is too large: " + str(f2_info["num_of_atoms"]) + " > " + str(max_orig))
        sys.exit(0)
    if f1_info["space_number"] == f2_info["space_number"] and compare_wyckoffs(f1_info["wyckoffs"], f2_info["wyckoffs"]):
        print("Structures are identical")
    if len(set(f1_info["new_struct"][2])) != len(set(f2_info["new_struct"][2])):
        print("Structures' atomic composition does not match")
        sys.exit(0)
    for atom in set(f1_info["new_struct"][2]):
        if atom not in f2_info["new_struct"][2]:
            print("Structures' atomic composition does not match")
            sys.exit(0)
    atom_count_1 = get_reduced_formula_info(f1_info["formula"])
    atom_count_2 = get_reduced_formula_info(f2_info["formula"])
    atoms = list(atom_count_1.keys())
    if len(atoms) > 1:
        for atom in atoms:
            if atom_count_1[atom] != atom_count_2[atom]:
                print("Structures' atomic composition does not match")
                sys.exit(0)
    return "".join([i + str(j) if j > 1 else i for i, j in atom_count_1.items()])

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

def get_reduced_formula_info(formula_str):
    atom_count = {}
    big_letters = re.findall("[A-Z]{2}", formula_str)
    for big_letter_combo in big_letters:
        formula_str = formula_str.replace(big_letter_combo, big_letter_combo[0]+"1"+big_letter_combo[1])
    atom_count_pairs = re.findall("[A-Za-z]+[0-9]+", formula_str)
    for pair in atom_count_pairs:
        head = pair.rstrip("0123456789")
        tail = pair[len(head):]
        atom_count[head] = int(tail)
    atom_count_gcd = np.gcd.reduce(list(atom_count.values()))
    for key, val in atom_count.items():
        atom_count[key] = int(val / atom_count_gcd)
    return atom_count

def get_interpolation(wyckoffs1, wyckoffs2, space_group, start_matrix, end_matrix, steps, collision_threshold, collision_level):
    complete_structures = []
    interpolation_desc = {}
    done_atom_letter = []
    pair_dict = {}
    xyz = ["x", "y", "z"]
    start_parameters = lattice_matrix_to_parameters(start_matrix)
    end_parameters = lattice_matrix_to_parameters(end_matrix)
    intermediate_parameters = interpolate_between_coords(start_parameters, end_parameters, steps)
    complete_structures = [[lattice_parameters_to_matrix(x)] for x in intermediate_parameters]
    matrices = [lattice_parameters_to_matrix(x) for x in intermediate_parameters]
    total_dist = 0
    i = 0
    while i < len(wyckoffs1):
        if str(wyckoffs1[i]["atom"]) + wyckoffs1[i]["letter"] not in done_atom_letter:
            curr_wyckoffs_2 = [x for x in wyckoffs2 if str(x["atom"]) + x["letter"] == str(wyckoffs1[i]["atom"]) + wyckoffs1[i]["letter"]]
            curr_wyckoffs_1 = [x for x in wyckoffs1 if str(x["atom"]) + x["letter"] == str(wyckoffs1[i]["atom"]) + wyckoffs1[i]["letter"]]
            pair_dict_add, corr_msg_list, part_dist = get_best_vector_pairs(curr_wyckoffs_1, curr_wyckoffs_2, space_group, matrices, start_matrix, end_matrix, steps, collision_threshold, collision_level)
            total_dist += part_dist
            pair_dict.update(pair_dict_add)
            done_atom_letter.append(str(wyckoffs1[i]["atom"]) + wyckoffs1[i]["letter"])
        i += 1
    for pair, pair_info in pair_dict.items():
        degr_free = wyckoffs1[pair[0]]["freedom_degr"]
        wyckoffs2[pair[1]]["basis"] = pair_info[4]
        interpolated_basis = interpolate_between_coords(wyckoffs1[pair[0]]["basis"], wyckoffs2[pair[1]]["basis"], steps)
        interpolation_desc[pair] = {}
        i = 0
        while i < steps:
            positions, atoms = get_pos_from_wyckoff(space_group, {"atom": wyckoffs1[pair[0]]["atom"], "basis": interpolated_basis[i], "letter": wyckoffs1[pair[0]]["letter"]})
            if len(complete_structures[i]) == 1:
                complete_structures[i] += [list(positions), atoms]
            else:
                complete_structures[i][1] += list(positions)
                complete_structures[i][2] += atoms
            for j in range(0, 3):
                if degr_free[j]:
                    if xyz[j] in interpolation_desc[pair]:
                        interpolation_desc[pair][xyz[j]].append(interpolated_basis[i][j])
                    else:
                        interpolation_desc[pair][xyz[j]] = [interpolated_basis[i][j]]
            i += 1
    if collision_level > 0:
        i = 0
        while i < len(complete_structures):
            if check_collision_in_pos_ase(np.array(complete_structures[i][1]), collision_threshold, np.array(complete_structures[i][0])):
                corr_msg_list.append(str(i))
            i += 1
    return complete_structures, interpolation_desc, corr_msg_list, total_dist

def get_best_vector_pairs(wyckoffs1, wyckoffs2, space_group, matrices, start_matrix, end_matrix, steps, collision_threshold, collision_level):
    result_list = {}
    distances = {}
    dist_list = []
    coll_msg = []
    i = 0
    while i < len(wyckoffs1):
        j = 0
        while j < len(wyckoffs2):
            wyckoff2_pos, wyckoff2_atoms = get_pos_from_wyckoff(space_group, wyckoffs2[j])
            possible_free_degr = []
            for pos in wyckoff2_pos:
                pos_works = True
                for k in range(0, 3):
                    if not wyckoffs2[j]["freedom_degr"][k]:
                        if np.round(wyckoffs2[j]["basis"][k], 8) != np.round(pos[k], 8):
                            pos_works = False
                if pos_works:
                    candidate_pos, temp_atoms = get_pos_from_wyckoff(space_group, wyckoffs2[j], pos)
                    if compare_list_of_coords(wyckoff2_pos, candidate_pos):
                        possible_free_degr.append(pos)
            for possible_val in possible_free_degr:
                dist, new_end, coll_warning = calc_dist_with_boundary(wyckoffs1[i]["basis"], possible_val, wyckoffs1[i]["freedom_degr"], space_group, wyckoffs1[i]["letter"], matrices, steps, collision_threshold, collision_level, start_matrix, end_matrix, (wyckoffs1[i]["id"], wyckoffs2[j]["id"]))
                if coll_warning:
                    coll_msg.append(coll_warning)
                distances[(wyckoffs1[i]["id"], wyckoffs2[j]["id"])] = [dist, wyckoffs1[i]["id"], wyckoffs2[j]["id"], wyckoffs1[i]["basis"], new_end, wyckoffs1[i]]
                dist_list.append([dist, wyckoffs1[i]["id"], wyckoffs2[j]["id"], wyckoffs1[i]["basis"], new_end, wyckoffs1[i]])
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

def get_lowest_degr_free(wyckoff, space_group):
    s = Spacegroup(space_group)
    all_coords = s[wyckoff["letter"]].affinedot(wyckoff["basis"])
    all_coords.sort(key=get_dist_to_origin)
    for coord in all_coords:
        generated_coords = s[wyckoff["letter"]].affinedot[coord]
        if compare_list_of_coords(all_coords, generated_coords):
            return coord
    return None

def get_dist_to_origin(coord):
    corner_coord = 1 * (np.array(coord) > 0.5)
    dist = np.linalg.norm(corner_coord - coord)
    return dist

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

def check_collision_in_pos(positions, coll_dist):
    i = 0
    while i < len(positions):
        j = i + 1
        while j < len(positions):
            if np.linalg.norm(positions[i] - positions[j]) < coll_dist:
                return True
            j += 1
        i += 1
    return False

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