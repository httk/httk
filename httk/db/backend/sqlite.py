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

"""
This provides a thin abstraction layer for SQL queries, implemented on top of sqlite,3 to make it easier to exchange between SQL databases.
"""
import os, sys, time
import sqlite3 as sqlite
import atexit
from httk.core import FracScalar

sqliteconnections = set()
# TODO: Make this flag configurable in httk.cfg
database_debug = False
#database_debug = True
database_debug_slow = True
if 'DATABASE_DEBUG_SLOW' in os.environ:
    database_debug_slow = True
if 'DATABASE_DEBUG' in os.environ:
    database_debug = True


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
    
    def __init__(self, filename):
        self.connection = db_open(filename)
        #self._block_commit = False

    def close(self):
        db_close(self.connection)

    def rollback(self):
        self.connection.rollback()

    def commit(self):
        self.connection.commit()

    class SqliteCursor(object):

        def __init__(self, db):
            self.cursor = db.connection.cursor()
            self.db = db

        def execute(self, sql, values=[]):
            global database_debug
            if database_debug:
                print >> sys.stderr, "DEBUG: EXECUTING SQL:"+sql+" :: "+str(values)
            if database_debug_slow:
                time1 = time.time()
            try:
                self.cursor.execute(sql, values)
            except Exception:
                info = sys.exc_info()
                raise Exception("backend.Sqlite: Error while executing sql: "+sql+" with values: "+str(values)+", the error returned was: "+str(info[1])), None, info[2]
            if database_debug_slow:
                time2 = time.time()
                if (time2-time1) > 1 and not sql.startswith("CREATE"):
                    debug_cursor = self.db.connection.cursor()
                    print >> sys.stderr, "SLOW DATABASE DEBUG: EXECUTING SQL:"+sql+" :: "+str(values)
                    print >> sys.stderr, "sqlite execute finished in ", (time2-time1)*1000.0, "ms"
                    try:
                        debug_cursor.execute("EXPLAIN QUERY PLAN "+sql, values)
                        queryplan = "### QUERY PLAN ####\n"+"\n".join([str(x) for x in debug_cursor.fetchall()]) + "\n########"
                        print >> sys.stderr, queryplan
                    except sqlite.OperationalError:
                        print >> sys.stderr, "(Could not retrieve query plan)"
                        pass
                    debug_cursor.close()

        def fetchone(self):
            return self.cursor.fetchone()

        def fetchall(self):
            return self.cursor.fetchall()

        def close(self):
            return self.cursor.close()

        @property
        def description(self):
            return self.cursor.description

        def __iter__(self):
            for row in self.cursor:
                yield row

    def cursor(self):
        return self.SqliteCursor(self)

    def table_exists(self, name, cursor=None):
        result = self.query("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,), cursor=cursor)    
        if result == []:
            return False
        return True

    def create_table(self, name, primkey, columnnames, columntypes, cursor=None, index=None):
        sql = primkey+" INTEGER PRIMARY KEY"
        for i in range(len(columnnames)):
            if columntypes[i] == int:
                typestr = "INTEGER"
            elif columntypes[i] == float:
                typestr = "REAL"
            elif columntypes[i] == str:
                typestr = "TEXT"
            elif columntypes[i] == FracScalar:
                typestr = "INTEGER"
            elif columntypes[i] == bool:
                typestr = "INTEGER"
            else:
                raise Exception("backend.Sqlite.create_table: column of unrecognized type: "+str(columntypes[i])+" ("+str(columntypes[i].__class__)+")")                      
            
            sql += ", "+columnnames[i]+" "+typestr
            
        self.modify_structure("CREATE TABLE "+name+" ("+sql+")", (), cursor=cursor)    
        if index is not None:
            for ind in index:
                if isinstance(ind, tuple):
                    indexname = "__".join(ind)
                    indexcolumns = ",".join(ind)
                    self.modify_structure("CREATE INDEX "+name+"_"+indexname+"_index"+" ON "+name+"("+indexcolumns+")", (), cursor=cursor)    
                else:
                    self.modify_structure("CREATE INDEX "+name+"_"+ind+"_index"+" ON "+name+"("+ind+")", (), cursor=cursor)    

    def insert_row(self, name, columnnames, columnvalues, cursor=None):
        if len(columnvalues) > 0:
            return self.insert("INSERT INTO "+name+" ("+(",".join(columnnames))+") VALUES ("+(",".join(["?"]*len(columnvalues)))+" )", columnvalues, cursor=cursor)  
        else:
            return self.insert("INSERT INTO "+name + " DEFAULT VALUES", (), cursor=cursor)  

    def update_row(self, name, primkeyname, primkey, columnnames, columnvalues, cursor=None):
        if len(columnvalues) == 0:
            return
        return self.update("UPDATE "+name+" SET "+(" = ?,".join(columnnames))+" = ? WHERE "+primkeyname+" = ?", columnvalues + [primkey], cursor=cursor)  

    def get_val(self, table, primkeyname, primkey, columnname, cursor=None):
        result = self.query("SELECT "+columnname+" FROM "+table+" WHERE "+primkeyname+" = ?", [primkey], cursor=cursor)
        val = result[0][0]
        return val

    def get_row(self, table, primkeyname, primkey, columnnames, cursor=None):
        columnstr = ",".join(columnnames)
        return self.query("SELECT "+columnstr+" FROM "+table+" WHERE "+primkeyname+" = ?", [primkey], cursor=cursor)  

    def get_rows(self, table, primkeyname, primkeys, columnnames, cursor=None):
        columnstr = ",".join(columnnames)
        return self.query("SELECT "+columnstr+" FROM "+table+" WHERE "+primkeyname+" = "+("or".join(["?"]*len(primkeys))), primkeys, cursor=cursor)
        
    def query(self, sql, values, cursor=None):
        if cursor is None:
            cursor = self.cursor()
            cursor.execute(sql, values)
            result = cursor.fetchall()
            cursor.close()
            return result
        else:
            cursor.execute(sql, values)
            return cursor.fetchall()
                
    def insert(self, sql, values, cursor=None):
        if cursor is None:
            cursor = self.cursor()
            cursor.execute(sql, values)
            cursor.commit()
            lid = cursor.cursor.lastrowid
            cursor.close()
        else:
            cursor.execute(sql, values)
            lid = cursor.cursor.lastrowid
        return lid

    def update(self, sql, values, cursor=None):
        if cursor is None:
            cursor = self.cursor()
            cursor.execute(sql, values)
            cursor.commit()
            lid = cursor.cursor.lastrowid
            cursor.close()
        else:
            cursor.execute(sql, values)
            lid = cursor.cursor.lastrowid
        return lid
    
    def alter(self, sql, values, cursor=None):
        if cursor is None:
            cursor = self.cursor()
            cursor.execute(sql, values)
            cursor.commit()
            cursor.close()
        else:
            cursor.execute(sql, values)

    def modify_structure(self, sql, values, cursor=None):
        if cursor is None:
            cursor = self.cursor()
            cursor.execute(sql, values)
            cursor.commit()
            cursor.close()
        else:
            cursor.execute(sql, values)
            
