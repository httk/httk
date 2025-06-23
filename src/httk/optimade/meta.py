#!/usr/bin/env python
#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2020 Rickard Armiento
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

import datetime

from httk import __version__ as httk_version
from httk.optimade.httk_entries import httk_entry_info, httk_all_entries
from httk.optimade.versions import optimade_supported_versions

def generate_meta(request, config, data_count=None, more_data_available=False, data_available = None):

    meta = {
        "query": {
            "representation": request['representation']
        },
        "api_version": request['version'],
        "time_stamp": datetime.datetime.now().isoformat(),
        #"data_returned": data_count, #TODO: find a way to implement this
        "more_data_available": more_data_available,
        "implementation": {
            "name": "httk",
            "version": httk_version,
            "homepage": "https://httk.org/",
        },
        "provider": config["provider"]
    }
    if data_count is not None:
        meta['data_returned'] = data_count
    if data_available is not None:
        meta['data_available'] = data_available
    return meta
