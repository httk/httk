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

from httk.core.httkobject import HttkObject, httk_typed_init, httk_typed_property
from httk.core.basic import is_sequence
from data import periodictable
from httk.core import FracVector, FracScalar
from assignment import Assignment


class SiteAssignment(HttkObject):

    """
    Represents a possible vector of assignments
    """
   
    @httk_typed_init({'assignments': [Assignment]}, index=['assignments'])
    def __init__(self, assignments):
        """
        Private constructor, as per httk coding guidelines. Use SiteAssignments.create instead.
        """
        self.assignments = assignments
            
    @classmethod
    def create(cls, assignments=None):
        """
        Create a new assignment object, 

       assignments: a list-style object with one entry per 'atom type'. Any sensible type accepted, most notably, 
                     integers (for atom number)
        """        
        if isinstance(assignments, SiteAssignment):
            return assignments

        if isinstance(assignments, dict):
            if 'assignments' in assignments:
                assignments = assignments['assignments']
            else:
                #raise Exception("Assignments.create: assignments is a dict, but does not contain the necessary key.")
                assignments = [Assignment.create(assignments)]

        newassignments = []
        if is_sequence(assignments):
            for x in assignments:
                if not isinstance(x, dict) and is_sequence(x):
                    for y in x:
                        newassignments += [Assignment.use(y)]
                else:
                    newassignments += [Assignment.use(x)]
        else:
            newassignments = [Assignment.use(assignments)]

        ratiosum = 0
        for a in newassignments:
            ratiosum += a.ratio

        if ratiosum > 1:
            print "Ratiosum:", ratiosum
            print "Assignmnets:", assignments
            raise Exception("siteassignment.create: sum of ratios for one site larger than 1, broken structure.")
        
        return cls(newassignments)

    @classmethod
    def use(cls, old):
        if isinstance(old, SiteAssignment):
            return old
        try:
            return old.to_SiteAssignment()
        except Exception:
            pass   
        return cls.create(assignments=old)

    def to_basis(self):
        return self.basis    

    @httk_typed_property([int])
    def atomic_numbers(self):
        return [x.atomic_number for x in self.assignments]

    @httk_typed_property([str])
    def symbols(self):
        return [x.symbol for x in self.assignments]

    @httk_typed_property([FracScalar])
    def ratios(self):
        return [x.ratio for x in self.assignments]

    def __len__(self):
        return len(self.assignments)

    def __getitem__(self, key):
        return self.assignments[key]

    def get_extensions(self):
        extensions = set()
        for a in self.assignments:
            extensions = extensions | set(a.get_extensions())
        extensions = sorted(extensions)
        return extensions

    @httk_typed_property(str)
    def symbol(self):
        if len(self.assignments) == 1:
            return self.assignments[0].symbol
        else:            
            return "["+",".join(["%s%.2f" % (str(x.symbol), x.ratio) for x in self.assignments])+"]"

    @httk_typed_property(FracScalar)
    def ratio(self):
        if len(self.assignments) == 1:
            return self.assignments[0].ratio
        else:
            return FracScalar.create(-1)

    @httk_typed_property(str)
    def atomic_number(self):
        if len(self.assignments) == 1:
            return self.assignments[0].atomic_number
        else:
            return 0


#     @classmethod
#     def use(cls,old):
#         if isinstance(old,Assignments):
#             return old
#         try:
#             return old.to_Assignments()
#         except Exception:
#             pass   
#         return cls.create(assignments=old)
# 
#     def to_basis(self):
#         return self.basis    
# 
#     @property
#     def integers(self):
#         return [x.to_integer() for x in self.siteassignments]
# 
#     @property
#     def symbols(self):
#         if self.extended == True:
#             raise Exception("Symbols of extended structure not implemented (yet?).")
#         return [periodictable.atomic_symbol(x) for x in self.elements]
# #        return [y.to_symbol() for x in self.siteassignments for y in x.as_list()]
# 
#     @property
#     def ratios(self):
#         if self.extended:
#             print "Not implemented yet"
#             
#         return FracVector.create([1]*len(self.elements))
# 
#     def __len__(self):
#         return len(self.siteassignments)
# 
#     def __getitem__(self,key):
#         return self.assignments[key]


def main():
    pass

if __name__ == "__main__":
    main()
    
    
