import argparse
import os
import sys
program_path = sys.path[0]
parser = argparse.ArgumentParser(prog="space group pathfinder", description="Program for finding path with most symmetries between two given space group structures.")
parser.add_argument("-f", "--files", nargs=1, type=str, help="Files providing structures of start and end points in paths.")
parser.add_argument("-s", "--subgroup", nargs="+", type=int, help="Subgroup to generate. Can be 'all' or list of numbers.", default=["all"])
parser.add_argument("--output", nargs=1, help="Directory to save output in.", default=["sub_output"])
parser.add_argument("--save-format", choices=["cif", "poscar"], nargs="*", help="Choose formats for the output structures to be saved in.", default=["poscar"])
parser.add_argument("--symprec", nargs=1, type=float, help="Symmetry precision when finding space group and Wyckoff positions.", default=[1e-05])
args = parser.parse_args()
if not args.files:
	print("Provide a structure file")
elif not args.output:
	print("Provide output path")
elif not args.save_format:
	print("Provide save format")
elif not args.symprec:
	print("Provide symmetry precision value")
elif not args.subgroup:
	print("Provide subgroups to transform structure into.")
else:
	import pathfinder
	pathfinder_obj = pathfinder.obj(program_path)
	orig_space_num, std_struct, subgroup_structs, trans_info_list, prefix_str = pathfinder_obj.get_subgroup_struct(args.files[0], args.subgroup, args.symprec[0])
	pathfinder_obj.output_subgroup(prefix_str, orig_space_num, std_struct, subgroup_structs, trans_info_list, args.output[0], args.save_format)