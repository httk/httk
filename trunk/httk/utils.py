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
Provides a few very simple utility functions
"""

import re, errno, os, itertools, sys, tempfile, shutil, collections
from core.ioadapters import IoAdapterFileReader

def is_unary(e):
    if type(e)==str:
        return True
    try:
        dummy = iter(e)
        return False
    except TypeError:
        return True

def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el

def parse_parexpr(string):
    """Generate parenthesized contents in string as pairs (level, contents)."""
    stack = []
    for i, c in enumerate(string):
        if c == '(':
            stack.append(i)
        elif c == ')' and stack:
            start = stack.pop()
            yield (len(stack), string[start + 1: i])

# Create and destroy temporary directories in a very safe way
def create_tmpdir():
    return tempfile.mkdtemp(".httktmp","httktmp.")

def destroy_tmpdir(tmpdir):
    tmpdirname = os.path.dirname(tmpdir)
    segment = os.path.basename(tmpdir)[len("httktmp."):-len(".httktmp")]
    #print "DELETING:",os.path.join(tmpdirname,"httktmp."+segment+".httktmp")
    shutil.rmtree(os.path.join(tmpdirname,"httktmp."+segment+".httktmp"))

def tuple_to_str(t):
    strlist = []
    for i in t:
        if isinstance(i,tuple):
            tuplestr = "\n"
            tuplestr += tuple_to_str(i)
            #tuplestr += "\n"
            strlist.append(tuplestr)
        else:
            strlist.append(str(i))
    return " ".join(strlist)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def micro_pyawk(ioa, search, results=None, debug=False, debugfunc=None, postdebugfunc=None):
    """
    Small awk-mimicking search routine.
       
    'f' is stream object to search through.
    'search' is the "search program", a list of lists/tuples with 3 elements; i.e.
      [[regex,test,run],[regex,test,run],...]
    'results' is a an object that your search program will have access to for storing results.

    Here regex is either as a Regex object, or a string that we compile into a Regex.
    test and run are callable objects.

    This function goes through each line in filename, and if regex matches that line *and* 
    test(results,line)==True (or test == None) we execute run(results,match), 
    where match is the match object from running Regex.match.   
    
    The default results is an empty dictionary. Passing a results object let you interact 
    with it in run() and test(). Hence, in many occasions it is thus clever to use results=self. 
    
    Returns: results
    """
    ioa = IoAdapterFileReader.use(ioa)
    f = ioa.file
    
    if results == None: results = {}

    # Compile strings into regexs
    for entry in search:
        if isinstance(entry[0], str):
            try:
                entry[0] = re.compile(entry[0])
            except Exception as e:
                raise Exception("Could not compile regular expression:"+entry[0]+" error: "+str(e))
            
    for line in f:
        if debug: sys.stdout.write("\n" + line[:-1])
        for i in range(len(search)):
            match = search[i][0].search(line)
            if debug and match: sys.stdout.write(": MATCH")
            if match and (search[i][1] == None or search[i][1](results,line)):
                if debug: sys.stdout.write(": TRIGGER")
                if debugfunc != None:
                    debugfunc(results,match)
                search[i][2](results,match)
                if postdebugfunc != None:
                    postdebugfunc(results,match)
    if debug: sys.stdout.write("\n")

    ioa.close()
    return results

def breath_first_idxs(dim=1, start=None, end=None, perm=True):

    if start == None:
        start = [0]*dim
    elif len(start) != dim:
        start = [start]*dim

    if end == None:
        end = [None]*dim
    elif len(end) != dim:
        end = [end]*dim

    eles = itertools.count(start[0])

    if dim==1:
        for e in eles:
            yield (e,)
            if end[0] != None and e >= end[0]:
                return
   
    for e in eles:
        oeles = breath_first_idxs(dim-1, start=start[1:], end=[e]*(dim-1),perm=False)
        for oe in oeles:
            base = (e,) + oe
            if perm:
                for p in set(itertools.permutations(base)):
                    yield p
            else:
                yield base
        if end[0] != None and e >= end[0]:
            return

# def breath_first_loop_x(*iterables):
#     
#     if len(iterables) == 1:
#         for element in iterables[0]:
#             yield (element,)
#         return
# 
#     car = iterables[0]
#     cdr = iterables[1:]
# 
#     for element in car:
#         for rest in breath_first_loop_x(*cdr):
#             yield (element,) + rest


try:
    # Python 2
    import ConfigParser as configparser
except ImportError:
    # Python 3
    import configparser

def read_config(ioa):
    ioa = IoAdapterFileReader.use(ioa)
    f = ioa.file
        
    config = configparser.ConfigParser()
    config.readfp(f)

    return config
