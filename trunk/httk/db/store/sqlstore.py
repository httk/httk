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

#from numpy import *
import sys
from httk.db import Storable
from httk.db.filteredcollection import *
from httk.utils import flatten

#def table_exist(db,table):
#    db.execute("")

class SqlStore(object):
    """
    Keep objects in an sql database
    """
    basics = [int, float, str, bool]
    
    def __init__(self,db):
        self.db = db
        self._delay_commit = False

    class Keeper(object):
        def __init__(self, store, table, types, sid):
            self.store = store
            self.table = table
            self.sid = sid
            self.types = types
    
        def __getitem__(self,name):
            return self.store.get(self.table, self.sid, self.types, name)
    
        def __setitem__(self,name,val):
            return self.store.insert(self.table, self.types, {name:val}, updatesid=self.sid)
    
        def puts(self, **args):
            self.store.puts(self.table,self.sid,**args)

    def new(self,table,types,keyvals=None):
        if not self.db.table_exists(table):
            self.create_table(table,types)

        if keyvals != None:
            sid = self.insert(table,types,keyvals)       
            return SqlStore.Keeper(self,table,types, sid)

    def retrieve(self,table,types, sid):
        #if not self.db.table_exists(table):
        #    raise Exception("DictStore.retrieve: retrieve of non-existing table")
        return SqlStore.Keeper(self,table,types, sid)

    def create_table(self,table,types,cursor=None):        
        #self.store[table]={}
        #self.sids[table]=0
        #self.types[table] = types
        if cursor == None:
            cursor = self.db.cursor()
            mycursor = True
        else:
            mycursor = False
        
        #self.typedicts[table] = dict(types)

        column_types = []
        columns = []
        index = []
        if 'index' in types:
            inindex = types['index']
        else:
            inindex = []

        #print "What is types:",types
        for column in types['keys']:
            name = column[0]
            t = column[1]

            # Regular column, no strangeness            
            if t in self.basics:
                columns.append(name)
                column_types.append(t)
                if name in inindex:
                    index.append(name)

            # List type means we need to establish a second table and store key values
            elif type(t) == list:
                if type(t[0]) != tuple:
                    t = [(name,t[0])]
                subtablename = table+"_"+name
                subtypes = [(table+"_sid",int)]
                subindex = [table+"_sid"]
                for it in t:
                    if issubclass(it[1],Storable):
                        subtypes.append((it[0]+"_"+it[1].types['name']+"_sid",int,))
                        subindex.append(it[0]+"_"+it[1].types['name']+"_sid")
                    else:
                        subtypes.append((it[0],it[1],))

                self.create_table(subtablename,{'keys':subtypes,'index':subindex},cursor)

            # Tuple means numpy array                
            elif type(t) == tuple:

                # Numpy array with fixed number of entries, just flatten and store as _1, _2, ... columns
                if t[0] >= 1:
                    size=t[0]*t[1]
                    for i in range(size):
                        columns.append(name+"_"+str(i))
                        column_types.append(float)

                # Variable length numpy array, needs subtable
                if t[0] == 0:
                    subtablename = table+"_"+name
                    subtablecolumnname = name 
                    
                    subdimension = (1,t[1])
                    self.create_table(subtablename,{'keys':[(table+"_sid",int),(subtablecolumnname,subdimension)],'index':[table+'_sid']},cursor)
            
            elif issubclass(t,Storable):
                columnname = name+"_"+t.types['name']+"_sid"                
                columns.append(columnname)
                column_types.append(int)
                if name in inindex:
                    index.append(columnname)
            else:
                raise Exception("Dictstore.create_table: unexpected class; can only handle basic types and subclasses of Storable. Offending class:"+str(t))

        self.db.create_table(table,table+"_id",columns,column_types,cursor,index=index)
        if mycursor:
            if not self._delay_commit:
                self.db.commit()
            cursor.close()

        #self.columns[table] = columns
        #self.column_types[table] = column_types


    def insert(self,table,types,keyvals,cursor=None,updatesid=None):
        #sid=self.sids[table]
        #types=self.types[table]        
        #self.store[table][sid]={}
        if cursor == None:
            cursor = self.db.cursor()
            mycursor = True
        else:
            mycursor = False

        columns=[]
        columndata = []
        subinserts = []
        for column in types['keys']:
            name = column[0]
            t = column[1]

            if not keyvals.has_key(name):
                val = None
            else:
                val = keyvals[name]
            if val == None:
                continue

            # Regular column, no strangeness            
            if t in self.basics:
                columns.append(name)
                columndata.append(val)

            # List type means we need to establish a second table and store key values
            elif type(t) == list:                
                if type(t[0]) != tuple:
                    t = [(name,t[0])]
                    val = [(x,) for x in val]
                subtablename = table+"_"+name
                for entry in val:
                    subtypes = [(table+"_sid",int)]
                    data = {}
                    for i in range(len(t)):
                        if issubclass(t[i][1],Storable):
                            if not hasattr(entry[i].store,'store'):
                                raise Exception("SqlStore.insert: type error, ",entry[i])
                            if entry[i].store.store != self:
                                raise Exception("SqlStore.insert: Can only use Storable variables pertaining to the same store within another Storable.")
                            subtypename = t[i][0]+"_"+t[i][1].types['name']+"_sid"
                            subtypes.append((subtypename,int,))
                            data[subtypename] = entry[i].store.sid
                        else:
                            subtypename = t[i][0]
                            subtypes.append((subtypename,t[i][1],))
                            if isinstance(entry,tuple):
                                #print "TRYING",entry,i,subtypename
                                data[subtypename] = entry[i]
                            elif isinstance(entry,dict):
                                data[subtypename] = entry[t[i][0]]
                            else:
                                raise Exception("Data for multifield of wrong type, got:"+str(entry))
                    
                    subinserts.append((subtablename,subtypes, data,))
                    #print "SUBINSETS",subinserts
                            
            # Tuple means numpy array                
            elif type(t) == tuple:
                # Numpy array with fixed number of entries, just flatten and store as _1, _2, ... columns
                if t[0] >= 1:
                    #flat=val.flatten()
                    flat = tuple(flatten(val))
                    size=t[0]*t[1]
                    for i in range(size):
                        columname=name+"_"+str(i)
                        columns.append(columname)
                        columndata.append(float(flat[i]))

                # Variable length numpy array, needs subtable
                if t[0] == 0:
                    subtablename = table+"_"+name
                    subtablecolumnname = name                     
                    subdimension = (1,t[1])

                    for entry in val:  # loops over rows in 2d array                      
                        #data = {table+"_sid":sid,name:entry}
                        #self.insert(subtablename,data)
                        data = {name:entry}
                        subtypes = [(subtablecolumnname,subdimension),(table+"_sid",int)]
                        subinserts.append((subtablename, subtypes, data,))
                                   
            elif issubclass(t,Storable):
                if val.store.store != self:
                    raise Exception("SqlStore.insert: Can only use Storable variables pertaining to the same store within another Storable.")
                columnname = name+"_"+t.types['name']+"_sid"                
                columns.append(columnname)
                columndata.append(val.store.sid)
            else:
                raise Exception("Dictstore.insert: unexpected class; can only handle basic types and subclasses of Storable. Offending class:"+str(t))

        # TODO: this logic is not finished, more elaborate updates need handling
        if updatesid != None:
            sid = self.db.update_row(table, table+"_id", updatesid, columns, columndata, cursor)
        else:
            sid = self.db.insert_row(table, columns, columndata, cursor)
            for subinsert in subinserts:
                subinsert[2][table+"_sid"]=sid
                self.insert(subinsert[0],{'keys':subinsert[1]},subinsert[2],cursor)
        
        if mycursor:
            if not self._delay_commit:
                self.db.commit()
            cursor.close()

        return sid

    def get(self,table,sid,types, name):
        #types=self.types[table]        
        t = types['keydict'][name]
        origt = t

        # Regular column, no strangeness            
        if t in self.basics: 
            return self.db.get_val(table,table+"_id",sid,name)

        # List type means we need to establish a second table and store key values
        elif type(t) == list:
            if type(t[0]) != tuple:
                t = [(name,t[0])]            
            subtablename = table+"_"+name
            subtypes = [(table+"_sid",int)]
            columns = []

            must_convert_sids = []
            for i in range(len(t)):
                if issubclass(t[i][1],Storable):
                    subtypename = t[i][0]+"_"+t[i][1].types['name']+"_sid"
                    subtypes.append((subtypename+"_sid",int,))
                    columns.append(subtypename)
                    must_convert_sids.append(i)
                else:
                    subtypename = t[i][0]
                    subtypes.append((subtypename,t[i][1],))
                    columns.append(subtypename)

            result = self.db.get_row(subtablename,table+"_sid",sid,columns)

            # If the type points to another Storable obect, we need to turn all the sid:s into real objects.
            newresult = []
            for line in result:
                line = list(line)
                for i in must_convert_sids:
                    line[i] = t[i][1].instantiate_from_store(self,line[i])
                newresult.append(line)
            result = newresult

            #print "TYPE0",types['keydict'][name]
            #print "TYPE",origt[0]
            #print "RESULT",result
            if not type(origt[0]) in (list,tuple):
                return [x[0] for x in result]
            else:
                return result
                                
        # Tuple means numpy array                
        elif type(t) == tuple:

            # Numpy array with fixed number of entries, just flatten and store as _1, _2, ... columns
            if t[0] >= 1:
                size=t[0]*t[1]
                columnames = []
                for i in range(size):
                    columnames.append(name+"_"+str(i))
                flat = self.db.get_row(table,table+"_id",sid,columnames)
                arr = array(flat)
                arr.shape = (t[0],t[1])
                return arr

            # Variable length numpy array, needs subtable
            if t[0] == 0:
                subtablename = table+"_"+name
                columnames = []
                for i in range(t[1]):
                    columnames.append(name+"_"+str(i))
                return self.db.get_row(subtablename,table+"_sid",sid,columnames)
                               
        elif issubclass(t,Storable):
            columnname = name+"_"+t.types['name']+"_sid"
            subsid = self.db.get_val(table,table+"_id",sid,columnname)
            return t.instantiate_from_store(self,subsid)                
        
        else:
            raise Exception("Dictstore.get: unexpected class; can only handle basic types and subclasses of Storable. Offending class:"+str(t))


    def put(self,table,sid,types,name,val):
        t = types['keydict'][name]
        origt = t

        # Regular column, no strangeness            
        if t in self.basics:
            self.store[table][sid][name]=val

        # List type means we need to establish a second table and store key values
        elif type(t) == list:
            subtablename = table+"_"+name
            if issubclass(t[0],Storable):
                for entry in val:                        
                    data = {table+"_sid":sid,t[0].types['name']+"_sid":entry.store.sid}                   
                    self.insert(subtablename,data)
            else:
                for entry in val:                        
                    data = {table+"_sid":sid,name:entry}
                    self.insert(subtablename,data)

        # Tuple means numpy array                
        elif type(t) == tuple:
            # Numpy array with fixed number of entries, just flatten and store as _1, _2, ... columns
            if t[0] >= 1:
                flat=val.flatten()
                size=t[0]*t[1]
                for i in range(size):
                    columname=name+"_"+str(i)
                    self.store[table][sid][columname]=flat[i]

            # Variable length numpy array, needs subtable
            if t[0] == 0:
                subtablename = table+"_"+name
                for entry in val:  # loops over rows in 2d array                      
                    data = {table+"_sid":sid,name:entry}
                    self.insert(subtablename,data)
                               
        elif issubclass(t,Storable):
            if val.store != self:
                raise Exception("DictStore.put: Can only use Storable variables pertaining to the same store within another Storable.")
            columnname = name+"_"+t.types['name']+"_sid"                
            self.store[table][sid][columnname]=val.store.sid
        else:
            raise Exception("Dictstore.put: unexpected class; can only handle basic types and subclasses of Storable")


    def puts(self,table,sid,**args):
        for name,val in args.iteritems():
            self.set(table,sid,name,val)

    def searcher(self):
        return FCSqlite(self)
        
    def delay_commit(self):
        self._delay_commit = True
        
    def commit(self):
        self.db.commit()
        self._delay_commit = False
        
        



