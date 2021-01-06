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

from .request import request, RequestError

def validate_headers(base_url, relurl='/info'):
    result = {'error':[], 'warning':[], 'note':[]}

    try:
        output = request(base_url+relurl)
    except RequestError as e:
        result['error'] += [{'description':'Unexpected server error:'+str(e)}]
        return
        
    if 'Content-Type' not in output['headers']:
        result['error'] += [{'description':'Server response is missing header Content-Type'}]
    else:
        content_type = output['headers']['Content-Type']
        if content_type != 'application/vnd.api+json':
            result['error'] += [{'description':'Server response Content-Type header is not "application/vnd.api+json"'}]

    try:
        output = request(base_url+relurl,{'Accept':'Content-Type: application/vnd.api+json; unknown_media_type_parameter'})
        if output['code'] != 406:
            result['error'] += [{'description':'Server did not return 406 Not Acceptable for json api 1.0 violating Accept header'}]
    except RequestError as e:
        if e.code != 406:            
            result['error'] += [{'description':'Server did not return 406 Not Acceptable for json api 1.0 violating Accept header'}]
    
    return result
    


