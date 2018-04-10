# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2015 Rickard Armiento
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
import sys
from httk.core import FracVector
from httk.core.basic import is_sequence
from cellshape import CellShape
from spacegroup import Spacegroup
from sitesutils import *
from httk.core.httkobject import HttkObject, httk_typed_init, httk_typed_property


class Sites(HttkObject):

    """
    Represents any collection of sites in a unitcell
    """
    #@classmethod
    #def types(cls):
    #    return cls.types_declare(
    #                        (('reduced_coords',(FracVector,0,3)),('counts',[int]),('cell',Cell),('hall_symbol',str),('pbc',(bool,1,3))),
    #                         index=[])
    
    @httk_typed_init({'reduced_coords': (FracVector, 0, 3), 'counts': [int], 
                      'hall_symbol': str, 'pbc': (bool, 1, 3)},
                     index=['counts', 'hall_symbol', 'pbc'])
    def __init__(self, reduced_coordgroups=None, 
                 reduced_coords=None, 
                 counts=None, 
                 hall_symbol=None, pbc=None):
        """
        Private constructor, as per httk coding guidelines. Use Sites.create instead.
        """
        self._reduced_coordgroups = reduced_coordgroups
        self._reduced_coords = reduced_coords
        self._counts = counts
        self.hall_symbol = hall_symbol

        if pbc is None:
            self.pbc = (True, True, True)
        else:
            self.pbc = pbc 
                                        
    @classmethod
    def create(cls, sites=None, reduced_coordgroups=None, 
               reduced_coords=None, 
               counts=None, occupancies=None,
               spacegroup=None, hall_symbol=None, spacegroupnumber=None, setting=None,
               pbc=None, periodicity=None):
        """
        Create a new sites object
        """        
        if isinstance(sites, Sites):
            return cls(reduced_coords=sites.reduced_coords, counts=sites.counts, cell=sites.cell, spacegroupobj=sites.spacegroupobj, pbc=sites.pbc, refs=sites.refs, tags=sites.tags)

        if reduced_coordgroups is None and reduced_coords is None:
            raise Exception("Sites.create: no valid coordinate specifications given.")       

        if reduced_coordgroups is None and counts is None and occupancies is None:
            raise Exception("Sites.create: if giving coordinates, counts or occupancies must also be given.")       

        if reduced_coordgroups is None and counts is None and reduced_coords is not None and occupancies is not None:
            reduced_coordgroups, assignments = coords_and_occupancies_to_coordgroups_and_assignments(reduced_coords, occupancies)

        if spacegroup is not None or hall_symbol is not None or spacegroupnumber is not None or setting is not None:
            spacegroupobj = Spacegroup.create(spacegroup=spacegroup, hall_symbol=hall_symbol, spacegroupnumber=spacegroupnumber, setting=setting) 
            hall_symbol = spacegroupobj.hall_symbol
        else:
            hall_symbol = None
        
        if reduced_coordgroups is not None:
            reduced_coordgroups = FracVector.use(reduced_coordgroups)
        
        if reduced_coords is not None:
            reduced_coords = FracVector.use(reduced_coords)

        if reduced_coords is None and reduced_coordgroups is not None:
            reduced_coords = FracVector.chain_vecs(reduced_coordgroups)

        if pbc is None:
            if periodicity is not None:
                pbc = periodicity_to_pbc(periodicity)
            else:
                pbc = (True, True, True)

        if counts is None and reduced_coordgroups is not None:
            counts = [len(x) for x in reduced_coordgroups]

        if counts is None or reduced_coords is None:
            raise Exception("Sites.create: not enough information to create sites object.")

        sites = cls(reduced_coordgroups=reduced_coordgroups, 
                    reduced_coords=reduced_coords, 
                    counts=counts, 
                    hall_symbol=hall_symbol, pbc=pbc)

        return sites

    @classmethod
    def use(cls, old, cell=None, hall_symbol=None, periodicity=None):
        if isinstance(old, Sites):
            return old                
        try:
            return old.to_Sites()
        except Exception:
            pass 
        return cls.create(sites=old, cell=cell, hall_symbol=hall_symbol, periodicity=periodicity)        

    #@property
    #reduced_coordgroups: provided as member

    @property
    def reduced_coordgroups(self):
        if self._reduced_coordgroups is None:
            #if self._cartesian_coordgroups != None:
            #    self._reduced_coordgroups = coordgroups_cartesian_to_reduced(self._cartesian_coordgroups,self.cell.basis)
            if self._reduced_coords is not None:
                reduced_coordgroups = coords_and_counts_to_coordgroups(self._reduced_coords, self._counts)
                self._reduced_coordgroups = FracVector.use(reduced_coordgroups)
            #elif self._cartesian_coords != None:
            #    reduced_coordgroups = coords_and_counts_to_coordgroups(self._cartesian_coords,self._counts)
            #    self._reduced_coordgroups = coordgroups_cartesian_to_reduced(reduced_coordgroups,self.cell.basis)
        return self._reduced_coordgroups 

    def get_cartesian_coordgroups(self, cell):
        return coordgroups_reduced_to_cartesian(cell.basis, self.reduced_coordgroups)

    @property
    def counts(self):
        if self._counts is None:
            self._coords, self._counts = coordgroups_to_coords(self.reduced_coordgroups)
        return self._counts

    @property
    def reduced_coords(self):
        if self._reduced_coords is None:
            self._reduced_coords, self._counts = coordgroups_to_coords(self.reduced_coordgroups)
        return self._reduced_coords

    def get_cartesian_coords(self, scale):
        cartesian_coords, counts = coordgroups_to_coords(self.get_cartesian_coordgroups(scale))
        return cartesian_coords

    @httk_typed_property([int])
    def coords_groupnumber(self):
        out = []
        for i in range(len(self.counts)):
            out += [i]*self.counts[i]
        return out

    @httk_typed_property(str)
    def anonymous_formula(self):
        return anonymous_formula(self.counts)

    def clean(self):
        
        reduced_coordgroups = self.reduced_coordgroups.limit_denominator(5000000)
        reduced_coords = self.reduced_coords.limit_denominator(5000000)
            
        return self.__class__(reduced_coordgroups=reduced_coordgroups, 
                              reduced_coords=reduced_coords, 
                              counts=self.counts,  
                              hall_symbol=self.hall_symbol, pbc=self.pbc)

    @property
    def total_number_of_atoms(self):
        raise Exception("Sites: attempt to call total_number_of_atoms on generic site, needs unitcellsites or representativesites")

        
    #def tidy(self):
    #    return Sites(self._unique_coordgroups, self._uc_coordgroups, self.cell, self.hall_symbol, self.periodicity, self.refs, self.tags)

def main():
    pass

if __name__ == "__main__":
    main()


