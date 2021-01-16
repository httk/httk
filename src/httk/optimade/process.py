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

from __future__ import print_function

from pprint import pprint

from httk.optimade.validate import validate_optimade_request
from httk.optimade.info_endpoint import generate_info_endpoint_reply, generate_entry_info_endpoint_reply, generate_base_endpoint_reply, generate_versions_endpoint_reply, generate_links_endpoint_reply
from httk.optimade.entry_endpoint import generate_entry_endpoint_reply, generate_single_entry_endpoint_reply
from httk.optimade.httk_entries import default_response_fields, required_response_fields, httk_all_entries, httk_valid_response_fields
from httk.optimade.error import OptimadeError, TranslatorError
from httk.optimade.parse_optimade_filter import ParserSyntaxError, parse_optimade_filter

def process(request, query_function, version, config, debug=False):
    """
    Process an optimade query.

    Args:
      request: a dict with these entries:
                   baseurl (required): the base url that serves the OPTIMaDe API.
                   representation (mandatory): the string with the part of the URL that follows the base URL. This must always be provided, because
                        the OPTIMaDe specification requires this to be part of the output in the meta section (meta -> query -> representation).
                   relurl (optional): the part of the URL that follows the base URL but without query parameters.
                        Include this if the web-serving framework provides this, i.e., if it splits off the query part for you.
                   endpoint (optional): the endpoint being requested
                   request_id (optional): a specific entry id being requested.
                   querystr (optional): a string that defines the query parameters that follows the base URL and the relurl and a single '?'.
                   query (optional): a dictionary representation of the query part of the URL.
          missing information is derived from the 'representation' string.

      query_function: a callback function of signature
                         query_function(entries, response_fields, response_limit, filter_ast, debug)
                      with:
                         entries: list of optimade entries to run the query for, usually just the entry type requested by the end point.
                         response_fields: which fields should be present in the output
                         response_limit: the maximum number of results to return
                         filter_ast: an abstract syntax tree representing the optimade filter requested
                         debug: if set to true, print debug information to stdout.
                      returns an OptimadeResults object.

    """

    if debug:
        print("==== OPTIMADE REQUEST FOR:", request['representation'])

    validated_request = validate_optimade_request(request, version)
    baseurl = validated_request['baseurl']
    endpoint = validated_request['endpoint']
    request_id = validated_request['request_id']
    version = validated_request['version']
    validated_parameters = validated_request['query']

    if debug:
        print("==== VALIDATED ENDPOINT, REQUEST_ID, AND PARAMETERS:")
        print("ENDPOINT:", endpoint)
        print("REQUEST_ID:", request_id)
        pprint(validated_parameters)
        print("====")

    if endpoint == '':
        response = generate_base_endpoint_reply(validated_request, config)
        return {'content': response, 'content_type':'text/html', 'response_code':200, 'response_msg':'OK', 'encoding':'utf-8'}

    elif endpoint == 'versions':
        response = generate_versions_endpoint_reply(validated_request, config)
        return {'content': response, 'content_type':'text/csv; header=present', 'response_code':200, 'response_msg':'OK', 'encoding':'utf-8'}

    elif endpoint == 'links':
        response = generate_links_endpoint_reply(validated_request, config)

    elif endpoint == 'info':
        response = generate_info_endpoint_reply(validated_request, config)

    elif endpoint in httk_all_entries:

        response_fields = validated_request['recognized_response_fields']
        unknown_response_fields = validated_request['unrecognized_response_fields']
        entries = [endpoint]

        if response_fields is None:
            response_fields = default_response_fields[endpoint]

        for response_field in required_response_fields[endpoint]:
            if response_field not in response_fields:
                response_fields += [response_field]

        input_string = None
        filter_ast = None
        if request_id is not None:
            input_string = 'filter=id="'+request_id+'"'
            filter_ast = ('=', ('Identifier', 'id'), ('String', request_id))
        elif 'filter' in validated_parameters:
            input_string = validated_parameters['filter']

        if input_string is not None:
            if filter_ast is None:
                try:
                    filter_ast = parse_optimade_filter(input_string)
                except ParserSyntaxError as e:
                    raise OptimadeError(str(e), 400, "Bad request")

            if debug:
                print("==== FILTER STRING PARSE RESULT:")
                pprint(filter_ast)
                print("====")

            try:
                results = query_function(entries, response_fields, unknown_response_fields, validated_parameters['page_limit'], validated_parameters['page_offset'], filter_ast, debug=debug)
            except TranslatorError as e:
                raise OptimadeError(str(e), e.response_code, e.response_msg)

        else:
            results = query_function(entries, response_fields, unknown_response_fields, validated_parameters['page_limit'], validated_parameters['page_offset'], debug=debug)

        if request_id is not None:
            response = generate_single_entry_endpoint_reply(validated_request, config, results)
        else:
            response = generate_entry_endpoint_reply(validated_request, config, results)

        if debug:
            print("==== END RESULT")
            pprint(response)
            print("===============")

    elif endpoint.startswith("info/"):
        info, _sep, base = endpoint.partition("/")
        assert(info == "info")
        if base in httk_all_entries:
            response = generate_entry_info_endpoint_reply(validated_request, config, base)
        else:
            raise OptimadeError("Internal error: unexpected endpoint.", 500, "Internal server error")

    else:
        raise OptimadeError("Internal error: unexpected endpoint.", 500, "Internal server error")

    return {'json_response': response, 'content_type':'application/vnd.api+json', 'response_code':200, 'response_msg':'OK', 'encoding':'utf-8'}
