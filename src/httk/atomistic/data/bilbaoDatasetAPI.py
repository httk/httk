import json, sys
from os.path import abspath, dirname, join
with open(join(dirname(abspath(__file__)), "..", "..", "..", "external", "FromBilbaoCrystallographicServer", "bilbaoMAXSUB_WPsplittings.json"), "r") as f:
    data = json.load(f)
def get_max_subgroups(group_id, sub_type=None, curr_size=None, max_size=None, subgroup_restriction=[], search_same_spacegroup=False):
    group_id = str(group_id)
    return_list = []
    for key, val in data[group_id]["data"].items():
        if search_same_spacegroup:
            if sub_type and curr_size and max_size:
                if curr_size * val["size_increase"] <= max_size and val["type"] in sub_type and (val["int_number"] in subgroup_restriction or len(subgroup_restriction) == 0) and group_id == str(val["int_number"]):
                    return_list.append({"id": key, "int_number": val["int_number"], "space_name": val["space_name"], "index": val["index"], "type": val["type"], "size_increase": val["size_increase"]})
            elif (val["int_number"] in subgroup_restriction or len(subgroup_restriction) == 0) and group_id == str(val["int_number"]):
                return_list.append({"id": key, "int_number": val["int_number"], "space_name": val["space_name"], "index": val["index"], "type": val["type"], "size_increase": val["size_increase"]})
        else:
            if sub_type and curr_size and max_size:
                if curr_size * val["size_increase"] <= max_size and val["type"] in sub_type and (val["int_number"] in subgroup_restriction or len(subgroup_restriction) == 0) and group_id != str(val["int_number"]):
                    return_list.append({"id": key, "int_number": val["int_number"], "space_name": val["space_name"], "index": val["index"], "type": val["type"], "size_increase": val["size_increase"]})
            elif (val["int_number"] in subgroup_restriction or len(subgroup_restriction) == 0) and group_id != str(val["int_number"]):
                return_list.append({"id": key, "int_number": val["int_number"], "space_name": val["space_name"], "index": val["index"], "type": val["type"], "size_increase": val["size_increase"]})
    return return_list
def get_space_group_name(group_id):
    return data[str(group_id)]["name"]
def get_trans_matrices(group_id, subgroup_id, subgroup_index=None, subgroup_type=None):
    if "_" in subgroup_id:
        return data[str(group_id)]["data"][subgroup_id]["trans_matrices"]
    return data[str(group_id)]["data"][str(subgroup_id)+"_"+str(subgroup_index)+"_"+subgroup_type]["trans_matrices"]
def get_best_trans_matrix(group_id, subgroup_id, subgroup_index=None, subgroup_type=None):
    """Get first transformation matrix with no origin shift, or the one with the smallest.

    Args:
        matrices (list): List of dictionaries each containing a transformation matrix and corresponding Wyckoff splittings.
    """
    best_matrix = None
    lowest_translation_sum = 9999
    for matrix in get_trans_matrices(group_id, subgroup_id, subgroup_index, subgroup_type):
        translation_sum = sum([abs(x[3]) for x in matrix["trans_matrix"][0:3]])
        if translation_sum == 0:
            return matrix
        else:
            if translation_sum < lowest_translation_sum:
                lowest_translation_sum = translation_sum
                best_matrix = matrix
    return best_matrix