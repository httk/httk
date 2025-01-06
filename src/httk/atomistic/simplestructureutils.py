from httk.atomistic.simplestructure import SimpleStructure

def convert_to_simplestruct(struct_obj):
    species = []
    species_at_sites = []
    species_at_sites_numbers = []
    fractional_coords = []
    for i in range(0, len(struct_obj.assignments.symbols)):
        species_at_sites += [struct_obj.assignments.symbols[i]]*len(struct_obj.uc_sites.reduced_coordgroups.to_floats()[i])
        species_at_sites_numbers += [struct_obj.assignments.atomic_numbers[i]]*len(struct_obj.uc_sites.reduced_coordgroups.to_floats()[i])
        fractional_coords += struct_obj.uc_sites.reduced_coordgroups.to_floats()[i]
        species.append({"name": struct_obj.assignments.symbols[i], "chemical_symbols": [struct_obj.assignments.symbols[i]], "atomic_numbers": [struct_obj.assignments.atomic_numbers[i]], "concentration": [1.0]})
    simple_obj = SimpleStructure(cell_lattice_vectors=struct_obj.uc_cell.basis.to_floats(), scale=1, sites_fractional=fractional_coords, species=species, species_sites=species_at_sites, species_sites_numbers=species_at_sites_numbers)
    return simple_obj