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
from httk.atomistic import Structure, StructureTag, StructureRef
from httk.core.reference import Reference
from httk.core.computation import Computation
from httk.core import FracScalar


class Compound(HttkObject):

    """
    """   

    @httk_typed_init({'element_wyckoff_sequence': str, 'formula': str, 'spacegroup_number': int, 'extended': bool, 
                      'extensions': [str], 'pbc': (bool, 1, 3)}, 
                     index=['element_wyckoff_sequence', 'anonymous_wyckoff_sequence', 'wyckoff_sequence', 'formula', 'anonymous_formula',
                            'spacegroup_number', 'extended', 'formula_symbols', 'formula_counts', 'extensions'])
    def __init__(self, element_wyckoff_sequence, formula, spacegroup_number, extended, extensions,
                 wyckoff_sequence, anonymous_wyckoff_sequence, anonymous_formula, 
                 formula_symbols, formula_counts, pbc):
        """
        Private constructor, as per httk coding guidelines. See *.create classmethod instead.
        """    
        self.element_wyckoff_sequence = element_wyckoff_sequence
        self.formula = formula
        self.spacegroup_number = spacegroup_number
        self.extended = extended
        self.extensions = extensions
        self.pbc = pbc

        self._anonymous_wyckoff_sequence = anonymous_wyckoff_sequence
        self._anonymous_formula = anonymous_formula
        self._wyckoff_sequence = wyckoff_sequence
        self._formula_symbols = formula_symbols
        self._formula_counts = formula_counts
         
        self._tags = None
        self._refs = None
        self._names = None
        self._codependent_callbacks = []
        self._codependent_data = []
        self._codependent_info = [{'class': CompoundName, 'column': 'compound', 'add_method': 'add_names'},
                                  {'class': CompoundTag, 'column': 'compound', 'add_method': 'add_tags'},
                                  {'class': CompoundRef, 'column': 'compound', 'add_method': 'add_refs'}]

    @classmethod
    def create(cls, base_on_structure=None, lift_tags=True, lift_refs=True):
        """
        struct: Structure object which forms the basis of this object
        """                  
        if base_on_structure is not None:
            struct = base_on_structure
            new = cls(element_wyckoff_sequence=struct.element_wyckoff_sequence,
                      formula=struct.formula, spacegroup_number=struct.spacegroup_number,
                      extended=struct.extended, extensions=struct.extensions,
                      wyckoff_sequence=struct.wyckoff_sequence, anonymous_wyckoff_sequence=struct.anonymous_wyckoff_sequence,
                      anonymous_formula=struct.anonymous_formula, formula_symbols=struct.formula_symbols,
                      formula_counts=struct.formula_counts,
                      pbc=struct.pbc)                   
            tags = base_on_structure.get_tags()
            names = []
            keeptags = {}
            for tag in tags:
                if tag == 'Name' or tag == 'name':
                    names += [tags[tag].value]
                else:
                    keeptags[tag] = tags[tag]            
            new.add_names(names)
            if lift_tags:
                new.add_tags(keeptags)
            if lift_refs:
                new.add_refs(base_on_structure.get_refs())
            return new
        raise Exception("Compound.create: not enough info given.")

    @httk_typed_property([str])
    def formula_symbols(self):
        return self._formula_symbols

    @httk_typed_property(int)
    def number_of_elements(self):
        seen = {}
        for symbol in self._formula_symbols:
            seen[symbol] = True
        return len(seen)

    @httk_typed_property([FracScalar])     
    def formula_counts(self):
        return self._formula_counts
    
    @httk_typed_property(str)
    def wyckoff_sequence(self):
        return self._wyckoff_sequence

    @httk_typed_property(str)
    def anonymous_wyckoff_sequence(self):
        return self._anonymous_wyckoff_sequence

    @httk_typed_property(str)
    def anonymous_formula(self):
        return self._anonymous_formula

    def _fill_codependent_data(self):
        self._tags = {}
        self._refs = []
        self._names = []
        for x in self._codependent_callbacks:
            x(self)            

    def add_tag(self, tag, val):
        if self._tags is None:
            self._fill_codependent_data()
        new = CompoundTag(self, tag, val)
        self._tags[tag] = new
        self._codependent_data += [new]

    def add_tags(self, tags):
        for tag in tags:
            if isinstance(tags, dict):
                tagdata = tags[tag]
            else:
                tagdata = tag
            if isinstance(tagdata, CompoundTag):
                self.add_tag(tagdata.tag, tagdata.value)
            if isinstance(tagdata, StructureTag):
                self.add_tag(tagdata.tag, tagdata.value)
            else:
                self.add_tag(tag, tagdata)

    def get_tags(self):
        if self._tags is None:
            self._fill_codependent_data()
        return self._tags

    def get_tag(self, tag):
        if self._tags is None:
            self._fill_codependent_data()
        return self._tags[tag]

    def get_refs(self):
        if self._refs is None:
            self._fill_codependent_data()
        return self._refs

    def add_ref(self, ref):        
        if self._refs is None:
            self._fill_codependent_data()
        if isinstance(ref, CompoundRef):
            refobj = ref.reference
        if isinstance(ref, StructureRef):
            refobj = ref.reference
        else:
            refobj = Reference.use(ref)
        new = CompoundRef(self, refobj)
        self._refs += [new]
        self._codependent_data += [new]

    def add_refs(self, refs):
        for ref in refs:
            self.add_ref(ref)

    def get_names(self):
        if self._names is None:
            self._fill_codependent_data()
        return self._names

    def add_name(self, name):        
        if self._names is None:
            self._fill_codependent_data()
        if isinstance(name, CompoundName):
            name = name.name
        new = CompoundName(self, name)
        self._names += [new]
        self._codependent_data += [new]

    def add_names(self, names):
        for name in names:
            self.add_name(name)


class CompoundTag(HttkObject):                               

    @httk_typed_init({'compound': Compound, 'tag': str, 'value': str}, index=['compound', 'tag', ('tag', 'value'), ('compound', 'tag', 'value')], skip=['hexhash'])    
    def __init__(self, compound, tag, value):
        self.tag = tag
        self.compound = compound
        self.value = value

    def __str__(self):
        return "(Tag) "+self.tag+": "+self.value+""


class CompoundRef(HttkObject):

    @httk_typed_init({'compound': Compound, 'reference': Reference}, index=['compound', 'reference'], skip=['hexhash'])        
    def __init__(self, compound, reference):
        self.compound = compound
        self.reference = reference

    def __str__(self):
        return str(self.reference)


class CompoundName(HttkObject):

    @httk_typed_init({'compound': Compound, 'name': str}, index=['compound', 'name'], skip=['hexhash'])        
    def __init__(self, compound, name):
        self.compound = compound
        self.name = name

    def __str__(self):
        return "[(CompoundName) "+str(self.name)+"]"


class CompoundStructure(HttkObject):

    @httk_typed_init({'compound': Compound, 'structure': Structure}, index=['compound', 'structure'], skip=['hexhash'])
    def __init__(self, compound, structure):
        self.structure = structure
        self.compound = compound

    @classmethod
    def create(cls, compound, structure):
        return cls(compound, structure)


class ComputationRelatedCompound(HttkObject):

    @httk_typed_init({'computation': Computation, 'compound': Compound}, index=['compound', 'computation'], skip=['hexhash'])
    def __init__(self, computation, compound):
        self.computation = computation
        self.compound = compound

    @classmethod
    def create(cls, computation, compound):
        return cls(computation, compound)


def main():
    print "Ok"

if __name__ == "__main__":
    main()
    
    
