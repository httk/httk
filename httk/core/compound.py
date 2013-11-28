# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2013 Rickard Armiento
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

from htdata import periodictable
from fracvector import FracVector
from structure import Structure
from structureutils import *
from httk.crypto import tuple_to_hexhash
        
class Compound(object):
    """
    Class for basically any "basic system". (In technical terms, a compound is an aristotype, which should be referenced 
    in any type of work that deals with a hettotype.)
    
    Most compounds will have a basic_structure, but it is conceiveable to have basic_structure = None for
    a system where no structure is known, or for some reason impossible to express with a structure object.
    
    (This is the reason formula and abtract_formula is also present here, and not just referenced via basic_structure.)
    """       
    def __init__(self, source_computation, name, names, basic_structure,
                 formula, abstract_formula, formula_parts, element_count, spacegroup_number, tags, 
                 extended, extensions, periodicity, refs):

        self.source_computation = source_computation
        self.name = name
        self.names = names
        self.basic_structure = basic_structure
        self.formula =formula
        self.abstract_formula = abstract_formula
        self.formula_parts =formula_parts
        self.element_count = element_count
        self.spacegroup_number = spacegroup_number
        self.refs = refs
        self.tags = tags
        self.extended = extended
        self.extensions = extensions
        self.periodicity = periodicity
         
        self._hexhash = None
    
    @classmethod    
    def create(cls, source_computation, basic_structure = None, formula=None, abstract_formula=None, main_name=None, 
               names=None, refs=None, tags={}):

        basic_structure = Structure.use(basic_structure)

        if basic_structure==None:
            raise Exception("Compound creation without structure is not implemented yet, sorry.")
        
        sg_number = basic_structure.spacegroup_number
        basic_structure = Structure.use(basic_structure)

        #structures = [Structure.use(x) for x in structures if x != None]
          
        return Compound(source_computation, main_name, names, basic_structure,
                 basic_structure.formula,
                 basic_structure.abstract_formula,
                 basic_structure.normalized_formula_parts,
                 basic_structure.element_count, sg_number, tags, 
                 basic_structure.extended, basic_structure.extensions, basic_structure.periodicity, refs)

    @classmethod
    def use(cls,old):
        if isinstance(old,Compound):
            return old
        else:
            try:
                return old.to_Compound()
            except Exception as e:    
                raise Exception("Compound.use: unknown input:"+str(e)+" object was:"+str(old))
        
    def to_tuple(self):
        return self.basic_structure.to_tuple()
    
    @property
    def hexhash(self):
        if self._hexhash == None:
            self._hexhash = tuple_to_hexhash(self.to_tuple())
        return self._hexhash
    
    
    