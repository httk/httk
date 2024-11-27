import numpy as np
from httk.core.basic import *
from httk.atomistic.simplestructure import SimpleStructure

class SymmetryStructure(SimpleStructure):
    def __init__(self, wyckoff):
        self._wyckoff = wyckoff