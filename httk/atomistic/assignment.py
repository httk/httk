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

from httk.core import HttkObject, httk_typed_init, httk_typed_property
from data import periodictable
from httk.core import FracVector, FracScalar


class Assignment(HttkObject):

    """
    Represents a possible vector of assignments
    """
    @httk_typed_init({'atomic_number': int, 'weight': FracScalar, 'ratio': FracScalar, 'magnetic_moment': (FracScalar, 1, 3)}, index=['atomic_number', 'weight', 'ratio'])
    def __init__(self, atomic_number, weight, ratio, magnetic_moment):
        """
        Private constructor, as per httk coding guidelines. Use Assignment.create instead.
        """    
        self.atomic_number = atomic_number
        self.weight = weight
        self.ratio = ratio
        self.magnetic_moment = magnetic_moment
            
    @classmethod
    def create(cls, siteassignment=None, atom=None, weight=None, ratio=None, magnetic_moment=[None, None, None]):
        """
        Create a new siteassignment object
          site: integer for the site number that this atom is assigned to
          atomic number or symbol 
        """
        #TODO: Convert assignments into strict internal representation
        if isinstance(siteassignment, Assignment):
            return siteassignment

        if isinstance(siteassignment, dict):
            if 'atom' in siteassignment:
                atom = siteassignment['atom']
            if 'weight' in siteassignment:
                weight = FracScalar.use(siteassignment['weight'])
            if 'ratio' in siteassignment:
                ratio = FracScalar.use(siteassignment['ratio'])
            if 'magnetic_moment' in siteassignment:
                magnetic_moment = siteassignment['magnetic_moment']
        elif siteassignment is not None:
            return cls(periodictable.atomic_number(siteassignment), None, FracScalar.create(1), [None, None, None])
                
        if atom is None:
            raise Exception("SiteAssignment needs at least an atom specification")

        atom = periodictable.atomic_number(atom)

        if magnetic_moment is None:
            magnetic_moment = [None, None, None]

        if ratio is None:
            ratio = FracScalar.create(1)
                
        return cls(atom, weight, ratio, magnetic_moment)

    def get_extensions(self):
        extensions = []
        if self.weight is not None:
            extensions += ['isotope']
        if self.ratio is not None and self.ratio != 1:
            extensions += ['disordered']
        if self.magnetic_moment is not None and self.magnetic_moment != [None, None, None]:
            extensions += ['magnetic_moments']
        return extensions

    @classmethod
    def use(cls, old):
        if isinstance(old, Assignment):
            return old
        try:
            return old.to_ssignment()
        except Exception:   
            pass        
        return cls.create(old)

    @httk_typed_property(str)
    def symbol(self):
        #if self.extended:
        #    raise Exception("SiteAssignment: cannot convert extended site assignment into just a symbol.")
        return periodictable.atomic_symbol(self.atomic_number)

    def get_weight(self):
        if self.weight is None:
            return periodictable.most_common_mass(self.atom)
        else:
            return self.weight


def main():
    pass

if __name__ == "__main__":
    main()
    
    
