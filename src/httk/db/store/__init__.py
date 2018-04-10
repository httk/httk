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
Stores are abstract keepers of data. The only one properly implemented right now is sqlite, but others are possible.
Trivialstore stores data just in the python classes, and dictstore stores all data in a dictionary.

TODO: Note: since a few changes back I think neither trivialstore or dictstore currently works the way they should.
"""

from httk.core import citation
citation.add_src_citation("httk_db", "Rickard Armiento")

from dictstore import DictStore
from sqlstore import SqlStore
