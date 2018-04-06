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
Reads the file httk.cfg in the root of the httk tree and the user's .httk.cfg.
If none of them is found it uses the httk.cfg.default.
"""

import sys
import os.path
import inspect

try:
    # Python 2
    import ConfigParser as configparser
except ImportError:
    # Python 3
    import configparser

_realpath = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))

config = configparser.ConfigParser()
config_files = []

global_cfgpathstr = os.path.expanduser('~/.httk.cfg')
if os.path.exists(global_cfgpathstr):
    config_files.append(global_cfgpathstr)

local_cfgpathstr = os.path.join(_realpath, '..', 'httk.cfg')
if os.path.exists(local_cfgpathstr):
    config_files.append(local_cfgpathstr)

if config_files:
    config.read(config_files)
else:
    sys.stderr.write("Warning: no httk.cfg found. Using httk.cfg.default settings.\n")
    config.read(os.path.join(_realpath, '..', 'httk.cfg.default'))


#: The path to the main httk directory
httk_dir = os.path.join(_realpath, '..')





