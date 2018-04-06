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

import sys, os, subprocess, datetime
from .config import httk_dir, config

default_copyright_end_year = 2018

httk_version = None
if (not config.getboolean('general', 'bypass_git_version_lookup')) and os.path.exists(os.path.join(httk_dir,'.git')):
    try:
        httk_version = subprocess.check_output(["git", "describe","--dirty","--always"]).strip()
        git_commit_datetime = datetime.datetime.fromtimestamp(int(subprocess.check_output(["git", "log","-1",'--format=%ct'])))
        httk_version_date = str(git_commit_datetime.year)+ "-" + str(git_commit_datetime.month)+ "-" + str(git_commit_datetime.day)
        httk_copyright_note = "(c) 2012 - " + str(git_commit_datetime.year)
    except Exception as e:
        sys.stderr.write("Note: failed to obtain httk version from git: " + str(e) + "\n")

    # Read and check that if VERSION file is already correct before overwriting it, in case
    # httk is on a read-only file system, or writes are slow.
    old_version = None
    f = None
    try:
        f = open(os.path.join(httk_dir,'VERSION'),"r")
        old_version = f.read().strip()
    except Exception:
        pass
    finally:
        if f is not None:
            f.close()
        
    if httk_version != None and old_version != httk_version:
        try:
            f = open(os.path.join(httk_dir,'VERSION'),"w")
            f.write(httk_version)
            sys.stderr.write("Note: updated httk VERSION file to:" + httk_version + "\n")
        except Exception as e:
            raise Exception("httk VERSION file is missing or not updated, and the attempt to updated it failed: " + str(e))
        finally:
            if f is not None:
                f.close()
        
if httk_version == None:
    try:
        from .version_string import version, copyright_note
        httk_version = version
        httk_copyright_note = copyright_note
    except Exception as e:
        sys.stderr.write("Note: failed to obtain httk version from httk/version_string.py: "+str(e)+"\n")
        httk_version = 'unknown'
        httk_copyright_note = "(c) 2012 - " + default_copyright_end_year
