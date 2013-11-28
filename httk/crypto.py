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
Provides a few central and very helpful functions for cryptographic hashes, etc.
"""

import hashlib, os.path
from core.ioadapters import IoAdapterFileReader

def hexhash_str(data,prepend=None):
    s = hashlib.sha1()
    s.update("httk\0")
    if prepend != None:
        s.update(prepend)
        s.update("\0")
    s.update(data)
    s.update("\0%u\0" % len(data))
    return s.hexdigest()

def tuple_to_hexhash(t):
    return hexhash_str(tuple_to_str(t))

def hexhash_ioa(ioa,prepend=None):
    def chunks(f, size=8192): 
        while True: 
            s = f.read(size) 
            if not s: break 
            yield s     
    ioa = IoAdapterFileReader.use(ioa)
    f = ioa.file
    s = hashlib.sha1() 
    size = 0
    s.update("httk\0")
    if prepend != None:
        s.update("\0")
        s.update(prepend)
    for chunk in chunks(f): 
        size += len(chunk)
        s.update(chunk) 
    ioa.close()
    s.update("\0%u\0" % size)
    return s.hexdigest() 

def generate_manifest_for_files(codename,codever, basedir, filenames,fakenames=None,skip_filenames=False):
    hash_manifest=""
    for i in range(len(filenames)):
        f = filenames[i]
        if skip_filenames:
            hash_manifest += hexhash_ioa(f)+"\n"
        else:
            if fakenames != None and fakenames[i] != None:
                relpath = fakenames[i]
            else:
                common_prefix = os.path.commonprefix([basedir, f])
                if common_prefix == '':
                    relpath = f
                else:
                    relpath = os.path.relpath(f, common_prefix)
            hash_manifest += relpath+" "+hexhash_ioa(f)+"\n"
    hash_hex = hexhash_str(hash_manifest,prepend=codename+" "+codever)
    return (hash_manifest,hash_hex)

def generate_manifest_for_dir(codename,codever, basedir, excludes=None):
    raise Exception("generate_manifest_for_dir: Not implemented, sorry")

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
      