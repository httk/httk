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
    from urllib.parse import parse_qsl, urlparse
except ImportError:
    from urlparse import parse_qsl, urlparse

from .httk_entries import httk_all_entries, httk_valid_endpoints, httk_valid_response_fields
from .error import OptimadeError
from .versions import optimade_supported_versions, optimade_default_version


def _validate_query(endpoint, query):
    validated_parameters = {'page_limit': 50, 'page_offset': 0, 'response_fields': None}

    if ('response_format' in query and query['response_format'] is not None) and query['response_format'] != 'json':
        raise OptimadeError("Requested response_format not supported.", 400, "Bad request")
    else:
        validated_parameters['response_format'] = 'json'

    if 'page_limit' in query and query['page_limit'] is not None:
        try:
            validated_parameters['page_limit'] = int(query['page_limit'])
        except ValueError:
            raise OptimadeError("Cannot interprete page_limit.", 400, "Bad request")
        if validated_parameters['page_limit'] > 50:
            validated_parameters['page_limit'] = 50

    if 'page_offset' in query and query['page_offset'] is not None:
        try:
            validated_parameters['page_offset'] = int(query['page_offset'])
        except ValueError:
            raise OptimadeError("Cannot interprete page_offset.", 400, "Bad request")
        if validated_parameters['page_offset'] < 0:
            validated_parameters['page_offset'] = 0

    if 'response_fields' in query and query['response_fields'] is not None:
        response_fields = [x.strip() for x in query['response_fields'].split(",")]
        for response_field in response_fields:
            if response_field in httk_valid_response_fields[endpoint]:
                validated_parameters['response_fields'] += [httk_valid_response_fields[endpoint][httk_valid_response_fields[endpoint].index(response_field)]]

    # Validating the filter string is deferred to its parser
    if 'filter' in query and query['filter'] is not None:
        validated_parameters['filter'] = query['filter']

    return validated_parameters


def validate_optimade_request(request, version):
    validated_request = {'baseurl': request['baseurl'], 'representation': request['representation'], 'endpoint': None, 'version': optimade_default_version, 'request_id': None, 'query': None}

    if 'endpoint' in request:
        validated_request['endpoint'] = request['endpoint']
    if 'request_id' in request:
        validated_request['request_id'] = request['request_id']
    if 'version' in request:
        validated_request['version'] = request['version']

    if validated_request['endpoint'] is None:
        if 'relurl' in request:
            relurl = request['relurl']
        else:
            relurl = request['representation'].partition('?')[0]

        endpoint = relurl.strip("/")

        potential_optimade_version, _sep, rest = endpoint.partition('/')

        if len(potential_optimade_version) > 2 and potential_optimade_version[0] == 'v' and potential_optimade_version[1] in "0123456789":
            if potential_optimade_version in optimade_supported_versions:
                validated_request['version'] = optimade_supported_versions[potential_optimade_version]
                endpoint = rest
            else:
                raise OptimadeError("Unsupported version requested. Supported versioned base URLs are: "+(", ".join(["/"+str(x) for x in optimade_supported_versions.keys()])), 553, "Bad request")

        if endpoint in httk_valid_endpoints:
            # Defensive programming; don't trust '=='/in to be byte-for-byte equivalent,
            # so don't use the insecure string from the user
            validated_request['endpoint'] = httk_valid_endpoints[httk_valid_endpoints.index(endpoint)]
        else:
            endpoint, _sep, request_id = endpoint.rpartition('/')
            if endpoint in httk_all_entries:
                # Defensive programming; don't trust '=='/in to be byte-for-byte equivalent,
                # so don't use the insecure string from the user
                validated_request['endpoint'] = httk_valid_endpoints[httk_valid_endpoints.index(endpoint)]
                # Only allow printable ascii characters in id; this is not in the standard, but your
                # database really should adhere to it or you are doing weird things.
                if all(ord(c) >= 32 and ord(c) <= 126 for c in request_id):
                    validated_request['request_id'] = request_id
                else:
                    raise OptimadeError("Unexpected characters in entry id.", 400, "Bad request")

        if validated_request['endpoint'] is None:
            raise OptimadeError("Request for invalid endpoint.", 400, "Bad request")

    if 'query' in request:
        query = request['query']
    else:
        if 'querystr' in request:
            querystr = query['querystr']
        else:
            querystr = urlparse(request['representation'])['query']
        query = dict(parse_qsl(querystr, keep_blank_values=True))

    validated_request['query'] = _validate_query(validated_request['endpoint'], query)

    if validated_request['version'] != version:
        raise Exception("validate_optimade_request: unexpected version")

    return validated_request




def determine_optimade_version(request):

    if 'relurl' in request:
        relurl = request['relurl']
    else:
        relurl = request['representation'].partition('?')[0]

    endpoint = relurl.strip("/")

    potential_optimade_version, _sep, rest = endpoint.partition('/')

    if len(potential_optimade_version) > 2 and potential_optimade_version[0] == 'v' and potential_optimade_version[1] in "0123456789":
        if potential_optimade_version in optimade_supported_versions:
            return optimade_supported_versions[potential_optimade_version]
        else:
            raise OptimadeError("Unsupported version requested. Supported versioned base URLs are: "+(", ".join(["/"+str(x) for x in optimade_supported_versions.keys()])), 553, "Version Not Supported")

    else:
        return optimade_default_version
