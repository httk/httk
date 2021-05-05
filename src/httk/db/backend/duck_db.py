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
This provides a thin abstraction layer for SQL queries, implemented on top of DuckDB.
"""
from __future__ import print_function
import os, sys, time
import duckdb
import atexit
from httk.core import FracScalar
from httk.core import reraise_from

duckdbconnections = set()
# TODO: Make this flag configurable in httk.cfg
database_debug = False
# database_debug = True
database_debug_slow = False
if 'DATABASE_DEBUG_SLOW' in os.environ:
    database_debug_slow = True
if 'DATABASE_DEBUG' in os.environ:
    database_debug = True


def db_open(filename):
    global duckdbconnections
    connection = duckdb.connect(filename)
    duckdbconnections.add(connection)
    return connection


def db_close(connection):
    global duckdbconnections
    duckdbconnections.remove(connection)
    connection.close()


def db_duckdb_close_all():
    global duckdbconnections
    for connection in duckdbconnections:
        connection.close()

atexit.register(db_duckdb_close_all)


class Duckdb(object):

    def __init__(self, filename):
        self.connection = db_open(filename)
        self.connection.begin()
        #self._block_commit = False
        self.primary_keys = {}
        self.connection.execute("create table if not exists primary_keys(name varchar, value integer)")
        self.connection.execute("select * from primary_keys")
        res = self.connection.fetchall()
        if len(res) > 0:
            for (name, value) in res:
                self.primary_keys[name] = value

    def close(self):
        db_close(self.connection)

    def rollback(self):
        self.connection.rollback()

    def commit(self):
        # Save primary keys:
        self.connection.execute("create table if not exists primary_keys(name varchar, value integer)")
        for name, value in self.primary_keys.items():
            self.connection.execute("select name from primary_keys where name='{}'".format(name))
            res = self.connection.fetchone()
            if res is not None:
                self.connection.execute("delete from primary_keys where name='{}'".format(name))
            self.connection.execute("insert into primary_keys values ('{}', {})".format(name, value))
        self.connection.commit()

    class DuckdbCursor(object):
        """It should be noted that in DuckDB the cursor is frivolous,
        meaning creating a cursor returns a duplicate of the connection object.
        """

        def __init__(self, db):
            self.cursor = db.connection.cursor()
            self.db = db

        def execute(self, sql, values=[]):
            global database_debug
            if database_debug:
                print("DEBUG: EXECUTING SQL:"+sql+" :: "+str(values) + "\n", end="", file=sys.stderr)
            if database_debug_slow:
                time1 = time.time()
            try:
                # DuckDB gives "syntax error near object" and one way
                # I have found to fix that is to remove the "object" keyword
                # from the SQL query.:
                sql = sql.replace("object \n", " \n")
                # Also "header" should be removed:
                sql = sql.replace("header \n", " \n")
                # DuckDB uses "ON" instead of WHERE when doing a JOIN operation:
                if "JOIN" in sql:
                    sql = sql.replace("WHERE", "ON")
                self.cursor.execute(sql, values)
            except Exception as e:
                info = sys.exc_info()
                reraise_from(Exception, "backend.Duckdb: Error while executing sql: "+sql+" with values: "+str(values)+", the error returned was: "+str(info[1]), e)
            if database_debug_slow:
                time2 = time.time()
                if (time2-time1) > 1 and not sql.startswith("CREATE"):
                    debug_cursor = self.db.connection.cursor()
                    print("SLOW DATABASE DEBUG: EXECUTING SQL:"+sql+" :: "+str(values), end="", file=sys.stderr)
                    print("duckdb execute finished in " + str((time2-time1)*1000.0) + " ms", end="", file=sys.stderr)
                    try:
                        debug_cursor.execute("EXPLAIN QUERY PLAN "+sql, values)
                        queryplan = "### QUERY PLAN ####\n"+"\n".join([str(x) for x in debug_cursor.fetchall()]) + "\n########"
                        print(queryplan, end="", file=sys.stderr)
                    except duckdb.OperationalError:
                        print("(Could not retrieve query plan)", end="", file=sys.stderr)
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
            for row in self.cursor.fetchall():
                yield row

    def cursor(self):
        return self.DuckdbCursor(self)

    def table_exists(self, name, cursor=None):
        result = self.query("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,), cursor=cursor)
        if result == []:
            return False
        return True

    def create_table(self, name, primkey, columnnames, columntypes, cursor=None, index=None):
        sql = primkey+" INTEGER PRIMARY KEY"
        # Data types have been modified to correspond to the
        # types that DuckDB expects.
        # Optimize by making certain columns INTEGER, where there is no
        # danger of values being bigger than what INTEGER allows.
        for i in range(len(columnnames)):
            column_name = columnnames[i]
            if column_name.endswith('_id') and not column_name == 'material_id':
                typestr = "INTEGER"
            elif 'orientation' in column_name:
                typestr = "INTEGER"
            elif "_sid" in column_name:
                typestr = "INTEGER"
            elif columntypes[i] == int:
                typestr = "BIGINT"
            elif columntypes[i] == float:
                typestr = "DOUBLE"
            elif columntypes[i] == str:
                typestr = "TEXT"
            elif columntypes[i] == FracScalar:
                typestr = "BIGINT"
            elif columntypes[i] == bool:
                typestr = "INTEGER"
            else:
                raise Exception("backend.Duckdb.create_table: column of unrecognized type: "+str(columntypes[i])+" ("+str(columntypes[i].__class__)+")")

            sql += ", "+columnnames[i]+" "+typestr
        
        # Check if "main table" and if so, record a unique material ID
        # if name.startswith("Result_"):
            # sql += ", " + "material_id" + " " + "TEXT"

        self.modify_structure("CREATE TABLE \""+name+"\" ("+sql+")", (), cursor=cursor)
        if index is not None:
            for ind in index:
                if isinstance(ind, tuple):
                    indexname = "__".join(ind)
                    indexcolumns = ",".join(ind)
                    self.modify_structure("CREATE INDEX "+name+"_"+indexname+"_index"+" ON "+name+"("+indexcolumns+")", (), cursor=cursor)
                else:
                    self.modify_structure("CREATE INDEX "+name+"_"+ind+"_index"+" ON "+name+"("+ind+")", (), cursor=cursor)

    # DuckDB does not support auto-incrementing the primary key.
    # Fix this by keeping track of different tables primary keys manually.
    # TODO: handle auto-incrementing internally using sequences:
    # "CREATE SEQUENCE seq START 1;"
    # CREATE TABLE table (i INTEGER DEFAULT NEXTVAL('seq'), b INTEGER);
    # Also, extra code is needed to make the primary keys persistent.
    def insert_row(self, name, columnnames, columnvalues, cursor=None):
        if len(columnvalues) > 0:
            columnnames = [name+"_id"]+columnnames
            if name not in self.primary_keys.keys():
                self.primary_keys[name] = 1
            columnvalues = [self.primary_keys[name]] + columnvalues

            # Record unique material-id
            if name.startswith("Result_"):
                for i in range(len(columnnames)):
                    if columnnames[i] == 'material_id':
                        columnvalues[i] = "httk-{}".format(self.primary_keys[name])
            lid = self.insert(
                "INSERT INTO " + name + " (" + (",".join(columnnames)) + ") " + \
                "VALUES" + " ("+(",".join(["?"]*(len(columnvalues))))+" )",
                columnvalues, cursor=cursor, key_index=self.primary_keys[name])
            self.primary_keys[name] += 1
            return lid
        else:
            return self.insert("INSERT INTO "+name + " DEFAULT VALUES", (), cursor=cursor)

    def update_row(self, name, primkeyname, primkey, columnnames, columnvalues, cursor=None):
        if len(columnvalues) == 0:
            return
        return self.update("UPDATE "+name+" SET "+(" = ?,".join(columnnames))+" = ? WHERE "+primkeyname+" = ?", columnvalues + [primkey], cursor=cursor)

    def get_val(self, table, primkeyname, primkey, columnname, cursor=None):
        result = self.query("SELECT "+columnname+" FROM "+table+" WHERE "+primkeyname+" = ?", [primkey], cursor=cursor)
        # print(result)
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

    def insert(self, sql, values, cursor=None, key_index=None):
        if cursor is None:
            cursor = self.cursor()
            cursor.execute(sql, values)
            cursor.commit()
            # lid = cursor.cursor.lastrowid
            cursor.close()
        else:
            cursor.execute(sql, values)
            # lid = cursor.cursor.lastrowid
        if key_index is not None:
            lid = key_index
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
