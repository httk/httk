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

from numpy import *
import sys


class TrivialStore(object):

    """
    Very simple storage class that just stores everything into an individual dictionary, just like regular python objects work
    """

    def new(self, table, types, keyvals):
        d = dict(keyvals)
        d['sid'] = 0
        return d

    def retrieve(self, table, sid):
        raise Exception("TrivialStore.instance: You cannot load data from TrivialStore, sid must be = None.")
