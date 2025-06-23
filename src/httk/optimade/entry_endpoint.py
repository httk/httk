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

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

import datetime

from httk.optimade.meta import generate_meta

def generate_entry_endpoint_reply(request, config, data):
    ndata_returned = data.count()
    data_part = []
    for d in data:
        attributes = dict(d)
        del attributes['id']
        del attributes['type']
        data_part += [{
            'attributes': attributes,
            'id': d['id'],
            'type': d['type'],
        }]

    if data.more_data_available:
        query = dict((k,v) for k,v in request['query'].items() if v is not None)
        query['page_offset'] = query['page_offset'] + len(data_part)
        links = { "next": request['baseurl']+request['endpoint']+"?"+urlencode(query) }
    else:
        links = { "next": None }

    response = {
        "links": links,
        "data": data_part,
        "meta": generate_meta(request, config, data_count=ndata_returned, more_data_available = data.more_data_available, data_available=config['data_available'][request['endpoint']])
    }

    # TODO: Add 'next' element in links for pagination, via info propagated in data
    #   Add "data_available" if available in data
    #   Fix more_data_available

    return response

def generate_single_entry_endpoint_reply(request, config, data):
    data_part = []
    for d in data:
        attributes = dict(d)
        del attributes['id']
        del attributes['type']
        data_part += [{
            'attributes': attributes,
            'id': d['id'],
            'type': d['type'],
        }]

    if len(data_part) > 1:
        raise Exception("Unexpectedly received a data object with lenth > 1 for a single entry endpoint repsonse")
    elif len(data_part) == 0:
        data_part = None
        ndata = 0
    else:
        data_part = data_part[0]
        ndata = 1

    if data.more_data_available:
        raise Exception("Unexpectedly received a data object with more data available for a single entry endpoint repsonse")

    response = {
        "links": { "next": None },
        "data": data_part,
        "meta": generate_meta(request, config, data_count=ndata, more_data_available = False, data_available=config['data_available'][request['endpoint']])
    }

    # TODO: Add 'next' element in links for pagination, via info propagated in data
    #   Add "data_available" if available in data
    #   Fix more_data_available

    return response
