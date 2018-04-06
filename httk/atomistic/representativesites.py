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
from httk.core import HttkObject, FracVector
from httk.core.basic import is_sequence, int_to_anonymous_symbol
from spacegroup import Spacegroup
from sitesutils import *
from httk.core.httkobject import HttkObject, httk_typed_init, httk_typed_property
from sites import Sites
from unitcellsites import UnitcellSites
from httk.atomistic.spacegrouputils import crystal_system_from_hall, lattice_symbol_from_hall, lattice_system_from_hall


class RepresentativeSites(Sites):

    """
    Represents any collection of sites in a unitcell
    """
    
    @httk_typed_init({'reduced_coords': (FracVector, 0, 3), 'counts': [int], 
                      'hall_symbol': str, 'pbc': (bool, 1, 3), 'wyckoff_symbols': [str], 'multiplicities': [int]},
                     index=['counts', 'hall_symbol', 'pbc', 'wyckoff_symbols',
                            'wyckoff_sequence', 'anonymous_wyckoff_sequence'])
    def __init__(self, reduced_coordgroups=None, 
                 cartesian_coordgroups=None, reduced_coords=None, 
                 cartesian_coords=None, counts=None,  
                 hall_symbol=None, pbc=None, wyckoff_symbols=None,
                 multiplicities=None):
        """
        Private constructor, as per httk coding guidelines. Use Sites.create instead.
        """
        super(RepresentativeSites, self).__init__(reduced_coordgroups=reduced_coordgroups, 
                                                  reduced_coords=reduced_coords, 
                                                  counts=counts,  
                                                  hall_symbol=hall_symbol, pbc=pbc)

        self.wyckoff_symbols = wyckoff_symbols
        self.multiplicities = multiplicities
    
    #TODO: Recreate multiplicities (and perhaps also wyckoff_symbols) if those are not given in construction
    @classmethod           
    def create(cls, sites=None, reduced_coordgroups=None, 
               reduced_coords=None, 
               counts=None, 
               spacegroup=None, hall_symbol=None, spacegroupnumber=None, setting=None,
               periodicity=None, wyckoff_symbols=None, multiplicities=None, occupancies=None, pbc=None):           

        sites = super(RepresentativeSites, cls).create(sites=sites, reduced_coordgroups=reduced_coordgroups, 
                                                       reduced_coords=reduced_coords, 
                                                       counts=counts, 
                                                       spacegroup=spacegroup, hall_symbol=hall_symbol, spacegroupnumber=spacegroupnumber, setting=setting,
                                                       periodicity=periodicity, occupancies=occupancies)
        #sites.wyckoff_symbols = wyckoff_symbols
        #sites._multiplicity = multiplicity
        #return sites
        return cls(reduced_coordgroups=sites.reduced_coordgroups, 
                   reduced_coords=sites.reduced_coords, 
                   counts=sites.counts,  
                   hall_symbol=sites.hall_symbol, pbc=sites.pbc, wyckoff_symbols=wyckoff_symbols,
                   multiplicities=multiplicities)

#     Comment: I thought the Wyckoff labels could be seen as derivable from the spacegroup + coodinates, but this is actually
#       not so simple. First, it really requires understanding of the accuracy of the coordinates (or else, they'd be incorrectly determined).
#       also, at least ISOTROPY's FINDSYM requires you to first fill the cell, which isn't implemented in a foolproof way yet in httk.
#       but... this means one MUST KNOW the Wyckoff labels at the time of creation of this object.
#     @httk_typed_property([str])
#     def wyckoff_symbols(self):
#         if self._wyckoff_symbols == None:
#             sys.stderr.write("Warning: need to run symmetry finder. This may take a while.\n")
#             coordgroups, wyckoff_symbols, reorder = structure_reduced_coordgroups_to_representative(self.reduced_coordgroups,self.normalized_cellobj,self.hall_symbol)
#             new_wyckoff_symbols = []
#             for i in range(len(reorder)):
#                 for j in range(len(reorder[i])):
#                     new_wyckoff_symbols += [wyckoff_symbols[i]]*len(self.reduced_coordgroups[j])
#             self._wyckoff_symbols = wyckoff_symbols
#         return self._wyckoff_symbols

#    @httk_typed_property([int])
#    def multiplicities(self):
#        #if self._multiplicities is None:
#        #    raise Exception("Representativesites.multiplicities: Not yet implemented getting multiplicities when not given.")
#        return self._multiplicities
                                        
    @httk_typed_property(str)
    def anonymous_wyckoff_sequence(self):
        if self.wyckoff_symbols is None:
            return None
        data = {}
        idx = 0
        for i in range(len(self.counts)):
            for j in range(self.counts[i]):
                #print "HERE",self.wyckoff_symbols,idx,i,j
                wsymb = self.wyckoff_symbols[idx]
                if wsymb == '&':
                    wsymb = 'zz'
                key = (wsymb, i)
                if key in data:
                    data[key] = (wsymb, data[key][1]+1, i)
                else:
                    data[key] = (wsymb, 1, i)
                idx += 1
        sortedcounts = sorted(data.values())

        symbol = ""
        seen = {}
        for i in range(len(sortedcounts)):
            if sortedcounts[i][2] in seen:
                s = seen[sortedcounts[i][2]]
            else:
                s = len(seen)
                seen[sortedcounts[i][2]] = s
            wsymb = sortedcounts[i][0]
            if wsymb == 'zz':
                wsymb = '&'
            symbol += str(sortedcounts[i][1])+wsymb+int_to_anonymous_symbol(s)
        return symbol

    @httk_typed_property(str)
    def wyckoff_sequence(self):
        if self.wyckoff_symbols is None:
            return None
        seen = {}
        for symbol in self.wyckoff_symbols:
            if symbol in seen:
                seen[symbol] += 1
            else:
                seen[symbol] = 1
        sortedsymbs = sorted(seen.keys())
        out = ""
        for symbol in sortedsymbs:
            if seen[symbol] > 1:  
                out += symbol+str(seen[symbol])
            else:
                out += symbol
        #print "OUT",out,sortedsymbs,seen
        #exit(0)
        return out

    @property
    def total_number_of_atoms(self):
        return sum(self._multiplicities)

    def get_uc_sites(self):
        filled_reduced_coordgroups = coordgroups_reduced_to_unitcell(self.reduced_coordgroups, self.hall_symbol)
        return UnitcellSites.create(reduced_coordgroups=filled_reduced_coordgroups, pbc=self.pbc)

    def clean(self):
        c = super(RepresentativeSites, self).clean()
        return self.__class__(reduced_coords=c.reduced_coords, counts=c.counts, 
                              hall_symbol=self.hall_symbol, pbc=c.pbc, wyckoff_symbols=self.wyckoff_symbols, multiplicities=self.multiplicities)

    @httk_typed_property(str)
    def lattice_symbol(self):
        return lattice_symbol_from_hall(self.hall_symbol)

    @property
    def lattice_system(self):
        return lattice_system_from_hall(self.hall_symbol)

    @httk_typed_property(str)
    def crystal_system(self):
        return crystal_system_from_hall(self.hall_symbol)

    def tidy(self):
        return sites_tidy(self)

    def __str__(self):
        return "<RepresentativeSites:\n"+"\n".join(["".join(["    %.8f %.8f %.8f\n" % (x[0], x[1], x[2]) for x in y]) for y in self.reduced_coordgroups.to_floats()])+">" 
                                        

def main():
    pass

if __name__ == "__main__":
    main()


