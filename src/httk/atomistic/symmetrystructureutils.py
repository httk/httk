from httk.atomistic.symmetrystructure import SymmetryStructure
import numpy as np
import spglib, json, sys
from os.path import join, dirname, abspath
from httk.atomistic.data.symmetry_wyckoff import Spacegroup
from httk.atomistic.pathfinderutils import compare_list_of_coords

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
    return SymmetryStructure(cell_lattice_vectors=dataset2["std_lattice"],
                             cell_parameters=None,
                             cell_niggli=None,
                             cell_metric=None,
                             scale=1,
                             sites_fractional=dataset2["std_positions"],
                             sites_cartesian=None,
                             species=simple_struct._species,
                             species_sites=None,
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