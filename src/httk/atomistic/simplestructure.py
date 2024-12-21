import numpy as np
from httk.core.basic import *
from httk.core.httkobject import HttkObject

class SimpleStructure(HttkObject):
    def __init__(self, cell_lattice_vectors=None, cell_parameters=None, cell_niggli=None, cell_metric=None, scale=None, sites_fractional=None, sites_cartesian=None, species=None, species_sites=None, species_sites_numbers=None):
        self._cell_lattice_vectors = cell_lattice_vectors
        self._cell_parameters = cell_parameters
        self._cell_niggli = cell_niggli
        self._cell_metric = cell_metric
        self._scale = scale
        self._sites_fractional = sites_fractional
        self._sites_cartesian = sites_cartesian
        self._species = species
        self._species_sites = species_sites
        self._species_sites_numbers = species_sites_numbers
    
    @classmethod
    def create(cls, cell_lattice_vectors=None, cell_parameters=None, cell_niggli=None, cell_metric=None, scale=None, sites_fractional=None, sites_cartesian=None, species=None, species_sites=None):
        if cell_lattice_vectors:
            if type(cell_lattice_vectors) is not list:
                cell_lattice_vectors = list(cell_lattice_vectors)
            if len(cell_lattice_vectors) == 3:
                all_vectors_correct = True
                i = 0
                while i < 3:
                    if type(cell_lattice_vectors[i]) is not list:
                        cell_lattice_vectors[i] = list(cell_lattice_vectors[i])
                    if len(cell_lattice_vectors[i]) != 3:
                        all_vectors_correct = False
                        break
                    i += 1
                if not all_vectors_correct:
                    print("cell_lattice_vectors error")
        else:
            if cell_parameters:
                if type(cell_parameters) is list and len(cell_parameters) == 6:
                    cell_parameters = {"a": cell_parameters[0], "b": cell_parameters[1], "c": cell_parameters[2], "alpha": cell_parameters[3], "beta": cell_parameters[4], "gamma": cell_parameters[5]}
                if type(cell_parameters) is not dict:
                    print("cell_parameters error")
        if sites_fractional is None and sites_cartesian is None:
            print("provide sites!")
        if species_sites is None and species is not None:
            species_sites = []
            for k, v in species:
                species_sites += [k]*v
        if species is None and species_sites is not None:
            species = {}
            for atom in species_sites:
                if atom not in species:
                    species[atom] = 1
                else:
                    species[atom] += 1
        return cls(cell_lattice_vectors, cell_parameters, cell_niggli, cell_metric, scale, sites_fractional, sites_cartesian, species, species_sites)

    @property
    def sites_cartesian(self):
        if self._sites_cartesian is None:
            self._sites_cartesian = (self._cell_lattice_vectors.T @ self._sites_fractional.T).T
        return self._sites_cartesian

    @property
    def sites_fractional(self):
        if self._sites_fractional is None:
            self._sites_fractional = self._cell_lattice_vectors.inv() @ self._sites_cartesian
        return self._sites_fractional

    @property
    def scale(self):
        if self._scale is None:
            if self._scale is not None:
                self._scale = abs(self._volume / self._cell_lattice_vectors.det()) # Some calculation here
        return self._scale
    
    @property
    def cell_lattice_vectors(self):
        return self._cell_lattice_vectors
    
    @property
    def cell_parameters(self):
        if self._cell_parameters is None:
            self._cell_parameters = self._cell_lattice_vectors # some transformation function
        return self._cell_parameters
    
    @property
    def cell_niggli(self):
        if self._cell_niggli is None:
            self._cell_niggli = self._cell_lattice_vectors # some transformation function
        return self._cell_niggli
    
    @property
    def cell_metric(self):
        if self._cell_metric is None:
            self._cell_metric = self._cell_lattice_vectors # some transformation function
        return self._cell_metric
    
    def get_volume(self):
        return abs(self._scale * self._cell_lattice_vectors.det()) # Some calculation here
    
    def get_formula(self):
        return self._species # some calculation here
    
    def get_atomic_formula(self, reduced=True, ones=True, sorted=True):
        formula_str = ""
        atoms_counts = {}
        counts_gcd = 1
        for atom in self._species:
            atoms_counts[atom["chemical_symbols"][0]] = self._species_sites.count(atom["chemical_symbols"][0])
        species_simple = list(atoms_counts.keys())
        if sorted:
            species_simple.sort()
        if reduced:
            counts_gcd = np.gcd.reduce(list(atoms_counts.values()))
        for key in species_simple:
            formula_str += key
            if atoms_counts[key]/counts_gcd > 1 or ones:
                formula_str += str(atoms_counts[key]/counts_gcd)
        return formula_str
    def get_species_copy(self):
        species_copy = []
        for specie in self._species:
            new_specie = {}
            for key, val in specie.items():
                if isinstance(val, list):
                    new_specie[key] = []
                    for list_val in val:
                        new_specie[key].append(list_val)
                else:
                    new_specie[key] = val
            species_copy.append(new_specie)
        return species_copy
    
    def write_to_poscar(self, output_name, first_line=None):
        pass