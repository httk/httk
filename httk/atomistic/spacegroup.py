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

from httk.core import HttkObject, httk_typed_init
from httk.core import FracVector
from spacegrouputils import *


class Spacegroup(HttkObject):

    """
    Represents a spacegroup
    """
    @httk_typed_init({'hall_symbol': [str]}, index=['hall_symbol'])
    def __init__(self, hall_symbol):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """    
        super(Spacegroup, self).__init__()
        self.hall_symbol = hall_symbol

    @classmethod
    def create(cls, spacegroup=None, hall_symbol=None, hm_symbol=None, spacegroupnumber=None, setting=None, symops=None):
        """
        Create a new spacegroup object, 
        
        Give ONE OF hall_symbol or spacegroup. 
        
        hall_symbol = a string giving the hall symbol of the spacegroup
        
        spacegroup = a spacegroup on any reasonable format that can be parsed, e.g.,
           an integer (spacegroup number)
           
        setting = if only a spacegroup number is given, this allows also specifying a setting.
        """        
        if isinstance(spacegroup, Spacegroup):
            return spacegroup

        #print "Creating spacegroup:",spacegroup, hall_symbol, hm_symbol, spacegroupnumber, setting, symops

        hall = None
        if hall_symbol is not None or hm_symbol is not None or spacegroupnumber is not None or setting is not None or symops is not None:
            halls = spacegroup_filter_specific(hall_symbol, hm_symbol, spacegroupnumber, setting, symops)
            if len(halls) == 1:
                hall = halls[0] 

        if hall is None and spacegroup is not None:
            hall = spacegroup_parse(spacegroup)
        
        if hall is not None:
            return cls(hall)
        
        raise Exception("Spacegroup.create: not enough input parameters given to create a spacegroup object.")

    @property
    def number_and_setting(self):
        return spacegroup_get_number_and_setting(self.hall_symbol)

    @property
    def number(self):
        return spacegroup_get_number_and_setting(self.hall_symbol)[0]


def main():
    pass

if __name__ == "__main__":
    main()
    
    
