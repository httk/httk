import numpy as np
from httk.core.basic import *
from httk.core.httkobject import HttkObject, HttkPluginPlaceholder, httk_typed_property, httk_typed_property_resolve, httk_typed_property_delayed, httk_typed_init
from httk.atomistic.assignments import Assignments
from httk.atomistic.representativesites import RepresentativeSites
from httk.atomistic.cell import Cell

class SimpleStructure(HttkObject):
    def __init__(self, cell_basis=None, cell_parameters=None, cell_niggli=None, cell_metric=None, cell_volume=None, scale=1, sites_fractional=None, sites_cartesian=None, species=None, species_sites=None):
        self.cell_basis = cell_basis
        self.cell_parameters = cell_parameters
        self.cell_niggli = cell_niggli
        self.cell_metric = cell_metric
        self.scale = scale
        self.sites_fractional = sites_fractional
        self.sites_cartesian = sites_cartesian
        self.species = species
        self.species_sites = species_sites
        self.cell_volume = cell_volume
    
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
        if cell_parameters:
            if type(cell_parameters) is list and len(cell_parameters) == 6:
                cell_parameters = {"a": cell_parameters[0], "b": cell_parameters[1], "c": cell_parameters[2], "alpha": cell_parameters[3], "beta": cell_parameters[4], "gamma": cell_parameters[5]}
            if type(cell_parameters) is not dict:
                print("cell_parameters error")
        
        return cls(cell_basis, cell_parameters, cell_niggli, cell_metric, cell_volume, scale, sites_fractional, sites_cartesian, species, species_sites)