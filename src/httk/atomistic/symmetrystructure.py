from httk.core.basic import *
from httk.atomistic.simplestructure import SimpleStructure

class SymmetryStructure(SimpleStructure):
    def __init__(self,
                 cell_lattice_vectors=None,
                 cell_parameters=None,
                 cell_niggli=None,
                 cell_metric=None,
                 scale=None,
                 sites_fractional=None,
                 sites_cartesian=None,
                 species=None,
                 species_sites=None,
                 species_sites_numbers=None,
                 wyckoffs=None,
                 space_number=None,
                 num_of_atoms=None):
        SimpleStructure.__init__(self, cell_lattice_vectors, cell_parameters, cell_niggli, cell_metric, scale, sites_fractional, sites_cartesian, species, species_sites, species_sites_numbers)
        self._wyckoffs = wyckoffs
        self._space_number = space_number
        self._num_of_atoms = num_of_atoms
    
    def __str__(self):
        return_str = ""
        return_str += "Space group number: "+str(self._space_number)+"\n"
        return_str += "Wyckoff\n"
        return_str += "Atom\tLetter\tNum\tFree_degr\tBasis\n"
        for wyckoff in self._wyckoffs:
            return_str += str(wyckoff["atom"])+"\t"+str(wyckoff["letter"])+"\t"+str(wyckoff["multiplicity"])+"\t"+", ".join(str(x)[0] for x in wyckoff["freedom_degr"])+"\t\t"+", ".join(str(round(x, 2)) for x in wyckoff["basis"])+"\n"
        return return_str