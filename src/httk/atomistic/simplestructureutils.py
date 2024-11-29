from httk.atomistic.simplestructure import SimpleStructure

def convert_to_simplestruct(struct_obj):
    cell = struct_obj.uc_cell
    assignments = struct_obj.assignments
    sites = struct_obj.uc_sites
    print(cell.normalization_scale.to_floats())
    print(cell.get_normalized().basis.to_floats())
    print(assignments.symbollists)
    print("\n".join(["".join(["    %.8f %.8f %.8f\n" % (x[0], x[1], x[2]) for x in y]) for y in sites.reduced_coordgroups.to_floats()]))
    simple_obj = SimpleStructure(cell_basis=cell.get_normalized().basis.to_floats(), scale=cell.normalization_scale.to_floats(), sites_fractional=sites, species=assignments)
    return simple_obj