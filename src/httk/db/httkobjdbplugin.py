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

from httk.core.httkobject import HttkPlugin, HttkObject, HttkPluginWrapper
from httk.db.storable import Storable


class HttkObjDbPlugin(HttkPlugin):
            
    def plugin_init(self, obj):
        self.obj = obj
        self.types = obj.types()
        self.object_name = self.types['name']
        self.keys = self.types['keys']
        self.keydict = dict(self.types['keys'])
        self.derived = self.types['derived']
        self.derived_keydict = dict(self.types['derived'])
        self.index = self.types['index']
        self.storable = Storable({"name": self.object_name, "keys": self.keys, "keydict": self.keydict, "index": self.index, 
                                  "derived": self.derived, "derived_keydict": self.derived_keydict})
        self.sid = None

    def store_codependent_data(self, store):
        for entry in self.obj.get_codependent_data():
            entry.db.store(store)

    def fetch_codependent_data(self, store):
        if hasattr(self.obj, '_codependent_info'):
            for c in self.obj._codependent_info:
                search = store.searcher()
                p = search.variable(c['class'])
                search.add(p.__getattr__(c['column']) == self.obj)
                search.output(p, 'object')
                results = list(search)
                if len(results) > 0:
                    getattr(self.obj, c['add_method'])([x[0][0] for x in results])
        
    def store(self, store, avoid_duplicate=True):
        self.storable.storable_init(store)
        if avoid_duplicate:
            if 'hexhash' in self.derived_keydict and hasattr(self.obj, 'hexhash'):
                hexhash = self.obj.hexhash
                p = self.storable.find_one(store, self.obj, 'hexhash', hexhash, self.types)
                if p is not None:
                    self.sid = p.db.sid
                    self.storable = p.db.storable
            else:
                search = store.searcher()
                # Order of variable definitions changed for database optimization
                definedvariables = []
                definedvariableidx = 0
                for variables in self.keys:
                    if issubclass(variables[1], HttkObject):
                        definedvariables += [search.variable(variables[1])]
                
                p = search.variable(self.obj.__class__)
                for variables in self.keys:
                    shouldbe = getattr(self.obj, variables[0])
                    if shouldbe is None:
                        search.add(p.__getattr__(variables[0]) is None)
                    elif issubclass(variables[1], HttkObject):
                        q = definedvariables[definedvariableidx]
                        definedvariableidx += 1
                        search.add(q.hexhash == shouldbe.hexhash)
                        search.add(p.__getattr__(variables[0]) == q)
                    else:
                        search.add(p.__getattr__(variables[0]) == shouldbe)
                search.output(p, 'object')
                results = list(search)
                if len(results) > 0:
                    p = results[0][0][0]
                    self.sid = p.db.sid
                    self.storable = p.db.storable
        
        data = {}
        for key in dict(self.keydict):
            data[key] = getattr(self.obj, key) 
        for key in self.derived_keydict:
            data[key] = getattr(self.obj, key) 

        if self.sid is not None:
            self.storable.storable_init(store, updatesid=-self.sid, **data) 
        else:
            self.storable.storable_init(store, **data) 
        self.sid = self.storable.store.sid

        self.store_codependent_data(store)


HttkObject.db = HttkPluginWrapper(HttkObjDbPlugin)

