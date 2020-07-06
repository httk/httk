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

import sys, collections, queue, bz2

unicode_type = str

# Exception backtrace is automatically saved in e.__backtrace__ in Python 3
def preserve_exception_backtrace(e):
    return e

def reraise_from(exc_cls, message, from_exc):
    raise exc_cls(message) from from_exc

def print_(*args,**kwargs):
    print(*args,**kwargs)

def is_sequence(l):
    return isinstance(l, collections.Iterable) and not isinstance(l, str)
    #return (not hasattr(arg, "strip") and hasattr(arg, "__getitem__") or
    #        (hasattr(arg, "__iter__") and not isinstance(arg, str)))

def is_string(s):
    return isinstance(s, str)

# In Python 3 bz2 files are opened by default in binary mode.
# This is an attempt at making bz2 files behave as ordinary files. 
# If mode does not contain 'b' we add 't' for text mode,
# and open the file with the bz2.open() function (only in Python 3.3)
def bz2open(filename, mode, *args):
    if not 'b' in mode and not 't' in mode:
        mode += 't'

    if sys.version_info >= (3, 3):
        return bz2.open(filename, mode, *args)
        
    elif not 'b' in mode: 
        return io.TextIOWrapper(bz2.BZ2File(filename, mode, *args), encoding='utf-8')
    else:
        return bz2.BZ2File(filename, mode, *args)

            
