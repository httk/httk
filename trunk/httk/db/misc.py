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

import dbcomputation
import tempfile, os, shutil

def register_code(store,name,ver,refs=None):
    # Find the present instance of 'code', if it does not exist, create it    
    if refs == None:
        refs = {}
    
    search = store.searcher()
    code = dbcomputation.DbCode.variable(search, 'code')
    search.add(code.name == name)
    search.add(code.version == ver)
    search.output(code,'code')

    matches = list(search)

    if len(matches) > 0:
        print "==== Code found in database."
        codeobj = matches[0][0][0]
        refsobjs = dbcomputation.DbCodeReference.find_all(store, 'code', codeobj)
    else:
        print "==== Code not found in database, creating entry."
        codeobj = dbcomputation.DbCode(name, ver, store=store)
        refsobjs = dbcomputation.DbCodeReference.merge(codeobj, refs, store=store)

    checkrefs = [x.reference.reference for x in refsobjs]

    if set(checkrefs) != set(refs):
        raise Exception("Code found in database, but references do not match:"+str(checkrefs)+" vs. "+str(refs))
        
    return codeobj

def find_computation(store,input_hexhash):
    # Find the present instance of 'code', if it does not exist, create it    
    search = store.searcher()
    c = dbcomputation.DbComputation.variable(search, 'c')
    search.add(c.input_hexhash == input_hexhash)
    search.output(c,'computation')

    matches = list(search)

    if len(matches) > 0:
        return matches[0][0][0]
    else:
        return None

