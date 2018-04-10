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

from .httkobject import HttkObject, httk_typed_init
from .reference import Reference


class Code(HttkObject):

    """
    Object for keeping track of httk data about a computer software or script
    """

    @httk_typed_init({'name': str, 'version': str}, index=['name', 'version'])
    def __init__(self, name, version):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """
        super(Code, self).__init__()
        self.name = name
        self.version = version

        self._tags = {}
        self._refs = []

        self._codependent_callbacks = []
        self._codependent_data = []
        self._codependent_info = [{'class': CodeTag, 'column': 'code', 'add_method': 'add_tags'},
                                  {'class': CodeRef, 'column': 'code', 'add_method': 'add_refs'}]
        
    @classmethod
    def create(cls, name, version, refs=None, tags=None):
        """
        Create a Computation object.
        """
        new = cls(name, version)
        if tags is not None:
            new.add_tags(tags)
        if refs is not None:
            new.add_refs(refs)
        return new

    def _fill_codependent_data(self):
        self._tags = {}
        self._refs = []
        for x in self._codependent_callbacks:
            x(self)

    def add_tag(self, tag, val):
        if self._tags is None:
            self._fill_codependent_data()
        new = CodeTag(self, tag, val)
        self._tags[tag] = new
        self._codependent_data += [new]

    def add_tags(self, tags):
        for tag in tags:
            if isinstance(tags, dict):
                tagdata = tags[tag]
            else:
                tagdata = tag
            if isinstance(tagdata, CodeTag):
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
        if isinstance(ref, CodeRef):
            refobj = ref.reference
        else:
            refobj = Reference.use(ref)
        new = CodeRef(self, refobj)
        self._refs += [new]
        self._codependent_data += [new]

    def add_refs(self, refs):
        for ref in refs:
            self.add_ref(ref)
    
    
class CodeTag(HttkObject):

    @httk_typed_init({'code': Code, 'tag': str, 'value': str},
                     index=['code', 'tag', ('tag', 'value'), ('structure', 'tag', 'value')], skip=['hexhash'])
    def __init__(self, structure, tag, value):
        self.tag = tag
        self.structure = structure
        self.value = value

    def __str__(self):
        return "(Tag) "+self.tag+": "+self.value+""


class CodeRef(HttkObject):

    @httk_typed_init({'code': Code, 'reference': Reference}, index=['code', 'reference'], skip=['hexhash'])
    def __init__(self, code, reference):
        self.code = code
        self.reference = reference

    def __str__(self):
        return str(self.reference)
    
    
def main():
    pass
    
if __name__ == "__main__":
    main()
    
    
