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
from .signature import Signature, SignatureKey
from .code import Code
from .project import Project
from .reference import Reference


class Computation(HttkObject):

    """
    Object for keeping track of httk data about a specific computation run
    """
    @httk_typed_init({'computation_date': str, 'description': str, 'code': Code, 
                      'manifest_hash': str, 'signatures': [Signature], 'keys': [SignatureKey], 'relpath': str,
                      'project_counter': int},
                     index=['computation_date', 'added_date', 'description', 'code', 'manifest_hexhash',
                            'signatures', 'keys', 'project_counter'])
    def __init__(self, computation_date, description, code, 
                 manifest_hash, signatures, keys, relpath, project_counter, added_date=None):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """
        self.computation_date = computation_date
        self._added_date = added_date
        self.description = description
        self.code = code
        self.manifest_hash = manifest_hash
        self.signatures = signatures
        self.keys = keys
        self.relpath = relpath
        self.project_counter = project_counter

        self._projects = None
        self._tags = None
        self._refs = None
                
        self._codependent_callbacks = []
        self._codependent_data = []
        self._codependent_info = [{'class': ComputationProject, 'column': 'computation', 'add_method': 'add_projects'},
                                  {'class': ComputationTag, 'column': 'structure', 'add_method': 'add_tags'},
                                  {'class': ComputationRef, 'column': 'structure', 'add_method': 'add_refs'}]        
        
    @classmethod
    def create(cls, computation_date, description, code, manifest_hash, signatures, keys,
               project_counter, relpath, added_date=None):
        """
        Create a Computation object.
        """
        return Computation(computation_date=computation_date, description=description,
                           code=code, manifest_hash=manifest_hash, signatures=signatures, keys=keys,
                           relpath=relpath, project_counter=project_counter,
                           added_date=added_date)

    @httk_typed_property(str)
    def added_date(self):
        return self._added_date

    def _fill_codependent_data(self):
        self._tags = {}
        self._refs = []
        for x in self._codependent_callbacks:
            x(self)

    def add_tag(self, tag, val):
        if self._tags is None:
            self._fill_codependent_data()
        new = ComputationTag(self, tag, val)
        self._tags[tag] = new
        self._codependent_data += [new]

    def add_tags(self, tags):
        for tag in tags:
            if isinstance(tags, dict):
                tagdata = tags[tag]
            else:
                tagdata = tag
            if isinstance(tagdata, ComputationTag):
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
        if isinstance(ref, ComputationRef):
            refobj = ref.reference
        else:
            refobj = ComputationRef.use(ref)
        new = ComputationRef(self, refobj)
        self._refs += [new]
        self._codependent_data += [new]

    def add_refs(self, refs):
        for ref in refs:
            self.add_ref(ref)

    def get_projects(self):
        if self._projects is None:
            self._fill_codependent_data()
        return self._projects

    def add_project(self, project):
        if self._projects is None:
            self._fill_codependent_data()
        if isinstance(project, ComputationProject):
            projectobj = project.reference
        else:
            projectobj = ComputationProject.create(self, project)
        new = ComputationProject(self, projectobj)
        self._projects += [new]
        self._codependent_data += [new]

    def add_projects(self, projects):
        for project in projects:
            self.add_ref(project)


class ComputationTag(HttkObject):

    @httk_typed_init({'computation': Computation, 'tag': str, 'value': str},
                     index=['computation', 'tag', ('tag', 'value'), ('computation', 'tag', 'value')], skip=['hexhash'])    
    def __init__(self, computation, tag, value):
        self.tag = tag
        self.computation = computation
        self.value = value

    def __str__(self):
        return "(Tag) "+self.tag+": "+self.value+""


class ComputationRef(HttkObject):

    @httk_typed_init({'computation': Computation, 'reference': Reference}, index=['structure', 'reference'], skip=['hexhash'])        
    def __init__(self, computation, reference):
        self.computation = computation
        self.reference = reference

    def __str__(self):
        return str(self.reference)


class ComputationRelated(HttkObject):

    """
    Object for keeping track of httk data about a specific computation run
    """
    @httk_typed_init({'main_computation': Computation, 'other_computation': Computation, 'relation': str},
                     index=['main_computation', 'other_computation', 'relation'])
    def __init__(self, main_computation, other_computation, relation):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """    
        self.main_computation = main_computation
        self.other_computation = other_computation
        self.relation = relation
        
    @classmethod
    def create(cls, main_computation, other_computation, relation):
        """
        Create a Computation object.
        """        
        return cls(main_computation, other_computation, relation)


class ComputationProject(HttkObject):

    """
    """
    @httk_typed_init({'computation': Computation, 'project': Project},
                     index=['computation', 'project'])
    def __init__(self, computation, project):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """
        self.computation = computation
        self.project = project
        
    @classmethod
    def create(cls, computation, project):
        """
        Create a Computation object.
        """
        return cls(computation, project)


class Result(HttkObject):

    """
    Intended as a base class for results tables for computations
    """
    @httk_typed_init({'computation': Computation}, index=['computation'])
    def __init__(self, computation):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """
        self.computation = computation
        
    @classmethod
    def create(cls, computation):
        """
        Create a Computation object.
        """
        return cls(computation)


def main():
    pass

if __name__ == "__main__":
    main()

