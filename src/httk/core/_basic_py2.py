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

from __future__ import print_function

import sys, collections, traceback, bz2

import Queue as queue

unicode_type=unicode

def preserve_exception_backtrace(e):
    e.__backtrace_str__ =  traceback.format_exc()
    return e

def reraise_from(exc_cls, message, from_exc):

    try:
        old_backtrace_str = from_exc.__backtrace_str__
    except Exception:
        # If old backtrace isn't preserved, assume it is the latest triggered exception
        old_backtrace_str = traceback.format_exc()

    raise exc_cls("%s\n\nThe above exception was caused by the following exception:\n\n%s" % (message, old_backtrace_str))


def print_(*args,**kwargs):
    print(*args,**kwargs)

def is_sequence(l):
    return isinstance(l, collections.Iterable) and not isinstance(l, basestring)
    #return (not hasattr(arg, "strip") and hasattr(arg, "__getitem__") or
    #        (hasattr(arg, "__iter__") and not isinstance(arg, str)))

def is_string(s):
    return isinstance(s, basestring)

def bz2open(filename, mode, *args):
    return bz2.BZ2File(filename, mode, *args)
