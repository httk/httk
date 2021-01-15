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

def validate_base_info(json):

    result = validate_response(json)

    if json is None:
        # Error for this is handled by validate_response
        return result

    allowed_data = {'type', 'id', 'attributes'}
    # Note: specification bug: specification shows in the example available_endpoints, but it isn't allowed according to the spec
    allowed_attributes = {'api_version','available_api_versions','formats','entry_types_by_format','available_endpoints'}
    
    # No neet to return errors if these are missing, since validate_response handles that
    if 'meta' in json:
        if 'data_returned' in json['meta']:
            if json['meta']['data_returned'] != 0:
                result['error'] += [{'description':'meta->data_returned is not zero'}]

    if 'data' not in json:
        result['error'] += [{'description':'missing data member'}]
    else:
        data = json['data']
        # It is unclear in the specification if data has to be a list
        if isinstance(data, list):
            if len(data)!=1:
                result['error'] += [{'description':'data is a list, but the length is not = 1'}]
            data = data[0]
            
        if not isinstance(data, dict):
            result['error'] += [{'description':'data is not either a dict, or, a list with one dict'}]
        else:
            if 'type' not in data:
                result['error'] += [{'description':'missing data->type member'}]
            else:
                if data['type'] != "info":
                    result['error'] += [{'description':'data->type is not info, it is:'+str(data)}]

            if 'id' not in data:
                result['error'] += [{'description':'missing data->id member'}]
            else:
                if data['id'] != "/":
                    result['error'] += [{'description':'data->id is not "/"'}]

            if 'attributes' not in data:
                result['error'] += [{'description':'missing data->attributes member'}]
            else:
                attributes=data['attributes']
                if 'api_version' not in attributes:
                    result['error'] += [{'description':'missing data->attributes->api_version member'}]
                elif attributes['api_version'] != 'v0.9.5':
                    result['error'] += [{'description':'data->attributes->api_version is not "v0.9.5"'}]

                remaining_attributes = {key: attributes[key] for key in attributes if ((key not in allowed_attributes) and (key[0] != '_'))}
                if len(remaining_attributes) > 0:
                    result['error'] += [{'description':'data->attributes contains unallowed keys: '+", ".join([str (x) for x in remaining_attributes])}]        

            if 'available_api_versions' not in attributes:
                result['error'] += [{'description':'missing data->attributes->available_api_versions'}]
            else:
                #TODO: Validate available_api_versions
                pass

            if 'formats' not in attributes:
                result['error'] += [{'description':'missing data->attributes->formats member'}]
            else:
                #TODO Validate formats
                pass

            if 'entry_types_by_format' not in attributes:
                result['error'] += [{'description':'missing data->attributes->entry_types_by_format member'}]
            else:
                #TODO Validate formats
                pass        

            remaining_data = {key: data[key] for key in data if ((key not in allowed_data) and (key[0] != '_'))}
            if len(remaining_data) > 0:
                result['error'] += [{'description':'data memeber contains unallowed keys'}]        
            
    return result


def validate_base_info_request(base_url, relurl='/info'):
    try:
        result = request(base_url+relurl)
        return validate_base_info(result['response'])
    except RequestError as e:
        return {'error':str(e), 'warning':[], 'note':[]}
        


if __name__ == '__main__':
    import pprint
    
    pprint.pprint(validate_base_info_request("http://localhost:8080"))
