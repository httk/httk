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

"""
This provides a thin abstraction layer for SQL queries, implemented on top of sqlite,3 to make it easier to exchange between SQL databases.
"""

import os, sys
import sqlite3 as sqlite
import atexit

sqliteconnections = set()
# TODO: Make this flag configurable in httk.cfg
database_debug = False
#database_debug = True

def db_open(filename):
    global sqliteconnections
    connection = sqlite.connect(filename)
    sqliteconnections.add(connection)
    return connection

def db_close(connection):
    global sqliteconnections
    sqliteconnections.remove(connection)
    connection.close()

def db_sqlite_close_all():
    global sqliteconnections
    for connection in sqliteconnections:
        connection.close()

atexit.register(db_sqlite_close_all)

class Sqlite(object):
    
    def __init__(self,filename):
        self.connection = db_open(filename)
        #self._block_commit = False

    def close(self):
        db_close(self.connection)

    def rollback(self):
        self.connection.rollback()

    def commit(self):
        #if self._block_commit:
       #     raise Exception("Who is commiting?!")
        self.connection.commit()

    class SqliteCursor(object):
        def __init__(self,db):
            self.cursor = db.connection.cursor()

        def execute(self,sql,values=[]):
            global database_debug
            if os.environ.has_key('DATABASE_DEBUG') or database_debug:
                print >> sys.stderr, "DEBUG: EXECUTING SQL:"+sql+" :: "+str(values)
            try:
                self.cursor.execute(sql,values)
            except Exception as e:
                info = sys.exc_info()
                raise Exception("backend.Sqlite: Error while executing sql: "+sql+" with values: "+str(values)+", the error returned was: "+str(info[1])), None, info[2]

        def fetchone(self):
            return self.cursor.fetchone()

        def fetchall(self):
            return self.cursor.fetchall()

        def close(self):
            return self.cursor.close()

        def __iter__(self):
            for row in self.cursor:
                yield row

    def cursor(self):
        return self.SqliteCursor(self)

    def table_exists(self,name,cursor = None):
        result = self.query("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(name,),cursor=cursor)    
        if result == []:
            return False
        return True

    def create_table(self,name,primkey,columnnames,columntypes,cursor = None, index=None):
        sql = primkey+" INTEGER PRIMARY KEY"
        for i in range(len(columnnames)):
            if columntypes[i] == int:
                typestr = "INTEGER"
            elif columntypes[i] == float:
                typestr = "REAL"
            elif columntypes[i] == str:
                typestr = "TEXT"
            else:
                raise Exception("backend.Sqlite.create_table: column of unrecognized type: "+str(columntypes[i])+" ("+str(columntypes[i].__class__)+")")                      
            
            sql += ", "+columnnames[i]+" "+typestr
            
        self.modify_structure("CREATE TABLE "+name+" ("+sql+")",(),cursor=cursor)    
        if index != None:
            for ind in index:
                self.modify_structure("CREATE INDEX "+name+"_"+ind+"_index"+" ON "+name+"("+ind+")",(),cursor=cursor)    

    def insert_row(self,name,columnnames,columnvalues,cursor = None):
        if len(columnvalues)>0:
            return self.insert("INSERT INTO "+name+" ("+(",".join(columnnames))+") VALUES ("+(",".join(["?"]*len(columnvalues)))+" )",columnvalues,cursor=cursor)  
        else:
            return self.insert("INSERT INTO "+name+ " DEFAULT VALUES",(),cursor=cursor)  

    def update_row(self,name,primkeyname, primkey, columnnames,columnvalues,cursor = None):
        if len(columnvalues)==0:
            return
        return self.update("UPDATE "+name+" SET "+(" = ?,".join(columnnames))+" = ? WHERE "+primkeyname+" = ?",columnvalues + [primkey],cursor=cursor)  

    def get_val(self,table, primkeyname, primkey, columnname, cursor = None):
        result = self.query("SELECT "+columnname+" FROM "+table+" WHERE "+primkeyname+" = ?",[primkey],cursor=cursor)
        val = result[0][0]
        return val

    def get_row(self,table, primkeyname, primkey, columnnames, cursor = None):
        columnstr = ",".join(columnnames)
        return self.query("SELECT "+columnstr+" FROM "+table+" WHERE "+primkeyname+" = ?",[primkey],cursor=cursor)  

    def get_rows(self,table, primkeyname, primkeys, columnnames, cursor = None):
        columnstr = ",".join(columnnames)
        return self.query("SELECT "+columnstr+" FROM "+table+" WHERE "+primkeyname+" = "+("or".join(["?"]*len(primkeys))),primkeys,cursor=cursor)
        
    def query(self, sql, values, cursor = None):
        if cursor == None:
            cursor = self.cursor()
            cursor.execute(sql,values)
            result = cursor.fetchall()
            cursor.close()
            return result
        else:
            cursor.execute(sql,values)
            return cursor.fetchall()
                
    def insert(self, sql, values, cursor = None):
        if cursor == None:
            cursor = self.cursor()
            cursor.execute(sql,values)
            cursor.commit()
            lid = cursor.cursor.lastrowid
            cursor.close()
        else:
            cursor.execute(sql,values)
            lid = cursor.cursor.lastrowid
        return lid

    def update(self, sql, values, cursor = None):
        if cursor == None:
            cursor = self.cursor()
            cursor.execute(sql,values)
            cursor.commit()
            lid = cursor.cursor.lastrowid
            cursor.close()
        else:
            cursor.execute(sql,values)
            lid = cursor.cursor.lastrowid
        return lid
    
    def alter(self, sql, values, cursor = None):
        if cursor == None:
            cursor = self.cursor()
            cursor.execute(sql,values)
            cursor.commit()
            cursor.close()
        else:
            cursor.execute(sql,values)

    def modify_structure(self, sql, values, cursor = None):
        if cursor == None:
            cursor = self.cursor()
            cursor.execute(sql,values)
            cursor.commit()
            cursor.close()
        else:
            cursor.execute(sql,values)
            