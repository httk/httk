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

#from store.trivialstore import TrivialStore
from filteredcollection import *
import sys


def storable_types(name, *keyvals, **flags):
    index = flags.pop('index', [])    
    return {'name': name, 'keys': keyvals, 'keydict': dict(keyvals), 'index': index}


def storable_props(*props):
    return props


class TrivialStore(object):

    """
    Very simple storage class that just stores everything into an individual dictionary, just like regular python objects work
    """

    def new(self, table, types, keyvals):
        d = dict(keyvals)
        d['sid'] = 0
        return d

    def retrieve(self, table, types, sid):
        raise Exception("TrivialStore.instance: You cannot load data from TrivialStore, sid must be = None.")


class Storable(object):

    """
    Superclass for handling various forms of data storage, retreival, etc. Class object representing data should inherit from Storable.
    
    All public variables must be initalized in a call to storable_init() inside __init__().
    Other member variables are OK, but must begin with '_', and all methods must handle these variables not being initialized.
    For private variables that needs to be preserved: let them start with '_' AND declare them in storable_init().
    """

    trivialstore = TrivialStore()  # The store class used if no store is specified, store things in the usual dictionary way
    _storable_tables = []

    def __init__(self, types=None, index=None):
        self.__dict__['types'] = types
        self.__dict__['index'] = index

    def storable_init(self, store, updatesid=None, **keyvals):
        """
        All Storable objects need to call this method in __init__(). Name should be a 'somewhat qualified' class name.
        """
        if store is None:
            store = Storable.trivialstore

        if keyvals:
            self.__dict__['store'] = store.new(self.types['name'], self.types, keyvals, updatesid=updatesid)
        else:
            self.__dict__['store'] = store.new(self.types['name'], self.types, None, updatesid=updatesid)
        self.__dict__['store_keys'] = keyvals.keys()

#     @classmethod
#     def instantiate_from_store(cls,store,sid):
#         """
#         Instantiate the storable object from the data in the store
#         """
#         name = cls.types['name']
#         obj = cls.__new__(cls) # Creates a new object, avoids calling __init__
#         obj.__dict__['store'] = store.retrieve(name,cls.types, sid)
#         return obj

    def __getattr__(self, name):
        #if name in self.__class__.types[2]:
        #    return getattr(self.__class__,name)
        if name[0] == '_':
            try:
                return self.__dict__[name]
            except KeyError:
                info = sys.exc_info()
                raise AttributeError("KeyError when accessing local dict: "+str(info[1])), None, info[2]
        return self.store[name]

    def __setattr__(self, name, val):
        if name in self.store_keys:
            self.store[name] = val
        elif name[0] == '_':
            self.__dict__[name] = val
        else:
            raise Exception("The class "+self.__class__+" inherits from Storable. Hence, all public variables must be " +
                            "declared in a call to self.storable_init, and non-public variables must start with an underscore (_). " +
                            "Offending variable name: "+name)

    @classmethod
    def variable(cls, searcher, name, types, outid=None, parent=None):        
        # The empty new triggers an e.g., create_table. I'm not sure it really should be here, but it is tricky to get the order correct when 
        # bootstapping new tables, and by placing this here, one can just simply make a query into the non-existent table, discover 
        # that some data is missing,  and insert it into the newly created table.
        #print searcher.variable()
        raise Exception("Internal error.")

        searcher.store.new(types['name'], types)

        if outid is None:
            outid = name+"_"+str(len(cls._storable_tables))
        table = TableOrColumn(searcher, types['name'], parent=parent, outid=outid, indirection=1, classref=cls)
        return table
    
    @classmethod
    def find_all(cls, obj, store, member, value, types):        
        """
        Convinience method to do a very simple search of type: find all entries where member = value.
        """
        search = store.searcher()
        p = search.variable(obj.__class__)
        #print "XXXXXXXXXX",obj.__class__
        search.add(p.__getattr__(member) == value)
        search.output(p, 'object')
        results = list(search)
        if len(results) > 0:
            return results[0]
        else:
            return []

    @classmethod
    def find_one(cls, obj, store, member, value, types):        
        """
        Convinience^2 method to do a very simple search of type: find one entry where member = value.
        """
        allresults = cls.find_all(store, obj, member, value, types)
        if len(allresults) >= 1:
            return allresults[0][0]
        return None

    def _sql(self):
        return str(self.store.sid)

