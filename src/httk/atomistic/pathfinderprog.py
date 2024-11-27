import httk.atomistic.pathfinderutils as pfutils
import httk.atomistic.data.bilbaoDatasetAPI as bilbaoAPI
import datetime
import os
import json


def check_path(start_wyckoff, path1, end_wyckoff, path2, final_space_id):
    path1_transformation = {}
    prev_wyckoffs1 = start_wyckoff
    next_wyckoffs1 = start_wyckoff
    i = 1
    while i < len(path1):
        transformation_info = pfutils.get_best_trans_matrix(bilbaoAPI.get_trans_matrices(path1[i - 1][0]["int_number"], path1[i][0]["id"]))
        wp_splitting = transformation_info["wp_splitting"]
        transformation_matrix = transformation_info["trans_matrix"]
        next_wyckoffs1 = pfutils.get_next_wyckoffs(path1[i][0]["int_number"], prev_wyckoffs1, wp_splitting)
        transformation_desc = [{"matrix": transformation_matrix, str(i): {"space_num": path1[i - 1][0]["int_number"], "wyckoff": prev_wyckoffs1.copy()}, str(i + 1): {"space_num": path1[i][0]["int_number"], "wyckoff": next_wyckoffs1}}, wp_splitting]
        prev_wyckoffs1 = next_wyckoffs1
        path1_transformation[str(i) + "-" + str(i + 1)] = transformation_desc
        i += 1
    if len(path1) == 1:
        path1_transformation["0-1"] = [{"1": {"space_num": path1[0][0]["int_number"], "wyckoff": prev_wyckoffs1.copy()}}]
    path2_transformation = {}
    prev_wyckoffs2 = end_wyckoff
    next_wyckoffs2 = end_wyckoff
    i = 1
    while i < len(path2):
        transformation_info = pfutils.get_best_trans_matrix(bilbaoAPI.get_trans_matrices(path2[i - 1][0]["int_number"], path2[i][0]["id"]))
        wp_splitting = transformation_info["wp_splitting"]
        transformation_matrix = transformation_info["trans_matrix"]
        next_wyckoffs2 = pfutils.get_next_wyckoffs(path2[i][0]["int_number"], prev_wyckoffs2, wp_splitting)
        transformation_desc = [{"matrix": transformation_matrix, str(i): {"space_num": path2[i - 1][0]["int_number"], "wyckoff": prev_wyckoffs2.copy()}, str(i + 1): {"space_num": path2[i][0]["int_number"], "wyckoff": next_wyckoffs2}}, wp_splitting]
        path2_transformation[str(i) + "-" + str(i + 1)] = transformation_desc
        prev_wyckoffs2 = next_wyckoffs2
        i += 1
    if len(path2) == 1:
        path2_transformation["0-1"] = [{"1": {"space_num": path2[0][0]["int_number"], "wyckoff": prev_wyckoffs2.copy()}}]
    return pfutils.compare_wyckoffs(next_wyckoffs1, next_wyckoffs2), path1_transformation, path2_transformation

def search_for_paths(wyckoffs1, paths_1, wyckoffs2, paths_2, max_size, sub_type, max_depth, max_results, subgroup_choices, search_within_spacegroup=False):
    complete_matches = []
    continue_search = True
    curr_depth = 0
    path_1_prev_len = 0
    path_2_prev_len = 1
    paths_1_start_len = len(paths_1[0])
    paths_2_start_len = len(paths_2[0])
    if len(paths_1) > 1 or len(paths_2) > 1:
        print("Incorrectly provided lengths of starting paths")
    subgroup_restriction = []
    if search_within_spacegroup:
        subgroup_restriction.append(paths_1[0][-1][0]["int_number"])
    while continue_search:
        i = path_1_prev_len
        while i < len(paths_1):
            if paths_1[i][-1][0]["int_number"] in subgroup_choices:
                j = 0
                while j < len(paths_2):
                    if paths_2[j][-1][0]["int_number"] in subgroup_choices:
                        if paths_2[j][-1][0]["int_number"] == paths_1[i][-1][0]["int_number"]:
                            if paths_2[j][-1][1] == paths_1[i][-1][1]:
                                result, path1_transformation, path2_transformation = check_path(wyckoffs1, paths_1[i], wyckoffs2, paths_2[j], paths_2[j][-1][0]["int_number"])
                                if result:
                                    subgroup_choices.remove(paths_1[i][-1][0]["int_number"])
                                    complete_matches.append([paths_1[i], path1_transformation, paths_2[j], path2_transformation])
                                    if len(complete_matches) == max_results:
                                        return complete_matches
                            elif not search_within_spacegroup:
                                new_matches = search_for_paths(wyckoffs1, [paths_1[i]], wyckoffs2, [paths_2[j]], max_size, sub_type, 4, 1, [paths_1[i][-1][0]["int_number"]], True)
                                subgroup_choices.remove(paths_1[i][-1][0]["int_number"])
                                if len(new_matches) > 0:
                                    complete_matches += new_matches
                                    if len(complete_matches) == max_results:
                                        return complete_matches
                    j += 1
            i += 1
        i = 0
        while i < path_1_prev_len:
            if paths_1[i][-1][0]["int_number"] in subgroup_choices:
                j = path_2_prev_len
                while j < len(paths_2):
                    if paths_2[j][-1][0]["int_number"] in subgroup_choices:
                        if paths_2[j][-1][0]["int_number"] == paths_1[i][-1][0]["int_number"]:
                            if paths_2[j][-1][1] == paths_1[i][-1][1]:
                                result, path1_transformation, path2_transformation = check_path(wyckoffs1, paths_1[i], wyckoffs2, paths_2[j], paths_2[j][-1][0]["int_number"])
                                if result:
                                    subgroup_choices.remove(paths_1[i][-1][0]["int_number"])
                                    complete_matches.append([paths_1[i], path1_transformation, paths_2[j], path2_transformation])
                                    if len(complete_matches) == max_results:
                                        return complete_matches
                            elif not search_within_spacegroup:
                                new_matches = search_for_paths(wyckoffs1, [paths_1[i]], wyckoffs2, [paths_2[j]], max_size, sub_type, 4, 1, [paths_1[i][-1][0]["int_number"]], True)
                                subgroup_choices.remove(paths_1[i][-1][0]["int_number"])
                                if len(new_matches) > 0:
                                    complete_matches += new_matches
                                    if len(complete_matches) == max_results:
                                        return complete_matches
                    j += 1
            i += 1
        curr_depth += 1
        all_new_empty = True
        if curr_depth < max_depth:
            k = 0
            path_1_prev_len = len(paths_1)
            while k < path_1_prev_len:
                if len(paths_1[k]) == curr_depth - 1 + paths_1_start_len:
                    new_subgroups = bilbaoAPI.get_max_subgroups(paths_1[k][-1][0]["int_number"], sub_type, paths_1[k][-1][1], max_size, subgroup_restriction, search_within_spacegroup)
                    for subgroup in new_subgroups:
                        all_new_empty = False
                        paths_1.append(paths_1[k] + [(subgroup, paths_1[k][-1][1] * subgroup["size_increase"])])
                k += 1
            m = 0
            path_2_prev_len_len = len(paths_2)
            while m < path_2_prev_len_len:
                if len(paths_2[m]) == curr_depth - 1 + paths_2_start_len:
                    new_subgroups = bilbaoAPI.get_max_subgroups(paths_2[m][-1][0]["int_number"], sub_type, paths_2[m][-1][1], max_size, subgroup_restriction, search_within_spacegroup)
                    for subgroup in new_subgroups:
                        all_new_empty = False
                        paths_2.append(paths_2[m] + [(subgroup, paths_2[m][-1][1] * subgroup["size_increase"])])
                m += 1
        else:
            continue_search = False
        if all_new_empty:
            continue_search = False
    return complete_matches

def generate_structs(paths, f1_info, f2_info, steps, collision_threshold, collision_level):
    paths_main = {}
    paths_short = {}
    i = 0
    while i < len(paths):
        paths_main[str(i + 1)] = {"start": {"1": f1_info["new_struct"]}, "end": {"1": f2_info["new_struct"]}}
        paths_short[str(i + 1)] = {"start": [], "end": []}
        paths_short[str(i + 1)]["size"] = paths[i][0][-1][1]
        j = 0
        while j < len(paths[i][0]):
            paths_short[str(i + 1)]["start"].append(paths[i][0][j][0]["int_number"])
            j += 1
        j = 0
        while j < len(paths[i][2]):
            paths_short[str(i + 1)]["end"].append(paths[i][2][j][0]["int_number"])
            j += 1
        # construct path 1
        next_lattice = f1_info["new_struct"][0]
        if len(paths[i][0]) > 1:
            j = 1
            while j < len(paths[i][0]):
                new_positions = []
                new_numbers = []
                next_lattice = pfutils.calc_new_lattice(next_lattice, paths[i][1][str(j) + "-" + str(j + 1)][0]["matrix"])
                prev_wyckoff = paths[i][1][str(j) + "-" + str(j + 1)][0][str(j)]["wyckoff"]
                for elem in prev_wyckoff:
                    wp_splitting_info = pfutils.get_orbits(paths[i][1][str(j) + "-" + str(j + 1)][1], elem["letter"])
                    for orbit_info in wp_splitting_info["orbits"]:
                        new_positions.append(pfutils.calc_new_wyckoff_pos(elem["basis"], orbit_info["subgroup_basis"]))
                        new_numbers.append(elem["atom"])
                paths_main[str(i + 1)]["start"][str(j + 1)] = (next_lattice, new_positions, new_numbers)
                paths_main[str(i + 1)]["start"][str(j) + "-" + str(j + 1)] = paths[i][1][str(j) + "-" + str(j + 1)][0]
                j += 1
        else:
            paths_main[str(i + 1)]["start"]["0-1"] = paths[i][1]["0-1"][0]
        # construct path 2
        next_lattice = f2_info["new_struct"][0]
        if len(paths[i][2]) > 1:
            j = 1
            while j < len(paths[i][2]):
                new_positions = []
                new_numbers = []
                next_lattice = pfutils.calc_new_lattice(next_lattice, paths[i][3][str(j) + "-" + str(j + 1)][0]["matrix"])
                prev_wyckoff = paths[i][3][str(j) + "-" + str(j + 1)][0][str(j)]["wyckoff"]
                for elem in prev_wyckoff:
                    wp_splitting_info = pfutils.get_orbits(paths[i][3][str(j) + "-" + str(j + 1)][1], elem["letter"])
                    for orbit_info in wp_splitting_info["orbits"]:
                        new_positions.append(pfutils.calc_new_wyckoff_pos(elem["basis"], orbit_info["subgroup_basis"]))
                        new_numbers.append(elem["atom"])
                paths_main[str(i + 1)]["end"][str(j + 1)] = (next_lattice, new_positions, new_numbers)
                paths_main[str(i + 1)]["end"][str(j) + "-" + str(j + 1)] = paths[i][3][str(j) + "-" + str(j + 1)][0]
                j += 1
        else:
            paths_main[str(i + 1)]["end"]["0-1"] = paths[i][3]["0-1"][0]
        subgroup_start = paths_main[str(i + 1)]["start"][str(len(paths[i][0]))]
        wyckoffs_start = paths[i][1][str(len(paths[i][0]) - 1) + "-" + str(len(paths[i][0]))][0][str(len(paths[i][0]))]["wyckoff"]
        subgroup_end = paths_main[str(i + 1)]["end"][str(len(paths[i][2]))]
        wyckoffs_end = paths[i][3][str(len(paths[i][2]) - 1) + "-" + str(len(paths[i][2]))][0][str(len(paths[i][2]))]["wyckoff"]
        space_group = paths[i][3][str(len(paths[i][2]) - 1) + "-" + str(len(paths[i][2]))][0][str(len(paths[i][2]))]["space_num"]
        intermediate_structs, interpolation_desc, coll_msg_list, total_dist = pfutils.get_interpolation(wyckoffs_start, wyckoffs_end, space_group, subgroup_start[0], subgroup_end[0], steps, collision_threshold, collision_level)
        if len(coll_msg_list) > 0:
            paths_short[str(i + 1)]["collision"] = coll_msg_list
        paths_main[str(i + 1)]["interpolation"] = {}
        paths_main[str(i + 1)]["interpolation"]["structs"] = intermediate_structs
        paths_main[str(i + 1)]["interpolation"]["desc"] = interpolation_desc
        paths_short[str(i + 1)]["total_distance"] = total_dist
        i += 1
    return paths_short, paths_main

def get_paths(f1, f2, max_depth, symprec, sub_type, max_path, max_orig, max_results, steps, subgroups, collision_threshold, collision_level):
    # Function for getting start and end structures, generating paths and generating the structures along the paths.
    f1_info = pfutils.read_file(f1, symprec)
    f2_info = pfutils.read_file(f2, symprec)
    prefix_str = pfutils.check_struct_compatibility(f1_info, f2_info, max_orig)
    if subgroups[0].lower() == "any":
        subgroup_choice = [x for x in range(1, 231)]
    else:
        subgroup_choice = [int(x) for x in subgroups]
    paths_1 = [[({"int_number": f1_info["space_number"]}, f1_info["num_of_atoms"])]]
    paths_2 = [[({"int_number": f2_info["space_number"]}, f2_info["num_of_atoms"])]]
    found_paths = search_for_paths(f1_info["wyckoffs"], paths_1, f2_info["wyckoffs"], paths_2, max_path, sub_type, max_depth, max_results, subgroup_choice)
    if len(found_paths) == 0:
        print("No found paths")
        return None, None, None, None, "no_path"
        #sys.exit(0)
    paths_short, paths_main = generate_structs(found_paths, f1_info, f2_info, steps, collision_threshold, collision_level)
    start_orig = f1_info["orig_struct"]
    end_orig = f2_info["orig_struct"]
    return prefix_str, start_orig, end_orig, paths_short, paths_main

def get_subgroup_struct(orig_struct, subgroup_num, symprec):
    # timing code
    # import time
    struct_info = pfutils.read_file(orig_struct, symprec)
    reduced_formula = pfutils.get_reduced_formula_info(struct_info["formula"])
    prefix_str = "".join([i + str(j) if j > 1 else i for i, j in reduced_formula.items()])
    subgroups = bilbaoAPI.get_max_subgroups(struct_info["space_number"])
    i = 0
    while i < len(subgroups):
        if subgroup_num[0] != "all":
            if subgroups[i]["int_number"] not in subgroup_num or subgroups[i]["int_number"] == struct_info["space_number"]:
                del subgroups[i]
                i -= 1
        elif subgroups[i]["int_number"] == struct_info["space_number"]:
            del subgroups[i]
            i -= 1
        i += 1
    if len(subgroups) == 0:
        print("Space group(s) " + str(subgroup_num) + " not in list of maximal subgroups of space group " + str(struct_info["space_number"]))
    subgroup_structs = []
    trans_info_list = []
    for subgroup_info in subgroups:
        # timing code
        # start_time = time.time()
        transformation_info = pfutils.get_best_trans_matrix(bilbaoAPI.get_trans_matrices(struct_info["space_number"], subgroup_info["id"]))
        wp_splitting = transformation_info["wp_splitting"]
        transformation_matrix = transformation_info["trans_matrix"]
        next_wyckoffs = pfutils.get_next_wyckoffs(subgroup_info["int_number"], struct_info["wyckoffs"], wp_splitting)
        trans_info_list.append({"matrix": transformation_matrix, "group": {"space_num": struct_info["space_number"], "wyckoff": struct_info["wyckoffs"]}, "subgroup": {"space_num": subgroup_info["int_number"], "wyckoff": next_wyckoffs}})
        new_positions = []
        new_numbers = []
        new_lattice = pfutils.calc_new_lattice(struct_info["new_struct"][0], transformation_matrix)
        for wyckoff in next_wyckoffs:
            pos, num = pfutils.get_pos_from_wyckoff(subgroup_info["int_number"], wyckoff)
            new_positions += list(pos)
            new_numbers += list(num)
        subgroup_structs.append((new_lattice, new_positions, new_numbers))
        # timing code
        # end_time = time.time()
        # elapsed_time = (end_time-start_time)
        # trans_info_list[-1]["time"] = elapsed_time
    return struct_info["space_number"], struct_info["new_struct"], subgroup_structs, trans_info_list, prefix_str

def output_paths(prefix_str, start_orig, end_orig, paths_short, paths_main, output_folder, formats, output_name, input_values):
    # Output results to files.
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    if output_name:
        work_folder = os.path.join(output_folder, output_name)
    else:
        work_folder = os.path.join(output_folder, timestamp)
    input_values["timestamp"] = timestamp
    os.makedirs(work_folder)
    main_dict = {"input_values": input_values, "paths": paths_short}
    with open(os.path.join(work_folder, prefix_str + "_out.json"), "w") as f:
        json.dump(main_dict, f, indent=4)
    for format_name in formats:
        pfutils.write_struct_to_file(os.path.join(work_folder, prefix_str + "_start." + format_name.replace("poscar", "vasp")), start_orig, format_name)
        pfutils.write_struct_to_file(os.path.join(work_folder, prefix_str + "_end." + format_name.replace("poscar", "vasp")), end_orig, format_name)
    for key_main, val_main in paths_main.items():
        for key, val in val_main.items():
            os.makedirs(os.path.join(work_folder, key_main, key))
            for struct_key, struct_val in val.items():
                if struct_key == "structs":
                    i = 0
                    while i < len(struct_val):
                        for format_name in formats:
                            pfutils.write_struct_to_file(os.path.join(os.path.join(work_folder, key_main, key), prefix_str + "_path" + key_main + "_" + key + "_" + str(i) + "." + format_name.replace("poscar", "vasp")), struct_val[i], format_name)
                        i += 1
                elif struct_key == "desc":
                    pfutils.write_interpolation_info(os.path.join(os.path.join(work_folder, key_main, key), prefix_str + "_path" + key_main + "_" + key + "_" + struct_key + ".txt"), struct_val)
                elif "-" in struct_key:
                    pfutils.write_transition(os.path.join(os.path.join(work_folder, key_main, key), prefix_str + "_path" + key_main + "_" + key + "_" + struct_key + ".txt"), struct_val)
                else:
                    for format_name in formats:
                        pfutils.write_struct_to_file(os.path.join(os.path.join(work_folder, key_main, key), prefix_str + "_path" + key_main + "_" + key + "_" + struct_key + "_" + str(paths_short[key_main][key][int(struct_key) - 1]) + "." + format_name.replace("poscar", "vasp")), struct_val, format_name)

def output_subgroup(file_prefix, start_num, std_struct, sub_structs, transition_info, output_folder, formats):
    work_folder = os.path.join(output_folder, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(work_folder)
    for format_name in formats:
        pfutils.write_struct_to_file(os.path.join(work_folder, file_prefix + "_" + str(start_num) + "_std." + format_name.replace("poscar", "vasp")), std_struct, format_name)
    i = 0
    while i < len(sub_structs):
        for format_name in formats:
            pfutils.write_struct_to_file(os.path.join(work_folder, file_prefix + "_" + str(transition_info[i]["subgroup"]["space_num"]) + "_struct." + format_name.replace("poscar", "vasp")), sub_structs[i], format_name)
        pfutils.write_transition(os.path.join(work_folder, file_prefix + "_" + str(transition_info[i]["subgroup"]["space_num"]) + "_wyckoff.txt"), transition_info[i])
        i += 1
