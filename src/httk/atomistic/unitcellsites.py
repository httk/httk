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
from httk.core.basic import is_sequence
from cell import Cell
from spacegroup import Spacegroup
from sitesutils import *
from httk.core.httkobject import HttkObject, httk_typed_init
from sites import Sites


class UnitcellSites(Sites):

    """
    Represents any collection of sites in a unitcell
    """
    
    @httk_typed_init({'reduced_coords': (FracVector, 0, 3), 'counts': [int], 
                      'pbc': (bool, 1, 3)}, index=['counts', 'pbc'])
    def __init__(self, reduced_coordgroups=None, 
                 reduced_coords=None, 
                 counts=None, 
                 hall_symbol='P 1', pbc=None):
        """
        Private constructor, as per httk coding guidelines. Use Sites.create instead.
        """        
        if hall_symbol != 'P 1' and hall_symbol is not None:
            raise Exception("Attempt to create FullSites object with other hall symbol than P 1, hall_symbol was:"+str(hall_symbol))
        
        super(UnitcellSites, self).__init__(reduced_coordgroups=reduced_coordgroups, 
                                            reduced_coords=reduced_coords, 
                                            counts=counts, 
                                            hall_symbol='P 1', pbc=pbc)

    @property
    def total_number_of_atoms(self):
        return sum(self._counts)

    def __str__(self):
        return "<UnitcellSites:\n"+"\n".join(["".join(["    %.8f %.8f %.8f\n" % (x[0], x[1], x[2]) for x in y]) for y in self.reduced_coordgroups.to_floats()])+">" 

                                        
def main():
    pass


if __name__ == "__main__":
    main()




