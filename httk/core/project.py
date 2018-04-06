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

from httk.core.httkobject import HttkObject, httk_typed_init
from .signature import SignatureKey
from .reference import Reference


class Project(HttkObject):

    """
    """    

    @httk_typed_init({'name': str, 'description': str, 'project_key': SignatureKey, 'keys': [SignatureKey]}, index=['name', 'description', 'key'])    
    def __init__(self, name, description, project_key, keys):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """    
        self.name = name
        self.description = description
        self.keys = keys
        self.project_key = project_key

        self._tags = None
        self._refs = None

        self._codependent_callbacks = []
        self._codependent_data = []
        self._codependent_info = [{'class': ProjectTag, 'column': 'project', 'add_method': 'add_tags'},
                                  {'class': ProjectRef, 'column': 'project', 'add_method': 'add_refs'}]
        
    @classmethod
    def create(cls, name, description, project_key, keys):
        """
        Create a Project object.
        """        
        return cls(name, description, project_key, keys)

    def _fill_codependent_data(self):
        self._tags = {}
        self._refs = []
        for x in self._codependent_callbacks:
            x(self)            

    def add_tag(self, tag, val):
        if self._tags is None:
            self._fill_codependent_data()
        new = ProjectTag(self, tag, val)
        self._tags[tag] = new
        self._codependent_data += [new]

    def add_tags(self, tags):
        for tag in tags:
            if isinstance(tags, dict):
                tagdata = tags[tag]
            else:
                tagdata = tag
            if isinstance(tagdata, ProjectTag):
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
        if isinstance(ref, ProjectRef):
            refobj = ref.reference
        else:
            refobj = Reference.use(ref)
        new = ProjectRef(self, refobj)
        self._refs += [new]
        self._codependent_data += [new]

    def add_refs(self, refs):
        for ref in refs:
            self.add_ref(ref)


class ProjectOwner(HttkObject):

    """
    """    

    @httk_typed_init({'project': Project, 'owner_key': SignatureKey}, index=['project', 'owner_key'])    
    def __init__(self, project, owner_key):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """    
        self.project = project
        self.owner_key = owner_key
        
    @classmethod
    def create(cls, project, owner):
        """
        Create a Project object.
        """        
        return cls(project, owner)

    
class ProjectTag(HttkObject):                               

    @httk_typed_init({'project': Project, 'tag': str, 'value': str}, index=['project', 'tag', ('tag', 'value'), ('project', 'tag', 'value')], skip=['hexhash'])    
    def __init__(self, project, tag, value):
        super(ProjectTag, self).__init__()
        self.tag = tag
        self.project = project
        self.value = value

    def __str__(self):
        return "(Tag) "+self.tag+": "+self.value+""


class ProjectRef(HttkObject):

    @httk_typed_init({'project': Project, 'reference': Reference}, index=['project', 'reference'], skip=['hexhash'])        
    def __init__(self, project, reference):
        super(ProjectRef, self).__init__()
        self.project = project
        self.reference = reference

    def __str__(self):
        return str(self.reference)
    

def main():
    pass

if __name__ == "__main__":
    main()
    
    
