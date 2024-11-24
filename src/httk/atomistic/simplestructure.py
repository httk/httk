import numpy as np
from httk.core.basic import *
from httk.core.httkobject import HttkObject, HttkPluginPlaceholder, httk_typed_property, httk_typed_property_resolve, httk_typed_property_delayed, httk_typed_init
from httk.atomistic.assignments import Assignments
from httk.atomistic.representativesites import RepresentativeSites
from httk.atomistic.cell import Cell

class SimpleStructure(HttkObject):
    def __init__(self, cell_basis=None, cell_parameters=None, cell_niggli=None, cell_metric=None, volume=None, scale=1, sites_fractional=None, sites_cartesian=None, species=None, species_sites=None):
        self._cell_basis = cell_basis
        self._cell_parameters = cell_parameters
        self._cell_niggli = cell_niggli
        self._cell_metric = cell_metric
        self._scale = scale
        self._sites_fractional = sites_fractional
        self._sites_cartesian = sites_cartesian
        self._species = species
        self._species_sites = species_sites
        self._volume = volume
    
    @classmethod
    def create(cls, cell_basis=None, cell_parameters=None, cell_niggli=None, cell_metric=None, scale=1, sites_fractional=None, sites_cartesian=None, species=None, species_sites=None):
        if cell_basis:
            if type(cell_basis) is not list:
                cell_basis = list(cell_basis)
            if len(cell_basis) == 3:
                all_vectors_correct = True
                i = 0
                while i < 3:
                    if type(cell_basis[i]) is not list:
                        cell_basis[i] = list(cell_basis[i])
                    if len(cell_basis[i]) != 3:
                        all_vectors_correct = False
                        break
                    i += 1
                if not all_vectors_correct:
                    print("cell_basis error")
            volume = abs(cell_basis.det())
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
        return cls(cell_basis, cell_parameters, cell_niggli, cell_metric, volume, scale, sites_fractional, sites_cartesian, species, species_sites)

    @property
    def sites_cartesian(self):
        if self._sites_cartesian is None:
            self._sites_cartesian = (self._cell_basis.T @ self._sites_fractional.T).T
        return self._sites_cartesian

    @property
    def sites_fractional(self):
        if self._sites_fractional is None:
            self._sites_fractional = self._cell_basis.inv() @ self._sites_cartesian
        return self._sites_fractional
    
    @property
    def volume(self):
        if self._volume is None:
            self._volume = abs(self.basis.det()) # Some calculation here
        return self._volume