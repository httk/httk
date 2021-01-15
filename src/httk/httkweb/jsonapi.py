#!/usr/bin/env python
#
# Copyright 2019 Rickard Armiento
#
# This file is part of a Python candidate reference implementation of
# the optimade API [https://www.optimade.org/]
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json

from httk.httkweb.webserver import WebError

_jsonapi_response_codes = {
    '200': 'OK',
    '201': 'Created',
    '202': 'Accepted',
    '204': 'No Content',
    '403': 'Forbidden',
    '400': 'Bad Request',
    '404': 'Not Found',
    '406': 'Not Acceptable',
    '409': 'Conflict',
    '415': 'Unsupported Media Type',
    '500': 'Internal Server Error'
}


class JsonapiError(WebError):
    def __init__(self, message, response_code, response_msg=None, longmsg=None, idstr=None, links=None, code=None, source=None, meta=None, indent=True):

        self.content = longmsg if longmsg is not None else message
        self.response_code = response_code
        self.content_type = 'application/vnd.api+json'
        self.response_msg = response_msg if response_msg is not None else _jsonapi_response_codes[str(response_code)]
        self.id = idstr
        self.links = links
        self.code = code
        self.source = source
        self.meta = meta
        self.indent = indent

        errordata = {}

        if idstr is not None:
            errordata['id'] = idstr

        if code is not None:
            errordata['code'] = code

        if source is not None:
            errordata['source'] = source            

        if meta is not None:
            errordata['meta'] = meta

        errordata['status'] = str(response_code)
        errordata['title'] = str(self.response_msg)
        errordata['detail'] = str(self.content)

        self.content_json = {'errors': errordata}

        if indent:
            message = json.dumps(self.content_json, indent=4, separators=(',', ': '), sort_keys=True)
        else:
            message = json.dumps(self.content_json, separators=(',', ': '), sort_keys=True)

        super(JsonapiError, self).__init__(message, response_code, response_msg, longmsg, self.content_type)


def check_jsonapi_header_requirements(headers):
    # Handle jsonapi MUSTs with regards to headers
    if 'Content-Type' in headers:
        _media_type, _sep, parameter = headers['Content-Type'].partition(";")
        if parameter.strip() != '':
            raise WebError("Requested content-type violates jsonapi requirements.", 415, "Unsupported Media Type")
               
    # The following implments my interpretation of the combination of RFC2616
    # and the jsonapi 1.0 specification:
    #
    # - The jsonapi 1.0 spec states that the request MUST be rejected with 406 Not Acceptable
    #   only if ALL these apply:
    #      (a) There is an Accept header
    #      (b) The Accept header explicitly specifies 'application/vnd.api+json' PLUS media parameters
    #      (c) The Accept header does NOT specify 'application/vnd.api+json' WITHOUT media parameters
    #
    # - RFC2616 specifies that if there is an Accept header and the server cannot send a response
    #   which is acceptable according to the combined Accept field value, then the server SHOULD
    #   reject the request with a 406 Not Acceptable.
    #
    #   Hence, if we get an Accept header with no 'application/vnd.api+json', then we accept
    #   the wildcards '*/*' and 'application/*'. BUT, if 'application/vnd.api+json' + media parameters
    #   occur anywhere, we DON'T accept those wildcards.
    # 
    # To reject the wildcards does seem to violate the sprit of the Accept header, but the json 1.0 spec
    # seems pretty set in its formulation with no exception for wildcards. I cannot, however, really
    # forsee a realistic scenario where this actually causes any trouble.
    #
        
    if 'accept' in headers:
        accepts = [x.strip() for x in headers['accept'].split(',')]
        may_accept_media_range = True
        media_range_encountered = False
        for accept in accepts:
            if accept == 'application/vnd.api+json':                
                break
            if accept.split(";")[0] == 'application/vnd.api+json':
                may_accept_media_range = False
            if accept.split(";")[0] == '*/*' or accept.split(";")[0] == 'application/*':
                media_range_encountered = True
        else:
            if not (may_accept_media_range and media_range_encountered):
                raise WebError("Accept header violates jsonapi requirements.", 406, "Not Acceptable")

