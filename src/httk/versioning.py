# -*- coding: utf-8 -*- 
# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2018 Rickard Armiento
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

_default_copyright_end_year = "2018"

import sys, os, subprocess, datetime
from .config import httk_root, config

sourcedir = os.path.dirname(os.path.realpath(__file__))

try:
    from .distdata import version, version_date, copyright_note
    httk_version = version
    httk_version_date = version_date
    httk_copyright_note = copyright_note

except ImportError:
    httk_version = None
    if (not config.getboolean('general', 'bypass_git_version_lookup')) and os.path.exists(os.path.join(httk_root,'.git')):
        try:
            httk_version = subprocess.check_output(["git", "describe","--dirty","--always"],cwd=sourcedir).strip()
            if httk_version.endswith('-dirty'):
                _git_commit_datetime = datetime.datetime.now()
            else:
                _git_commit_datetime = datetime.datetime.fromtimestamp(int(subprocess.check_output(["git", "log","-1",'--format=%ct'],cwd=sourcedir)))
            httk_version_date = "%d-%02d-%02d" % (_git_commit_datetime.year,_git_commit_datetime.month, _git_commit_datetime.day)
            httk_copyright_note = "(c) 2012 - " + str(_git_commit_datetime.year)

            # PEP 440 compliance
            httk_version = httk_version[1:]
            httk_version = httk_version.replace('-','.dev',1)
            httk_version = httk_version.replace('-','+',1)
            if httk_version.endswith('-dirty'):
                httk_version = httk_version.replace('-dirty','.d')
            
        except Exception as e:
            sys.stderr.write("Note: failed to obtain httk version from git: " + str(e) + "\n")
            httk_version = 'unknown'
            httk_version_date = 'unknown'
            httk_copyright_note = "(c) 2012 - " + _default_copyright_end_year
            
    else:
        httk_version = 'unknown'
        httk_version_date = 'unknown'
        httk_copyright_note = "(c) 2012 - " + _default_copyright_end_year

