import manageSettings
import argparse
import os
import sys
import time
settings = manageSettings.settings()
program_path = sys.path[0]
parser = argparse.ArgumentParser(prog="space group pathfinder", description="Program for finding path with most symmetries between two given space group structures.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("action", choices=["default", "calc"], help="default - Change and/or view default values.\ncalc - run path finding algorithm.")
parser.add_argument("-f", "--files", nargs=2, type=str, help="Files providing structures of start and end points in paths.")
parser.add_argument("-l", "--list", action="store_true", help="List default values.")
parser.add_argument("-u", "--update", action="store_true", help="Change default values.")
parser.add_argument("--output", nargs=1, help="Directory to save output in.", default=[settings.get_value("output")])
parser.add_argument("--save-format", choices=["cif", "poscar"], nargs="*", help="Choose formats for the output structures to be saved in.", default=settings.get_value("save-format"))
parser.add_argument("--depth", nargs=1, type=int, help="Search depth for path finding algorithm.", default=[settings.get_value("depth")])
parser.add_argument("--symprec", nargs=1, type=float, help="Symmetry precision when finding space group and Wyckoff positions.", default=[settings.get_value("symprec")])
parser.add_argument("--sub-type", nargs="*", choices=["t", "k"], help="Type of subgroup.", default=settings.get_value("sub-type"))
parser.add_argument("--max-path", nargs=1, type=int, help="Max size of structure at any point in the path. Size is number of atoms.", default=[settings.get_value("max-path")])
parser.add_argument("--max-orig", nargs=1, type=int, help="Max size of any provided structure. Size is number of atoms.", default=[settings.get_value("max-orig")])
parser.add_argument("--max-results", nargs=1, type=int, help="Max number of paths given in output.", default=[settings.get_value("max-results")])
parser.add_argument("--steps", nargs=1, type=int, help="Number of steps taken in linear interpolation generation.", default=[settings.get_value("steps")])
parser.add_argument("--subgroups", nargs="*", help="Choose specific subgroup(s) to search for. 'Any' for no choice.", default=settings.get_value("subgroups"))
parser.add_argument("--collision-threshold", nargs=1, type=float, help="Distance between atoms to deem as collision. Given in Ångström.", default=[settings.get_value("collision-threshold")])
parser.add_argument("--collision-level", type=int, choices=[0, 1, 2], nargs=1, help="How the program should handle collisions.\n0 - Skip detection checks completely.\n1 - Check and include warning, but don't exclude results. \n2 - Exclude results with collision unless unavoidable.", default=[settings.get_value("collision-level")])
parser.add_argument("--output-name", nargs=1, help="Name of generated output folder. Empty string for time stamp", default=[settings.get_value("output-name")])
args = parser.parse_args()
if args.action == "calc":
	if not args.files:
		print("Provide 2 files")
	elif not args.depth:
		print("Provide value of search depth")
	elif not args.output:
		print("Provide output path")
	elif not args.save_format:
		print("Provide save format")
	elif not args.symprec:
		print("Provide symmetry precision value")
	elif not args.sub_type:
		print("Provide subgroup type(s)")
	elif not args.max_path:
		print("Provide max size in path")
	elif not args.max_orig:
		print("Provide max size in input")
	elif not args.max_results:
		print("Provide max number of paths")
	elif not args.steps:
		print("Provide number of interpolation steps")
	elif not args.subgroups:
		print("Provide specific subgroup(s)")
	elif not args.collision_threshold:
		print("Provide collision threshold")
	elif not args.collision_level:
		print("Provide collision detection level")
	elif not args.output_name:
		print("Provide output folder name")
	else:
		start_time = time.time()
		import pathfinder, socket
		prefix_str, start_orig, end_orig, paths_short, paths_main=pathfinder.get_paths(args.files[0], args.files[1], args.depth[0], args.symprec[0], args.sub_type, args.max_path[0], args.max_orig[0], args.max_results[0], args.steps[0], args.subgroups, args.collision_threshold[0], args.collision_level[0])
		if not os.path.exists(args.output[0]):
			os.makedirs(args.output[0])
		if paths_main != "no_path":
			hostname = socket.gethostname()
			end_time = time.time()
			elapsed_time = (end_time-start_time)
			input_values = {"depth": args.depth[0],
							"symprec": args.symprec[0],
							"sub-type": args.sub_type,
							"max-path": args.max_path[0],
							"max-orig": args.max_orig[0],
							"max-results": args.max_results[0],
							"steps": args.steps[0],
							"subgroups": args.subgroups,
							"collision-threshold": args.collision_threshold[0],
							"collision-level": args.collision_level[0],
							"save-format": args.save_format,
							"hostname": hostname,
							"computation time": elapsed_time}
			pathfinder.output_paths(prefix_str, start_orig, end_orig, paths_short, paths_main, args.output[0], args.save_format, args.output_name[0], input_values)
		elif args.output_name[0]:
			work_folder = os.path.join(args.output[0], args.output_name[0])
			os.makedirs(work_folder)

elif args.action == "default":
	if args.update:
		settings.set_value("output", args.output[0])
		settings.set_value("save-format", args.save_format)
		settings.set_value("depth", args.depth[0])
		settings.set_value("symprec", args.symprec[0])
		settings.set_value("sub-type", args.sub_type)
		settings.set_value("max-path", args.max_path[0])
		settings.set_value("max-orig", args.max_orig[0])
		settings.set_value("max-results", args.max_results[0])
		settings.set_value("steps", args.steps[0])
		settings.set_value("subgroups", args.subgroups)
		settings.set_value("collision-threshold", args.collision_threshold[0])
		settings.set_value("collision-level", args.collision_level[0])
		settings.set_value("output-name", args.output_name[0])
	if args.list:
		print(settings)