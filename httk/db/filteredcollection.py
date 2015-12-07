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

from __future__ import division
import itertools, os, sys, re, inspect


class FilteredCollection(object):

    """ 
    Main interface for filtered collections.

    Apart from what is declared here, each subclass should define e.g. 'table', 'column', 'function' methods for
    defining fields for use for filters (in, e.g., set_filter) and expressions (in, e.g., set_columns).
    """

    def __init__(self):
        self.tables = []
        self.roottables = []
        self.filterexprs = []
        self.postfilterexprs = []
        self.columns = []
        self.sorts = []
        self.indirection = 1
        self._storable_tables = 0

    def add(self, filterexpr):
        """
        Append a filter to the filters currently filtering the FilteredCollection. When iterating over the 
        FilteredCollection, a result is only included if it matches all the filters.
        """        
        self.filterexprs.append(filterexpr)

    def add_all(self, filterexpr):
        """
        Append a filter to the filters currently filtering the FilteredCollection. When iterating over the 
        FilteredCollection, a result is only included if it matches all the filters.
        """
        self.postfilterexprs.append(filterexpr)

    def output(self, expression, name=None):
        """
        Define which columns should be included in the results when iterating over a FilteredCollection. 
        attributes is a list of tuples consisting of (name,definition) where definition can be any
        expression in columns.

        Default is to show all columns of all tables defined. (See FilteredColleciton.table)
        """
        #if isinstance(expression,TableOrColumn):
        #    expression = TableOrColumn(expression.context,expression.name+"_id")
        self.columns.append((name, expression))

    def reset(self):
        """
        Clear any filtering done on the data source.
        """
        self.tables = []
        self.roottables = []
        self.filterexprs = []
        self.postfilterexprs = []
        self.columns = []
        self.sorts = []

    def store_table(self, name):
        """
        Store the result of the filtered collection in a new table named 'name'.
        """
        raise Exception("store_table not implemented.")

    def add_sort(self, expression, direction='ASC'):
        """
        Define which columns should be included in the results when iterating over a FilteredCollection. 
        attributes is a list of tuples consisting of (name,definition) where definition can be any
        expression in columns.

        Default is to show all columns of all tables defined. (See FilteredColleciton.table)
        """
        self.sorts.append((expression, direction))

    def duplicate(self, other):
        other.tables = list(self.tables)
        other.roottables = list(self.roottables)
        other.filterexprs = list(self.filterexpr)
        other.columns = list(self.columns)

    def variable(self, obj, outid=None, parent=None, parentkey=None, subkey=None):
        types = obj.types()
        #types = {"name":obj.object_name, "keys":obj.object_properties, "keydict":dict(obj.object_properties), "index":obj.object_index}
        self.store.new(types['name'], types)

        if outid is None:
            outid = types['name']+"_"+str(self._storable_tables)
            self._storable_tables += 1
        table = TableOrColumn(self, types['name'], parent=parent, outid=outid, key=parentkey, subkey=subkey, indirection=1, classref=obj)
        return table


class FCDict(FilteredCollection):

    """
    This implements a filtered collection purely backed by a dictionary and python evaluation. 

    Note: FCSqliteMemory will usually be faster. (However, you need this class if
    you need to express filters and expressions using python functions rather than Sqlite functions.)
    """

    def __init__(self, data=None):
        """ 
        #Data should be a list of dictionaries, such that [{column1:value1a, column2:value2a, ...},
        #{column1:value1b, column2:value2b}, ...] 

        Data should be a list of tuples, such that [([value1a, value2a, ...],[column1, column2]), 
         ([value1b, value2b, ...],[column1, column2]), ...]
        """
        super(FCDict, self).__init__()
        self._data = data
        self.indirection = 1

    def copy(self):
        new = FCDict()
        self.duplicate(new)
        new._data = self._data
        return new

    def function(self, name):
        """
        Define a python function object for use when expressing filter queries and column expressions.
        (You cannot define a filter with a "bare function", since it would be called
        directly at the point of defining the filter.)
        Validy/existence of this function is not checked until the collection is iterated over.
        """
        return DeclaredFunction(self, name)

    def data(self, outid=None):
        """
        Return an object where the attributes are accessible as properties. I.e. 
          data = myFCDict.data
          myFCDict.set_filter(data.example == data.otherexample*2)
        """
        table = TableOrColumn(self, "data", outid=outid, indirection=self.indirection)
        return table

    def __iter__(self):
        """
        Iterate over all results matching set filters.
        """
        loops = []
        for table in self.tables:
            loops.append(self._data)
        for i in itertools.product(*loops):

            data = {}
            headers = []
            outdata = []
            # old format with dictionaries, should possibly re-invoke this as an alt repr.
            #for j in range(len(i)):
            #    for element in i[j]:
            #        data[self.tables[j].outid+"."+element] = i[j][element]
            #        outdata.append(i[j][element])
            #        headers.append(self.tables[j].outid+"."+element)

            for j in range(len(i)):
                for k in range(len(i[j][0])):                                        
                    data[self.tables[j].outid+"."+i[j][1][k]] = i[j][0][k]
                    outdata.append(i[j][0][k])
                    headers.append(self.tables[j].outid+"."+i[j][1][k])

            # Need to check subtable criteria 
            # (needed here if someone uses the table as its own subtable, which seems weird but is possible)
            # E.g., roads(fromcity:name, tocity:name) can be subtabled with itself to see where you can get in two hops.
            for table in self.tables:
                if not table.check_subtable_on(data):
                    break
            else:
                # This is executed if all subtable checks come out True.
                # The awkward flow with this inside the else: on a for, is due to Python missing "break 2"
                result = True
                for filterexpr in self.filterexprs:
                    result = result and filterexpr.evaluate(data)

                if result:
                    yield (outdata, headers)


class FCMultiDict(FilteredCollection):

    """
    This class allows you to combine a number of filtered collections and put filters on any combination
    of them together. Just create a separate FilteredCollection from each data source, and pass them in 
    a list to the constructor of this class.

    Filters that only apply to one of the FilteredCollections can be put on those collections instead,
    while a filter that applies to more than one must be set on this class.
    """

    def __init__(self, data=None):
        """
        Data is a dictionary of filtered collections on form data={name1:fc1, name2:fc2, ...}
        """
        super(FCMultiDict, self).__init__()
        if data is None:
            self._data = {}
        else:
            self._data = data

    def copy(self):
        new = FCMultiDict()
        self.duplicate(new)
        new._data = self._data
        return new

    def add(self, filterexpr):
        """
        Append a filter to the filters currently filtering the FilteredCollection. When iterating over the 
        FilteredCollection, a result is only included if it matches all the filters.
        """
        context = filterexpr.get_srctable_context()
        # If context comes back as 'MIXED', this is a mixed context expression. That means the MultiDict needs
        # to perform the search itself.
        if context is None:
            raise Exception("add cannot add context-less expressions, i.e., at least one column must be present in the expression.")
        if context == 'MIXED':
            self.filterexprs.append(filterexpr)
        else:
            context.add(filterexpr)

    def data(self, name, outid=None):
        """
        Return an object where the attributes of respective filtered collection is
        accessible as attributes. An example:
        
          languagereview = FCMultiDict('programming':programming_fc, 'review':review_fc)
          language = languagereview.data('programming').language
          review = languagereview.data('review')
          myFCMultiDict.set_filter(language.name == "python" & review.goodness > 9)

        """
        if outid is None:
            outid = "data_"+str(len(self.tables))
        srctable = TableOrColumn(self._data[name], name, outid=outid, indirection=self._data[name].indirection)
        table = TableOrColumn(self, name, outid=outid, srctable=srctable, indirection=self._data[name].indirection)
        return table

    def subdata(self, name, table, outid=None, key='rowid', subkey=None):
        """
        Return an object where the attributes of respective filtered collection is
        accessible as attributes. An example:

          languagereview = FCMultiDict('programming':programming_fc, 'review':review_fc)
          language = languagereview.data('programming').language
          review = languagereview.data('review')
          myFCMultiDict.set_filter(language.name == "python" & review.goodness > 9)

        """
        if outid is None:
            outid = table.name+"_"+name+"_"+str(len(self.tables))

        if table.context == self._data[name]:
            srctable = TableOrColumn(self._data[name], name, parent=table, outid=outid, key=key, subkey=subkey, indirection=self._data[name].indirection)
        else:
            srctable = TableOrColumn(self._data[name], name, outid=outid)
        table = TableOrColumn(self, name, parent=table, outid=outid, key=key, subkey=subkey, srctable=srctable, indirection=self._data[name].indirection)
        return table

    def __iter__(self):
        """
        Iterate over all results matching set filters.

        This can be made highly more optimized by doing the itertools.product only for proper tables (not subtables),
        and then set filters to handle the subtables. However, what happens when we have subtables of subtables?
        """
        loops = []
        for table in self.tables:
            loops.append(self._data[table.name])

        for i in itertools.product(*loops):
            data = {}
            headers = []
            outdata = []
            for j in range(len(i)):
                for k in range(len(i[j][0])):                                        
                    data[i[j][1][k]] = i[j][0][k]
                    outdata.append(i[j][0][k])
                    headers.append(i[j][1][k])

            for table in self.tables:
                if not table.check_subtable_on(data):
                    break
            else:
                # This is executed if all subtable checks come out True.
                # The awkward flow with this inside the else: on a for, is due to Python missing "break 2"
                result = True
                for filterexpr in self.filterexprs:
                    result = result and filterexpr.evaluate(data)

                if result:
                    yield (outdata, headers)

# Micro sqlite api to make sure all open databases gets closed on program termination
#from pysqlite2 import dbapi2 as sqlite
# import sqlite3 as sqlite
# sqliteconnections = set()
# database_debug = 0
# def sqlite_open_protected(filename):
#     global sqliteconnections
#     connection = sqlite.connect(filename)
#     sqliteconnections.add(connection)
#     return connection
# 
# def sqlite_close_protected(connection):
#     global sqliteconnections
#     sqliteconnections.remove(connection)
#     connection.close()
# 
# def sqlite_close_all():
#     global sqliteconnections
#     for connection in sqliteconnections:
#         connection.close()
# 
# def sqlite_execute(cursor, sql, values=[]):
#     global database_debug
#     if os.environ.has_key('DATABASE_DEBUG') or database_debug:
#         print >> sys.stderr, "SQL:"+sql
#     try:
#         cursor.execute(sql,values)
#     except:
#         raise Exception("Error executing SQL:"+sql)
# 
# import atexit
# atexit.register(sqlite_close_all)
###############################################################


def instantiate_from_store(classobj, store, id):
    types = classobj.types()
    output = store.retrieve(types['name'], types, id)
    args = types['init_keydict'].keys()
    calldict = {}
    #print "ARGS",args, output, id
    for arg in args:
        try:
            calldict[arg] = output[arg]
        except KeyError:
            pass
    #print "CALLDICT",classobj,calldict
    try:
        newobj = classobj(**calldict)
    except TypeError:
        print "Error when trying to create a new object", classobj, calldict
        raise
    newobj.db.sid = id
    # TODO: The handling of codependent data is a mess and really should be better abstracted up in HttkObject
    if hasattr(newobj, '_codependent_callbacks'):
        newobj._codependent_callbacks += [lambda x, y=store: x.db.fetch_codependent_data(y)]
    return newobj


class FCSqlite(FilteredCollection):

    def __init__(self, sqlstore):
        super(FCSqlite, self).__init__()
        self.sqliteconnection = sqlstore.db
        self.store = sqlstore
        self.indirection = 1

    def table(self, name, outid=None):
        """
        Defines a table object to use in filters (for add) and expressions (in set_columns).
        """
        if outid is None:
            outid = name+"_"+str(len(self.tables))
        table = TableOrColumn(self, name, outid=outid, indirection=self.indirection)
        return table

    def subtable(self, name, table, outid=None, key='rowid', subkey=None):
        """
        Defines a table object to use in filters (for add) and expressions (in set_columns).
        """
        if outid is None:
            outid = table._name+"_"+name+"_"+str(len(self.tables))
        table = TableOrColumn(self, name, parent=table, outid=outid, key=key, subkey=subkey, indirection=self.indirection)
        return table

    def function(self, name):
        """
        Define a function object for expressing functions in filter queries. Validity/existence of this function
        may not be tested until an iteration over matching entries is performed.
        """
        return DeclaredFunction(self, name)

    def store_table(self, name):
        sql = "CREATE TABLE "+name+" AS "+self.sql()
        cursor = self.sqliteconnection.cursor()
        cursor.execute("DROP TABLE IF EXISTS "+name+";")
        cursor.execute("PRAGMA full_column_names = true;")
        cursor.execute("PRAGMA short_column_names = false;")       
        #sqlstr = self.sql()
        cursor.execute(sql)        

    def sql(self):
        sqlstr = ""
        sqlstr += "SELECT\n"
        if len(self.columns) == 0:
            sqlstr += " *\n"
        else:
            sqlstr += "  "+", \n  ".join([c[1]._sql()+" "+c[0] for c in self.columns])+" \n"
        sqlstr += "FROM\n"
        tablelist = []
        groupset = set()
        for table in self.tables:
            tablelist.append(table._declare())
            groupby = table._groupby()
            if groupby is not None:
                groupset.add(groupby)
        #tablelist = [table.tablename+" "+table.outid for table in self.tables]
        sqlstr += "  "+" LEFT OUTER JOIN \n  ".join(tablelist)+"\n"
        if len(self.filterexprs) > 0:
            sqlstr += "WHERE\n"
            sqlstr += "  (\n    " + "\n  )  AND  (\n    ".join([x._sql() for x in self.filterexprs]) + "\n  )\n"     
        if len(groupset) > 0:
            sqlstr += "GROUP BY\n  "
            sqlstr += ",\n  ".join(groupset) + "\n"

        if len(self.postfilterexprs) > 0:
            sqlstr += "HAVING\n"
            sqlstr += "  ( SUM ( NOT (\n    " + "\n    )) = 0\n  ) AND (SUM ( NOT (\n    ".join([x._sql() for x in self.postfilterexprs]) + "\n    )) = 0\n  )\n"

        if len(self.sorts) > 0:
            sqlstr += "ORDER BY\n  "
            sqlstr += ",\n  ".join([s[0]._sql()+" "+s[1] for s in self.sorts]) + "\n"
        
        sqlstr += ";\n"
        return sqlstr

    def __iter__(self):
        sql = self.sql()
        cursor = self.sqliteconnection.cursor()
        #cursor.execute("PRAGMA full_column_names = true;")
        #cursor.execute("PRAGMA short_column_names = false;")
        cursor.execute(sql)

        if len(self.columns) == 0:
            headers = tuple([c[0] for c in cursor.description])
            mustreplace = []
        else:
            columns = self.columns
            mustreplace = []
            headers = tuple([c[0] for c in columns])
            for i in range(len(self.columns)):
                c = self.columns[i]
                if c[1]._classref is not None:
                    mustreplace.append((i, c[1]._classref,))

        #description = cursor.description
        #for entry in cursor:
        #    data = {}
        #    for i in range(len(description)):
        #        data[description[i][0]] = entry[i]
        #    yield data

        #cursor.row_factory = sqlite.Row
            
        #cursor.text_factory = str

        # A bit of premature optimization
        
        if len(mustreplace) == 0:        
            for entry in cursor:            
                yield (entry, headers)
        else:
            for entry in cursor:    
                entry = list(entry)                
                for replace in mustreplace:
                    entry[replace[0]] = instantiate_from_store(replace[1], self.store, entry[replace[0]])
                    #entry[replace[0]] = replace[1].instantiate_from_store(self.store,entry[replace[0]])
                yield (entry, headers)

        cursor.close()


class FCMultiSqlite(FilteredCollection):

    """
    This class allows you to combine a number of filtered collections and put filters on any combination
    of them together. Just create a separate FilteredCollection from each data source, and pass them in 
    a list to the constructor of this class.

    Filters that only apply to one of the FilteredCollections should preferably be put on those collections,
    while a filter that applies to more than one must be set on this class, *using field definitions made
    with this class*.
    """

    def __init__(self, dicts=None):
        super(FCMultiSqlite, self).__init__()
        self.dicts = dicts


def fc_eval(expr, data):
    if hasattr(expr, '_evaluate'):
        return expr._evaluate(data)
    else:
        return expr


def fc_sql(expr):
    if hasattr(expr, '_sql'):
        #print "HERE",expr._sql(), expr.__class__
        return expr._sql()
    elif isinstance(expr, (str, unicode)):
        # TODO: Fix quoting system
        return "\""+str(expr).replace("'", "''")+"\""

#    try:
#        return "\""+str(expr.hexhash)+"\""
#    except Exception:
    try:
        return str(expr.db.sid) 
    except Exception:
        return str(expr)


def fc_get_srctable_context(*args):
    firstcontext = None
    for arg in args:
        if hasattr(arg, '_get_srctable_context'):
            newcontext = arg._get_srctable_context()        
            if firstcontext is None:
                firstcontext = newcontext
            else:
                if firstcontext != newcontext:
                    return 'MIXED'
    return firstcontext


def fc_checkcontext(context, *exprs):
    for expr in exprs:
        if hasattr(expr, '_evaluate'):
            if expr._context != context:
                    raise Exception("Cannot relate expressions from different contexts!")


class Expression(object):

    def __init__(self, context, exprtype, *args):
        """
        exprtype should be 'bool','value','unknown'
        """        
        fc_checkcontext(context, *args)
        self._context = context
        self._args = args
        self._exprtype = exprtype

    #def eval(self,data):        
    #    evaledargs = [fc_eval(arg,data) for arg in self.args]
    #    return eval(self.name+"(" + ",".join([str(x) for x in self.evaledargs]) + ")")

    def get_srctable_context(self):
        return fc_get_srctable_context(*self._args)

    #def sql(self):
    #    return self.name+"(" + ",".join([fc_sql(x) for x in self.args]) + ")"

    def __eq__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: equality test with expression of wrong type.")
        return BinaryComparison(self._context, "=", self, other)

    def __ne__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: not equal test with expression of wrong type.")
        return BinaryComparison(self._context, "!=", self, other)

    def __gt__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: greater than test with expression of wrong type.")
        return BinaryComparison(self._context, ">", self, other)

    def __lt__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: less than test with expression of wrong type.")
        return BinaryComparison(self._context, "<", self, other)

    def __ge__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: greater equal test with expression of wrong type.")
        return BinaryComparison(self._context, ">=", self, other)

    def __le__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: less equal test with expression of wrong type.")
        return BinaryComparison(self._context, "<=", self, other)

    def __add__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: add operator with expression of wrong type.")
        return BinaryOp(self._context, "+", self, other)

    def __sub__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: sub operator with expression of wrong type.")
        return BinaryOp(self._context, "-", self, other)

    def __rsub__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: sub operator with expression of wrong type.")
        return BinaryOp(self._context, "-", other, self)

    def __mul__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: mul operator with expression of wrong type.")
        return BinaryOp(self._context, "*", self, other)

    def __div__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: div operator with expression of wrong type.")
        return BinaryOp(self._context, "/", self, other)

    def __truediv__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: div operator with expression of wrong type.")
        return BinaryOp(self._context, "/", self, other)

    def __floordiv__(self, other):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: strcat operator with expression of wrong type.")
        # This depends on the SQL server...
        # For ORACLE MYSQL etc
        # return Function(self._context,"CONCAT",self,other)
        # Sqlite
        return BinaryOp(self._context, "||", self, other)

    def is_in(self, *args):
        if not self._exprtype in ('value', 'unknown'):
            raise Exception("Syntax error: is_in operator with expression of wrong type.")
        return BinaryBooleanOp(self._context, "IN", self, args)

    def __and__(self, other):
        if not self._exprtype in ('bool', 'unknown'):
            raise Exception("Syntax error: and with expression of wrong type.")
        return BinaryBooleanOp(self._context, "and", self, other)

    def __or__(self, other):
        if not self._exprtype in ('bool', 'unknown'):
            raise Exception("Syntax error: or with expression of wrong type.")
        return BinaryBooleanOp(self._context, "or", self, other)

    def __xor__(self, other):
        if not self._exprtype in ('bool', 'unknown'):
            raise Exception("Syntax error: xor with expression of wrong type.")
        return BinaryBooleanOp(self._context, "xor", self, other)

    def __invert__(self):
        if not self._exprtype in ('bool', 'unknown'):
            raise Exception("Syntax error: invert with expression of wrong type.")
        return UnaryBooleanOp(self._context, "not", self)


class Function(Expression):

    def __init__(self, context, name, srctable, *args):
        fc_checkcontext(context, *args)
        Expression.__init__(self, context, 'unknown', *args)
        self._name = name
        self._srctable = srctable

    # get_srctable_context needs to be overridden, because a functions context can ony ever be the
    # context it was declared in.
    def _get_srctable_context(self, data):
        return self._srctable

    def _sql(self):
        return self._name+"(" + ",".join([fc_sql(x) for x in self._args]) + ")"


class UnaryBooleanOp(Expression):

    def __init__(self, context, operator, right):
        fc_checkcontext(context, right)
        Expression.__init__(self, context, 'bool', right)
        self._operator = operator
        self._right = right

    def _evaluate(self, data):
        if self._operator == 'not':
            return not fc_eval(self._args[1], data)
        else:
            raise Exception("Syntax Error")

    def _sql(self):
        if self._operator in ('not'):
            return self._operator + fc_sql(self._args[0])
        else:
            raise Exception("Syntax Error" + self._operator)


class BinaryBooleanOp(Expression):

    def __init__(self, context, operator, left, right):
        fc_checkcontext(context, left, right)
        Expression.__init__(self, context, 'bool', left, right)
        self._operator = operator

    def _evaluate(self, data):
        if self._operator == 'and':
            return fc_eval(self._args[0], data) and fc_eval(self._args[1], data)
        elif self._operator == 'or':
            return fc_eval(self._args[0], data) or fc_eval(self._args[1], data)
        elif self._operator == 'xor':
            # python doesn't have "xor"? Maybe ^ would do, though.
            l = fc_eval(self._args[0], data)
            r = fc_eval(self._args[1], data)
            return (l and (not r)) or ((not l) and r)
        else:
            raise Exception("Syntax Error")

    def _sql(self):
        if self._operator in ('and', 'or', 'xor'):
            return "("+fc_sql(self._args[0]) + " "+self._operator+" " + fc_sql(self._args[1])+")"
        elif self._operator in ('IN'):
            return "("+fc_sql(self._args[0]) + " IN (" + ",".join([fc_sql(a) for a in self._args[1]])+"))"            
        else:
            raise Exception("Syntax Error generating SQL for operator: " + self._operator)


class BinaryComparison(Expression):

    def __init__(self, context, operator, left, right):
        fc_checkcontext(context, left, right)
        Expression.__init__(self, context, 'bool', left, right)
        self._operator = operator

    def _evaluate(self, data):
        if self._operator == '=':
            return fc_eval(self._args[0], data) == fc_eval(self._args[1], data)
        elif self._operator == '<':
            return fc_eval(self._args[0], data) < fc_eval(self._args[1], data)
        elif self._operator == '>':
            return fc_eval(self._args[0], data) > fc_eval(self._args[1], data)
        elif self._operator == '>=':
            return fc_eval(self._args[0], data) >= fc_eval(self._args[1], data)
        elif self._operator == '<=':
            return fc_eval(self._args[0], data) <= fc_eval(self._args[1], data)
        elif self._operator == '!=':
            return fc_eval(self._args[0], data) != fc_eval(self._args[1], data)
        else:
            raise Exception("Syntax Error")

    def _sql(self):
        op = self._operator
        leftarg = None
        rightarg = None
        if self._args[0] is None:
            leftarg = 'NULL'
        elif self._args[0] is True:
            leftarg = '1'
        elif self._args[0] is False:
            leftarg = '0'
        else:
            leftarg = fc_sql(self._args[0])
        if self._args[1] is None:
            rightarg = 'NULL'
        elif self._args[1] is True:
            rightarg = '1'
        elif self._args[1] is False:
            rightarg = '0'
        else:
            rightarg = fc_sql(self._args[1])
        if leftarg == 'NULL' or rightarg == 'NULL':
            if self._operator == '=':
                op = 'IS'
            elif self._operator == '!=':
                op = 'IS NOT'            
            if leftarg == 'NULL' and rightarg != 'NULL': 
                leftarg, rightarg = rightarg, leftarg                

        if self._operator in ('=', '<', '>', '>=', '<=', '!='):
            return "("+leftarg + " "+op+" " + rightarg+")"
        else:
            raise Exception("Syntax Error" + self._operator)
        
#         if self._operator == '=' and self._args[0] is None and self._args[1] is None:
#             return "(NULL IS NULL)"
#         elif self._operator == '=' and self._args[0] is None:
#             return "("+fc_sql(self._args[1])+" IS NULL)"
#         elif self._operator == '=' and self._args[1] is None:
#             return "("+fc_sql(self._args[1])+" IS NULL)"
#         if self._operator == '!=' and self._args[0] is None and self._args[1] is None:
#             return "(NULL IS NOT NULL)"
#         elif self._operator == '!=' and self._args[0] is None:
#             return "("+fc_sql(self._args[1])+" IS NOT NULL)"
#         elif self._operator == '!=' and self._args[1] is None:
#             return "("+fc_sql(self._args[1])+" IS NOT NULL)"
#         elif self._operator in ('=','<','>','>=','<=','!='):
#             return "("+fc_sql(self._args[0]) + " "+self._operator+" " + fc_sql(self._args[1])+")"
#         else:
#             raise Exception("Syntax Error" + self._operator)


class BinaryOp(Expression):

    def __init__(self, context, operator, left, right):
        fc_checkcontext(context, left, right)
        Expression.__init__(self, context, 'value', left, right)
        self._operator = operator

    def _evaluate(self, data):
        if self._operator == '||':
            return fc_eval(self._args[0], data) + fc_eval(self._args[1], data)
        if self._operator == '+':
            return fc_eval(self._args[0], data) + fc_eval(self._args[1], data)
        elif self._operator == '-':
            return fc_eval(self._args[0], data) - fc_eval(self._args[1], data)
        elif self._operator == '*':
            return fc_eval(self._args[0], data) * fc_eval(self._args[1], data)
        elif self._operator == '/':
            return fc_eval(self._args[0], data) / fc_eval(self._args[1], data)
        else:
            raise Exception("Syntax Error")

    def _sql(self):
        if self._operator in ('+', '-', '*', '/', '||'):
            return "(" + fc_sql(self._args[0]) + " "+self._operator+" " + fc_sql(self._args[1]) + ")"
        else:
            raise Exception("Syntax Error" + self._operator)


class TableOrColumn(Expression):

    def __init__(self, context, name, parent=None, outid=None, key=None, subkey=None, srctable=None, indirection=1, classref=None):
        Expression.__init__(self, context, 'value')
        self._name = name
        self._parent = parent
        self._iscolumn = False
        self._istable = False
        self._outid = outid
        self._srctable = srctable
        self._subtables = []
        self._indirection = indirection
        self._classref = classref

        self._key = None
        self._subkey = None
       
        # If key is set, this is a subtable, joined on the key column
        if key is not None:
            #print "TABLE OR COLUMN WITH KEY",subkey
            self._key = key
            if subkey is None:
                self._subkey = self._key
            else:
                self._subkey = subkey
            if parent is None:
                raise Exception("Cannot set key, and still not give a parent.")
            parent._add_subtable(self)
            #context.tables.append(self)

        if self._indirection == 1:
            self._declare_as_table()

        if self._indirection == 0:
            self._declare_as_column()

        if self._indirection < 0:
            raise Exception("Syntax error, trying to access subattribute of column.")

    def _add_subtable(self, subtable):
        self._subtables.append(subtable)

    def _declare_as_table(self):
        if self._srctable is not None:
            self._srctable.declare_as_table()
        if not self._istable:
            if self._outid is None:
                if self._parent is not None:
                    self._outid = "t_"+self._parent._outid+"_"+str(len(self._context.tables))
                else:
                    self._outid = "t"+str(len(self._context.tables))
                    
            if self._key is None:
                self._context.roottables.append(self)

            self._context.tables.append(self)
            self._istable = True
        
    def _declare_as_column(self):
        if self._srctable is not None:
            self._srctable._declare_as_column()
        self._iscolumn = True
        if self._parent is not None:
            self._parent._declare_as_table()

    def __getattr__(self, name):
        if self._classref is not None:
            typedict = dict(self._classref.types()['keys']+self._classref.types()['derived'])
            try:
                typex = typedict[name]
                #if isinstance(typex,Storable):
                # Workaround to check if the object is storable without having to do a circular import...
                if hasattr(typex, 'types'):
                    return TableOrColumn(self._context, self._outid + "." + name+"_" + typex.types()['name']+"_sid", self, srctable=self._srctable, indirection=self._indirection-1, classref=typex)
                elif isinstance(typex, list):
                    if typex[0] in self._context.store.basics: 
                        subname = self._name + "_" + name
                        outid = subname + "_" + str(len(self._context.tables))
                        table = TableOrColumn(self._context, subname, parent=self, outid=outid, key=self._name+"_id", subkey=self._name+"_sid", indirection=self._indirection-1)
                        table._declare_as_table()
                        column = TableOrColumn(self._context, outid + "." + name, parent=table, outid=outid, key=None, subkey=None, indirection=self._indirection-1)
                        return column
                    elif isinstance(typex[0], tuple): 
                        subname = self._name + "_" + name
                        outid = subname + "_" + str(len(self._context.tables))
                        table = TableOrColumn(self._context, subname, parent=self, outid=outid, key=self._name+"_id", subkey=self._name+"_sid", indirection=1)
                        table._declare_as_table()
                        #column = TableOrColumn(self._context,outid + "." + name,parent=table,outid=outid,key=None,subkey=None,indirection=self._indirection-1)
                        return table
                        # Handle tuple
                        #print name, self._outid, self._classref
                        #raise Exception("Not implemented yet")
                    if len(typex) == 1 and hasattr(typex[0], 'types'):
                        subname = self._name + "_" + name
                        outid = subname + "_" + str(len(self._context.tables))
                        table = TableOrColumn(self._context, subname, parent=self, outid=outid, key=self._name+"_id", subkey=self._name+"_sid", indirection=self._indirection-1)
                        table._declare_as_table()
                        column = TableOrColumn(self._context, outid + "." + name+"_" + typex[0].types()['name']+"_sid", parent=table, outid=outid, key=None, subkey=None, indirection=self._indirection-1)
                        return column
                    else:
                        # Handle other defined Storable type
                        raise Exception("Not implemented yet")
                else:
                    return TableOrColumn(self._context, self._outid + "." + name, self, srctable=self._srctable, indirection=self._indirection-1)
            except KeyError as e:
                raise Exception("Field "+name+" does not exist:"+str(e))
        else:
            return TableOrColumn(self._context, self._outid + "." + name, self, srctable=self._srctable, indirection=self._indirection-1)

    def _evaluate(self, data):        
        if not self._iscolumn:
            raise Exception("Syntax error: asked to eval column on non-column.")        

        #disolve = self.name.rsplit('.',1)
        #if len(disolve)==2:
        #    return data[disolve[0]][disolve[1]]
        #else:
        #    return data[self.name]
        return data[self._name]

    def _declare(self):
        if not self._istable:
            raise Exception("Syntax error: asked to sql_declare non-table.")
        if self._key is not None:
            return self._name+" "+self._outid + " ON ("+self._outid+"."+self._subkey+" = "+self._parent._outid+"."+self._key + ")"
        else:
            return self._name+" "+self._outid

    def _groupby(self):
        if not self._istable:         
            raise Exception("Syntax error: asked to sql_groupby non-table.")
        if self._key is not None:
            return self._parent._outid+"."+self._key
        else:
            return None

    def _get_srctable_context(self):
        if self._srctable is not None:
            return self._srctable.context
        else:
            return None

    def _check_subtable_on(self, data):
        if not self._istable:         
            raise Exception("Syntax error: asked to check_subtable_on non-table.")
        if self._key is None:
            return True
        else:
            return data[self._outid+"."+self._subkey] == data[self._parent._outid+"."+self._key]

    def _sql(self):
        if not self._iscolumn:
            #print "HUH",self._outid, ".", self._name, "_id"
            return self._outid + "." + self._name+"_id"
            #raise Exception("Syntax error: asked to generate column sql on non-column.")
        return self._name


class DeclaredFunction(object):

    def __init__(self, context, name, srctable=None):
        self._context = context
        self._name = name
        self._srctable = srctable
        
    def __call__(self, *args):
        return Function(self._context, self._name, self._srctable, *args)

