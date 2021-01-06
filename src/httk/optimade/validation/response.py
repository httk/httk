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

def validate_response(json, expect_error=False):

    result = {'error':[], 'warning':[], 'note':[]}

    allowed = {'errors', 'links', 'meta', 'data', 'include'}
    allowed_links = {'next','base_url'}
    allowed_meta = {'query', 'api_version', 'time_stamp', 'data_returned', 'more_data_available', 'data_available', 'last_id', 'response_message'}

    if json is None:
        result['error'] += [{'description':'output is null'}]
        return result
        
    # ERROR section
    if 'errors' in json and not expect_error:        
        result['note'] += [{'description':'unexpected error member in response to base_info'}]

    if 'errors' not in json and expect_error:        
        result['note'] += [{'description':'missing expected error member in response to base_info'}]

    if expect_error:
        return

    # LINKS SECTION
    if 'links' not in json:
        result['error'] += [{'error':'response to base_info missing links member'}]
    else:
        links = json['links']
        if 'base_url' not in links:
            result['note'] += [{'description':'links member missing base_url'}]
            
        remaining_links = {key: links[key] for key in links if ((key not in allowed_links) and (key[0] != '_'))}
        if len(remaining_links) > 0:
            result['error'] += [{'description':'links memeber contains unallowed keys'}]        

            
    # META SECTION            
    if 'meta' not in json:
        result['error'] += [{'error':'response to base_info missing meta member'}]
    else:
        meta = json['meta']
        if 'query' not in meta:
            result['error'] += [{'description':'meta member missing query member'}]
        else:
            if 'representation' not in meta['query']:
                result['error'] += [{'description':'meta -> query member missing representation member'}]
            
        if 'api_version' not in meta:
            result['error'] += [{'description':'meta member is missing api_version member'}]
        elif meta['api_version'] != '0.9.5':
                result['error'] += [{'description':'meta->api_version is not 0.9.5'}]
                
        if 'time_stamp' not in meta:
            result['error'] += [{'description':'meta member is missing api_version member'}]
        else:
            pass
            # TODO Add validation of ISO 8601

        if 'data_returned' not in meta:
            result['error'] += [{'description':'meta member is missing data_returned member'}]
        elif not isinstance(meta['data_returned'], int):
            result['error'] += [{'description':'meta->data_returned is not integer'}]

        if 'more_data_available' not in meta:
            result['error'] += [{'description':'meta member is missing more_data_available member'}]
        elif not isinstance(meta['more_data_available'], bool):
            result['error'] += [{'description':'meta->data_returned is not bool'}]

        remaining_meta = {key: meta[key] for key in meta if ((key not in allowed_meta) and (key[0] != '_'))}
        if len(remaining_meta) > 0:
            result['error'] += [{'description':'meta memeber contains unallowed keys'}]        
            
    if 'include' in json:
        include = json['include']
        if not isinstance(meta['data_returned'], list):
            result['error'] += [{'description':'include member is not a list'}]

    remaining = {key: json[key] for key in json if ((key not in allowed) and (key[0] != '_'))}
    if len(remaining) > 0:
        result['error'] += [{'description':'response contains unallowed keys'}]

    return result

def validate_response_request(base_url, relurl):
    try:
        result = request(base_url+relurl)
        return validate_response(result['response'])
    except RequestError as e:
        return {'error':str(e), 'warning':[], 'note':[]}
            
