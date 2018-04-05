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

#from numpy import *
import sys
from httk.core.httkobject import HttkObject
from httk.db.filteredcollection import *
from httk.core.basic import flatten
from httk.core import FracVector, FracScalar
from httk.db.storable import Storable

#def table_exist(db,table):
#    db.execute("")


class SqlStore(object):

    """
    Keep objects in an sql database
    """
    basics = [int, float, str, bool, FracScalar]
    
    def __init__(self, db):
        self.db = db
        self._delay_commit = False

    class Keeper(object):

        def __init__(self, store, table, types, sid):
            self.store = store
            self.table = table
            self.sid = sid
            self.types = types
    
        def __getitem__(self, name):
            return self.store.get(self.table, self.sid, self.types, name)
    
        def __setitem__(self, name, val):
            return self.store.insert(self.table, self.types, {name: val}, updatesid=self.sid)
    
        def puts(self, **args):
            self.store.puts(self.table, self.sid, **args)

    def new(self, table, types, keyvals=None, updatesid=None):
        if not self.db.table_exists(table):
            self.create_table(table, types)

        if keyvals is not None:
            sid = self.insert(table, types, keyvals, updatesid=updatesid)       
            return SqlStore.Keeper(self, table, types, sid)

    def retrieve(self, table, types, sid):
        #if not self.db.table_exists(table):
        #    raise Exception("DictStore.retrieve: retrieve of non-existing table")
        return SqlStore.Keeper(self, table, types, sid)

    def create_table(self, table, types, cursor=None):        
        #self.store[table]={}
        #self.sids[table]=0
        #self.types[table] = types
        if cursor is None:
            cursor = self.db.cursor()
            mycursor = True
        else:
            mycursor = False
        
        #self.typedicts[table] = dict(types)

        column_types = []
        columns = []
        index = []
        if 'index' in types:
            inindex = list(types['index'])
        else:
            inindex = []

        #print "### What is types:",types,t
        for column in tuple(types['keys']) + tuple(types['derived']):
            #print "X",table,column,inindex
            name = column[0]
            t = column[1]
            #print "DEBUG",name,t

            # Regular column, no strangeness            
            if t in self.basics:
                columns.append(name)
                column_types.append(t)
                #if name in inindex:
                #    index.append(name)

            # List type means we need to establish a second table and store key values
            elif isinstance(t, list):
                if not isinstance(t[0], tuple):
                    t = [(name, t[0])]
                subtablename = table+"_"+name
                subtypes = [(table+"_sid", int)]
                subtypes += [(name+"_index", int)]
                subindex = [table+"_sid"]
                for it in t:
                    if issubclass(it[1], HttkObject):
                        subtypes.append((it[0]+"_"+it[1].types()['name']+"_sid", int,))
                        subindex.append(it[0]+"_"+it[1].types()['name']+"_sid")
                    else:
                        subtypes.append((it[0], it[1],))
                derivedtypes = ()

                self.create_table(subtablename, {'keys': subtypes, 'index': subindex, 'derived': derivedtypes}, cursor)
                inindex = filter(lambda x: x != name, inindex)

            # Tuple means array                
            elif isinstance(t, tuple):
                tupletype = t[0]
                #print "CREATE TUPLETYPE",tupletype,types

                if t[1] >= 1:
                    size = t[1]*t[2]
                    newcolumns = []
                    for i in range(size):
                        newcolumns.append(name+"_"+str(i))
                        columns.append(name+"_"+str(i))
                        if issubclass(tupletype, FracVector):
                            column_types.append(int)
                        else:   
                            column_types.append(tupletype)
                    newinindex = []
                    for indexitem in inindex:
                        if indexitem == name:
                            newinindex += newcolumns
                        else:
                            newinindex += [indexitem]
                    inindex = newinindex

                # Variable length numpy array, needs subtable
                if t[1] == 0:
                    subtablename = table+"_"+name
                    subtablecolumnname = name 
                    subdimension = (tupletype, 1, t[2])
                    self.create_table(subtablename, {'keys': [(table+"_sid", int), (name+"_index", int), (subtablecolumnname, subdimension)], 'index': [table+'_sid'], 'derived': ()}, cursor)
                    inindex = filter(lambda x: x != name, inindex)
                                
            elif issubclass(t, HttkObject):
                columnname = name+"_"+t.types()['name']+"_sid"                
                columns.append(columnname)
                column_types.append(int)
                #print "ININDEX",inindex
                for i in range(len(inindex)):
                    if isinstance(inindex[i], tuple):
                        indexentry = list(inindex[i])
                        for j in range(len(indexentry)):
                            if indexentry[j] == name:
                                indexentry[j] = columnname
                        inindex[i] = tuple(indexentry)
                    else:
                        if inindex[i] == name:
                            inindex[i] = columnname
                #print "2 ININDEX",inindex
                #if name in inindex:
                #    index.append(columnname)
            else:
                raise Exception("Dictstore.create_table: unexpected class; can only handle basic types and subclasses of Storable. Offending class:"+str(t))

        #print "TABLE",table
        #print "TYPES",tuple(types['keys']) + tuple(types['derived'])
        #print "INDEX",inindex
        self.db.create_table(table, table+"_id", columns, column_types, cursor, index=inindex)
        if mycursor:
            if not self._delay_commit:
                self.db.commit()
            cursor.close()

        #self.columns[table] = columns
        #self.column_types[table] = column_types

    def insert(self, table, types, keyvals, cursor=None, updatesid=None):
        #sid=self.sids[table]
        #types=self.types[table]        
        #self.store[table][sid]={}
        if cursor is None:
            cursor = self.db.cursor()
            mycursor = True
        else:
            mycursor = False

        columns = []
        columndata = []
        subinserts = []
        for column in tuple(types['keys']) + tuple(types['derived']):
            name = column[0]
            t = column[1]

            if name not in keyvals:
                val = None
            else:
                val = keyvals[name]
            if val is None:
                continue

            # Regular column, no strangeness            
            if t in self.basics:
                #if issubclass(t,FracVector):
                #    val = (val*1000000000).to_int()
                if issubclass(t, FracScalar):
                    val = FracScalar.use(val)
                    val = int(val.limit_denominator(50000000)*1000000000)
                #if isinstance(t,FracVector):
                #    print "DOES THIS HAPPEN?",t,val
                #    val = int(val.limit_denominator(50000000))
                else:
                    try:
                        val = t(val)
                    except UnicodeEncodeError:
                        val = unicode(val)
                    except TypeError:
                        print "HUH", val, t
                        raise
                columns.append(name)
                columndata.append(val)

            # List type means we need to establish a second table and store key values
            elif isinstance(t, list):                
                if not isinstance(t[0], tuple):
                    t = [(name, t[0])]
                    val = [(x,) for x in val]
                subtablename = table+"_"+name
                for idx, entry in enumerate(val):
                    subtypes = [(table+"_sid", int), (name+"_index", int)]
                    data = {name+"_index": idx}
                    for i in range(len(t)):
                        if issubclass(t[i][1], HttkObject):
                            subtypename = t[i][0]+"_"+t[i][1].types()['name']+"_sid"
                            subtypes.append((subtypename, int,))

                            if entry[i].db.sid is None:
                                entryval = t[i][1].use(entry[i])                    
                                entryval.db.store(self)                            
                            
                            data[subtypename] = entry[i].db.sid
                        else:
                            subtypename = t[i][0]
                            subtypes.append((subtypename, t[i][1],))
                            if isinstance(entry, tuple):
                                #print "TRYING",entry,i,subtypename
                                data[subtypename] = entry[i]
                            elif isinstance(entry, dict):
                                data[subtypename] = entry[t[i][0]]
                            else:
                                raise Exception("Data for multifield of wrong type, got:"+str(entry))
                    
                    subinserts.append((subtablename, subtypes, data, ()))
                    #print "SUBINSETS",subinserts
                            
            # Tuple means numpy array                
            elif isinstance(t, tuple):
                # Numpy array with fixed number of entries, just flatten and store as _1, _2, ... columns
                tupletype = t[0]
                #print "INSERT TUPLETYPE",tupletype,types,t

                if t[1] >= 1:
                    #flat=val.flatten()
                    flat = tuple(flatten(val))
                    size = t[1]*t[2]
                    for i in range(size):
                        columname = name+"_"+str(i)
                        columns.append(columname)
                        if tupletype == FracVector:
                            setval = (FracVector.use(flat[i]).limit_denominator(5000000)*1000000000).to_ints()
                            columndata.append(setval)
                        elif tupletype == FracScalar:
                            #print "FLATI",flat[i]
                            #columndata.append(map(lambda x:int(x*1000000000),flat[i]))
                            if flat[i] is not None:
                                setval = int(FracScalar.use(flat[i]).limit_denominator(5000000)*1000000000)
                                columndata.append(setval)
                            else:
                                columndata.append(None)
                        else:
                            columndata.append(flat[i])

                # Variable length numpy array, needs subtable
                if t[1] == 0:
                    subtablename = table+"_"+name
                    subtablecolumnname = name                     
                    subdimension = (tupletype, 1, t[2])

                    for idx, entry in enumerate(val):  # loops over rows in 2d array                      
                        #data = {table+"_sid":sid,name:entry}
                        #self.insert(subtablename,data)
                        data = {name: entry, name+"_index": idx}
                        subtypes = [(subtablecolumnname, subdimension), (table+"_sid", int), (name+"_index", int)]
                        subinserts.append((subtablename, subtypes, data, ()))
                                   
            elif issubclass(t, HttkObject):
                if val.db.sid is None:
                    # This fixes an issue where sometimes a different class (e.g. a subclass) is sent in to be stored in a field.
                    val = t.use(val)                    
                    val.db.store(self)
                columnname = name+"_"+t.types()['name']+"_sid"                
                columns.append(columnname)
                columndata.append(val.db.sid)
            else:
                raise Exception("Dictstore.insert: unexpected class; can only handle basic types and subclasses of Storable. Offending class:"+str(t))

        # TODO: this logic is not finished, more elaborate updates need handling
        if updatesid >= 0 or updatesid is None:
            if updatesid is not None:
                sid = self.db.update_row(table, table+"_id", updatesid, columns, columndata, cursor)
            else:
                sid = self.db.insert_row(table, columns, columndata, cursor)
                for subinsert in subinserts:
                    subinsert[2][table+"_sid"] = sid
                    self.insert(subinsert[0], {'keys': subinsert[1], 'derived': subinsert[3]}, subinsert[2], cursor)
        else:
            sid = -updatesid
        
        if mycursor:
            if not self._delay_commit:
                self.db.commit()
            cursor.close()

        return sid

    def get(self, table, sid, types, name):
        #types=self.types[table]        

        if name in types['keydict']:
            t = types['keydict'][name]
        else:
            t = types['derived_keydict'][name]
            
        origt = t

        # Regular column, no strangeness            
        if t in self.basics: 
            if t == FracScalar:
                val = self.db.get_val(table, table+"_id", sid, name)
                if val is None:
                    return None
                return FracVector.create(FracScalar(int(val), 1000000000).limit_denominator(5000000))
            return self.db.get_val(table, table+"_id", sid, name)

        # List type means we need to establish a second table and store key values
        elif isinstance(t, list):
            if not isinstance(t[0], tuple):
                t = [(name, t[0])]            
            subtablename = table+"_"+name
            subtypes = [(table+"_sid", int)]
            columns = []

            must_convert_sids = []
            for i in range(len(t)):
                if issubclass(t[i][1], HttkObject):
                    subtypename = t[i][0]+"_"+t[i][1].types()['name']+"_sid"
                    subtypes.append((subtypename+"_sid", int,))
                    columns.append(subtypename)
                    must_convert_sids.append(i)
                else:
                    subtypename = t[i][0]
                    subtypes.append((subtypename, t[i][1],))
                    columns.append(subtypename)

            result = self.db.get_row(subtablename, table+"_sid", sid, columns)

            # If the type points to another Storable obect, we need to turn all the sid:s into real objects.
            newresult = []
            for line in result:
                line = list(line)
                for i in must_convert_sids:
                    line[i] = instantiate_from_store(t[i][1], self, line[i])
                newresult.append(line)
            result = newresult

            #print "TYPE0",types['keydict'][name]
            #print "TYPE",origt[0]
            #print "RESULT",result
            if not type(origt[0]) in (list, tuple):
                return [x[0] for x in result]
            else:
                return result
                                
        # Tuple means numpy array                
        elif isinstance(t, tuple):
            tupletype = t[0]

            # Numpy array with fixed number of entries, just flatten and store as _1, _2, ... columns
            if t[1] >= 1:
                size = t[1]*t[2]

#                 flat = tuple(flatten(val))
#                 for i in range(size):
#                     columname=name+"_"+str(i)
#                     columns.append(columname)
#                     if tupletype == FracVector:
#                         columndata.append((flat[i]*1000000000).to_ints())
#                     else:
#                         columndata.append(flat[i])
# 
#                 # Variable length numpy array, needs subtable
#                 if t[1] == 0:
#                     subtablename = table+"_"+name
#                     subtablecolumnname = name                     
#                     subdimension = (tupletype,1,t[2])
# 
#                     for entry in val:  # loops over rows in 2d array                      
#                         #data = {table+"_sid":sid,name:entry}
#                         #self.insert(subtablename,data)
#                         data = {name:entry}
#                         subtypes = [(subtablecolumnname,subdimension),(table+"_sid",int)]
#                         subinserts.append((subtablename, subtypes, data,))

                columnames = []
                for i in range(size):
                    columnames.append(name+"_"+str(i))
                flat = self.db.get_row(table, table+"_id", sid, columnames)[0]

                if tupletype == FracVector or tupletype == FracScalar:
                    for x in flat:
                        if x is None:
                            return flat
                    #def flatterer(l):
                    #    if l == None:
                    #        return None
                    #    else:
                    #        return Fraction(int(l),1000000000) 
                    #flat=map(flatterer,flat)
                    flat = map(lambda l: FracScalar(int(l), 1000000000).limit_denominator(5000000), flat)
                    reshaped = zip(*[iter(flat)]*t[1])
                    return FracVector.create(reshaped)
                else:
                    map(tupletype, flat)
                    return zip(*[iter(flat)]*t[1])
                # TODO: ADD support for numpy

            # Variable length numpy array, needs subtable
            if t[1] == 0:
                subtablename = table+"_"+name
                columnames = []
                for i in range(t[2]):
                    columnames.append(name+"_"+str(i))
                if tupletype == FracVector or tupletype == FracScalar:
                    vals = self.db.get_row(subtablename, table+"_sid", sid, columnames)
                    vals = map(lambda l: map(lambda x: FracScalar(int(x), 1000000000), l), vals)
                    return FracVector.create(vals).limit_denominator(5000000)
                else:   
                    return self.db.get_row(subtablename, table+"_sid", sid, columnames)
                               
#       elif issubclass(t,Storable):
        elif hasattr(t, 'types'):
            columnname = name+"_"+t.types()['name']+"_sid"
            subsid = self.db.get_val(table, table+"_id", sid, columnname)
            return instantiate_from_store(t, self, subsid)                
        
        else:
            raise Exception("Dictstore.get: unexpected class; can only handle basic types and subclasses of Storable. Offending class:"+str(t))

    def put(self, table, sid, types, name, val):
        raise Exception("Is this being called?")
        t = types['keydict'][name]
        origt = t

        # Regular column, no strangeness            
        if t in self.basics:
            self.store[table][sid][name] = val

        # List type means we need to establish a second table and store key values
        elif isinstance(t, list):
            subtablename = table+"_"+name
            if issubclass(t[0], Storable):
                for entry in val:                        
                    data = {table+"_sid": sid, t[0].types['name']+"_sid": entry.store.sid}                   
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
            columnname = name+"_"+t.types['name']+"_sid"                
            self.store[table][sid][columnname] = val.store.sid
        else:
            raise Exception("Dictstore.put: unexpected class; can only handle basic types and subclasses of Storable")

    def puts(self, table, sid, **args):
        for name, val in args.iteritems():
            self.set(table, sid, name, val)

    def searcher(self):
        return FCSqlite(self)
        
    def delay_commit(self):
        self._delay_commit = True
        
    def commit(self):
        self.db.commit()
        self._delay_commit = False
        
    def save(self, obj):
        obj.db.store(self)  



