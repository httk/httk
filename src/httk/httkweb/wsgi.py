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
from __future__ import print_function

import cgi

try:
    from urllib.parse import parse_qsl, urlunsplit
except ImportError:
    from urlparse import parse_qsl, urlunsplit


def wsgi_get_request(environ):

    request = {}

    request['headers'] = dict((x[5:].lower(), environ[x]) for x in environ if x.startswith("HTTP_"))

    if 'REQUEST_METHOD' not in environ:
        return {}

    query = {}
    if 'QUERY_STRING' in environ:
        query = dict(parse_qsl(environ['QUERY_STRING'], keep_blank_values=True))
    request['query'] = query

    postvars = {}        
    if environ['REQUEST_METHOD'].upper() == 'POST':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            request_body_size = 0
        request_body = environ['wsgi.input'].read(request_body_size)        
        content_type_header = environ.get('CONTENT_TYPE', 'application/x-www-form-urlencoded')
        ctype, pdict = cgi.parse_header(content_type_header)
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(request_body, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            postvars = dict(parse_qsl(request_body, keep_blank_values=True))

    request['postvars'] = postvars

    request['scheme'] = environ['wsgi.url_scheme']

    if environ.get('HTTP_HOST'):
        request['netloc'] = environ['HTTP_HOST']
    else:
        request['netloc'] = environ['SERVER_NAME']

        if environ['wsgi.url_scheme'] == 'https':
            if environ['SERVER_PORT'] != '443':
                request['netloc'] += ':' + environ['SERVER_PORT']
        else:
            if environ['SERVER_PORT'] != '80':
                request['netloc'] += ':' + environ['SERVER_PORT']

    request['baseurl'] = urlunsplit((request['scheme'], request['netloc'], environ.get('SCRIPT_NAME', ''), '', ''))
    request['relpath'] = environ['PATH_INFO']

    request['querystr'] = environ['QUERY_STRING']

    request['representation'] = urlunsplit(('', '', request['relpath'], request['querystr'], ''))
    request['url'] = urlunsplit((request['scheme'], request['netloc'], request['relpath'], request['querystr'], ''))

    return request

#def wsgi_get_relpath(environ):
#    if 'PATH_INFO' in environ:
#        return environ['PATH_INFO']
#    else:
#        return ''


#def wsgi_get_headers(environ):
#    return dict((x[5:], environ[x]) for x in environ if x.startswith("_HTTP_"))


#def wsgi_get_query(environ):
#
#    if 'REQUEST_METHOD' not in environ:
#        return {}
#
#    if environ['REQUEST_METHOD'].upper() == 'GET':    
#        if 'QUERY_STRING' in environ:
#            query = dict(parse_qsl(environ['QUERY_STRING'], keep_blank_values=True))
#            return query
#        else:
#            return {}
#
#    if environ['REQUEST_METHOD'].upper() == 'POST':
#        try:
#            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
#        except ValueError:
#            request_body_size = 0
#        request_body = environ['wsgi.input'].read(request_body_size)        
#        content_type_header = environ.get('CONTENT_TYPE', 'application/x-www-form-urlencoded')
#        ctype, pdict = cgi.parse_header(content_type_header)
#        if ctype == 'multipart/form-data':
#            postvars = cgi.parse_multipart(request_body, pdict)
#        elif ctype == 'application/x-www-form-urlencoded':
#            postvars = dict(parse_qsl(request_body, keep_blank_values=True))
#        else:
#            postvars = {}
#
#        return postvars
#
#    return {}

