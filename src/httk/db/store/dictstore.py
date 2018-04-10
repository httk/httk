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

from httk.db.storable import Storable


class DictStore(object):

    """
    Simplified fake database store in a dict, for testing primarily; though it can be used as a fast database-like engine
    that enables reterival of data
    """
    basics = [int, float, str, bool]
    
    def __init__(self):
        self.store = {}
        self.sids = {}
        self.types = {}
        self.typedicts = {}
        self.columns = {}
        self.column_types = {}        

    class Keeper(object):

        def __init__(self, store, table, sid):
            self.store = store
            self.table = table
            self.sid = sid
    
        def __getitem__(self, name):
            return self.store.get(self.table, self.sid, name)
    
        def __setitem__(self, name, val):
            return self.store.put(self.table, self.sid, name, val)
    
        def puts(self, **args):
            self.store.puts(self.table, self.sid, **args)

    def new(self, table, types, keyvals):
        if table not in self.store:
            self.create_table(table, types)
        if types != self.types[table]:
            raise Exception("DictStore.new: type mismatch when creating a new row in table")

        sid = self.insert(table, keyvals)       
        return DictStore.Keeper(self, table, sid)

    def retrieve(self, table, types, sid):
        if table not in self.store:
            raise Exception("DictStore.retrieve: retrieve of non-existing table")
        return DictStore.Keeper(self, table, sid)

    def create_table(self, table, types):
        self.store[table] = {}
        self.sids[table] = 0
        self.types[table] = types
        self.typedicts[table] = dict(types)

        column_types = []
        columns = []

        for column in types:
            name = column[0]
            t = column[1]

            # Regular column, no strangeness            
            if t in self.basics:
                columns.append(name)
                column_types.append(t)

            # List type means we need to establish a second table and store key values
            elif isinstance(t, list):
                subtablename = table+"_"+name
                if issubclass(t[0], Storable):
                    subtypes = [(table+"_sid", int), (t[0].types[0]+"_sid", int)]
                else:
                    subtypes = [(table+"_sid", int), (name, t[0])]

                self.create_table(subtablename, subtypes)

            # Tuple means numpy array                
            elif isinstance(t, tuple):

                # Numpy array with fixed number of entries, just flatten and store as _1, _2, ... columns
                if t[0] >= 1:
                    size = t[0]*t[1]
                    for i in range(size):
                        columns.append(name+"_"+str(i))
                        column_types.append(float)

                # Variable length numpy array, needs subtable
                if t[0] == 0:
                    subtablename = table+"_"+name
                    subtablecolumnname = name 
                    
                    subdimension = (1, t[1])
                    self.create_table(subtablename, [(table, int), (subtablecolumnname, subdimension)])
            
            elif issubclass(t, Storable):
                columnname = name+"_"+t.types[0]+"_sid"                
                columns.append(columnname)
                column_types.append(int)
            else:
                raise Exception("Dictstore.create_table: unexpected class; can only handle basic types and subclasses of Storable. Offending class:"+str(t))

        self.columns[table] = columns
        self.column_types[table] = column_types

    def insert(self, table, keyvals):
        sid = self.sids[table]
        types = self.types[table]
        
        self.store[table][sid] = {}

        for column in types:
            name = column[0]
            t = column[1]

            if name not in keyvals:
                val = None
            else:
                val = keyvals[name]

            # Regular column, no strangeness            
            if t in self.basics:
                self.store[table][sid][name] = val

            # List type means we need to establish a second table and store key values
            elif isinstance(t, list):
                subtablename = table+"_"+name
                if issubclass(t[0], Storable):
                    for entry in val:                        
                        data = {table+"_sid": sid, t[0].types[0]+"_sid": entry.store.sid}                   
                        self.insert(subtablename, data)
                else:
                    for entry in val:                        
                        data = {table+"_sid": sid, name: entry}
                        self.insert(subtablename, data)

            # Tuple means numpy array                
            elif isinstance(t, tuple):
                # Numpy array with fixed number of entries, just flatten and store as _1, _2, ... columns
                if t[0] >= 1:
                    flat = val.flatten()
                    size = t[0]*t[1]
                    for i in range(size):
                        columname = name+"_"+str(i)
                        self.store[table][sid][columname] = flat[i]

                # Variable length numpy array, needs subtable
                if t[0] == 0:
                    subtablename = table+"_"+name
                    for entry in val:  # loops over rows in 2d array                      
                        data = {table+"_sid": sid, name: entry}
                        self.insert(subtablename, data)
                                   
            elif issubclass(t, Storable):
                print "VAL", val
                if val.store != self:
                    raise Exception("DictStore.insert: Can only use Storable variables pertaining to the same store within another Storable.")
                columnname = name+"_"+t.types[0]+"_sid"                
                self.store[table][sid][columnname] = val.store.sid
            else:
                raise Exception("Dictstore.insert: unexpected class; can only handle basic types and subclasses of Storable. Offending class:"+str(t))

        self.sids[table] += 1
        return sid

    def get(self, table, sid, name):
        types = self.types[table]        

        print "GET on", table, name
        t = self.typedicts[table][name]

        # Regular column, no strangeness            
        if t in self.basics:
            return self.store[table][sid][name]

        # List type means we need to establish a second table and store key values
        elif isinstance(t, list):
            subtablename = table+"_"+name
            entries = []
            if issubclass(t[0], Storable):
                for key in self.store[subtablename]:
                    entry = self.store[subtablename][key]
                    if entry[table+"_sid"] != sid:
                        continue
                    new = t[0].instantiate_from_store(self, entry[t[0].types[0]+"_sid"])
                    #print "I AM HERE:",new,self,entry[t[0].types[0]+"_sid"]
                    entries.append(new)
            else:
                for key in self.store[subtablename]:
                    entry = self.store[subtablename][key]
                    if entry[table+"_sid"] != sid:
                        continue
                    entries.append(entry[name])
            return entries
        
        # Tuple means numpy array                
        elif isinstance(t, tuple):

            # Numpy array with fixed number of entries, just flatten and store as _1, _2, ... columns
            if t[0] >= 1:
                size = t[0]*t[1]
                flat = []
                for i in range(size):
                    columname = name+"_"+str(i)
                    flat.append(self.store[table][sid][columname])
                arr = array(flat)
                arr.shape = (t[0], t[1])
                return arr

            # Variable length numpy array, needs subtable
            if t[0] == 0:
                subtablename = table+"_"+name
                for key in self.store[subtablename]:
                    entry = self.store[subtablename][key]
                    if entry[table+"_sid"] != sid:
                        continue                    
                    entries.append(self.get(subtablename), entry.store.sid, name)
                               
        elif issubclass(t, Storable):
            columnname = name+"_"+t.types[0]+"_sid"                
            new = t.instantiate_from_store(self, self.store[table][sid][columnname])
            return new
        
        else:
            raise Exception("Dictstore.get: unexpected class; can only handle basic types and subclasses of Storable. Offending class:"+str(t))

    def put(self, table, sid, name, val):
        t = self.typedicts[table][name]

        # Regular column, no strangeness            
        if t in self.basics:
            self.store[table][sid][name] = val

        # List type means we need to establish a second table and store key values
        elif isinstance(t, list):
            subtablename = table+"_"+name
            if issubclass(t[0], Storable):
                for entry in val:                        
                    data = {table+"_sid": sid, t[0].types[0]+"_sid": entry.store.sid}                   
                    self.insert(subtablename, data)
            else:
                for entry in val:                        
                    data = {table+"_sid": sid, name: entry}
                    self.insert(subtablename, data)

        # Tuple means numpy array                
        elif isinstance(t, tuple):
            # Numpy array with fixed number of entries, just flatten and store as _1, _2, ... columns
            if t[0] >= 1:
                flat = val.flatten()
                size = t[0]*t[1]
                for i in range(size):
                    columname = name+"_"+str(i)
                    self.store[table][sid][columname] = flat[i]

            # Variable length numpy array, needs subtable
            if t[0] == 0:
                subtablename = table+"_"+name
                for entry in val:  # loops over rows in 2d array                      
                    data = {table+"_sid": sid, name: entry}
                    self.insert(subtablename, data)
                               
        elif issubclass(t, Storable):
            if val.store != self:
                raise Exception("DictStore.put: Can only use Storable variables pertaining to the same store within another Storable.")
            columnname = name+"_"+t.types[0]+"_sid"                
            self.store[table][sid][columnname] = val.store.sid
        else:
            raise Exception("Dictstore.put: unexpected class; can only handle basic types and subclasses of Storable")

    def puts(self, table, sid, **args):
        for name, val in args.iteritems():
            self.set(table, sid, name, val)
