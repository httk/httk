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

# TODO: This should be replaced with json schema validation when we have a proper schema for the json output
from httk.optimade.validation.response import validate_response
from httk.optimade.validation.request import request, RequestError

def validate_single_entry_request(base_url, relurl='/structures'):
    result = {'error':[], 'warning':[], 'note':[]}

    try:
        output = request(base_url+relurl)
        json = output['response']
        
        if json is None:
            result['error'] += [{'description':'output is null'}]
            return result
        
        if 'data' not in json:
            result['error'] += [{'description':'missing data member'}]
        else:
            data = json['data']
            # It is unclear in the specification if data has to be a list
            if isinstance(data, list):
                if not len(data)>0:
                    result['error'] += [{'description':'no data returned'}]
                data = data[-1]

                if 'id' not in data:
                    result['error'] += [{'description':'data->id missing'}]
                else:
                    lastid = data['id']
                    if not isinstance(lastid,str):
                        result['error'] += [{'description':'data->id is not a string'}]
                    single_entry_result = request(base_url+relurl+"/"+data['id'])
                    return validate_response(single_entry_result['response'])              
                    
        return result
    
    except RequestError as e:
        return {'error':str(e), 'warning':[], 'note':[]}
        


if __name__ == '__main__':
    import pprint
    
    #pprint.pprint(validate_base_info_request("http://localhost:8080"))
