from httk.core.basic import *
from httk.core.httkobject import HttkObject, HttkPluginPlaceholder, httk_typed_property, httk_typed_property_resolve, httk_typed_property_delayed, httk_typed_init
from httk.atomistic.assignments import Assignments
from httk.atomistic.representativesites import RepresentativeSites
from httk.atomistic.cell import Cell

class SimpleStructure(HttkObject):
    def __init__(self, cell_basis=None, cell_parameters=None, cell_niggli=None, cell_metric=None, scale=None, sites_fractional=None, sites_cartesian=None, species=None, species_sites=None):
        self.cell_basis = cell_basis
        self.cell_parameters = cell_parameters
        self.cell_niggli = cell_niggli
        self.cell_metric = cell_metric
        self.scale = scale
        self.sites_fractional = sites_fractional
        self.sites_cartesian = sites_cartesian
        self.species = species
        self.species_sites = species_sites
    
    @classmethod
    def create(cls, cell=None):
        pass