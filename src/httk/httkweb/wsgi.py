#!/usr/bin/env python
#
# Copyright 2019-2023 Rickard Armiento
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

import time, codecs, traceback, sys, io

try:
    from urllib.parse import parse_qsl, urlunsplit
except ImportError:
    from urlparse import parse_qsl, urlunsplit

from httk.httkweb.webserver import WebError

from httk.core import parse_header, parse_multipart, cgitb_html

class BytesIOWrapper:

    def __init__(self, iterable, encoding):
        self.iterable = iterable
        self.encoding = encoding

    def __iter__(self):
        it = iter(self.iterable)
        line = next(it)
        try:
            if isinstance(line, str):
                while True:
                    yield codecs.encode(line, self.encoding)
                    line = next(it)
            else:
                while True:
                    yield line
                    line = next(it)
        except StopIteration:
            pass



class WsgiApplication:

    def __init__(self, app_callback, debug=False):

        self.app_callback = app_callback
        self.debug = debug

    def __call__(self, environ, start_response):

        starttime_wsgi_request = time.time()

        request = self.wsgi_get_request(environ)

        if request['relpath'] == '' or request['relpath'] == '/':
            request['relpath'] = 'index.html'

        try:
            out = self.app_callback(request)

        except WebError as e:
            start_response(e.response_code, [('Content-Type',e.content_type)])
            return self.output(e.content,e.encoding)

        except FileNotFoundError as e:
            start_response('404 Not found', [('Content-Type','text/html')])
            if self.debug:
                return self.output("<html><body>Requested URL not found. Reason given: "+str(e)+"</body></html>")
            else:
                return self.output("<html><body>Requested URL not found.</body></html>")

        except Exception as e:
            start_response('500 Internal error',[('Content-Type','text/html')])
            # OSErrors don't work in cgitb as it tries to access characters_written
            traceback.print_exc()
            if self.debug and not isinstance(e,OSError):
                error_html = cgitb.html(sys.exc_info())
                return self.output(error_html)
            else:
                return self.output("<html><body>An unexpected server error has occured.</body></html>")

        print("WSGI request "+request['relpath']+" handled in: {:.6f} sec".format(time.time() - starttime_wsgi_request))

        start_response('200 OK', [('Content-Type',out['content_type'])])
        return self.output(out['content'],out['encoding'])

    def output(self, content, encoding = 'utf-8'):
        #if isinstance(content,io.StringIO):
        #    return BytesIOWrapper(content, encoding)
        #3elif :
        if hasattr(content, '__iter__') and not isinstance(content, str):
            return BytesIOWrapper(content, encoding)
        else:
            return [codecs.encode(content,encoding)]

    def wsgi_get_request(self, environ):

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
        if request['relpath'].startswith('/'):
            request['relpath'] = request['relpath'][1:]

        request['querystr'] = environ['QUERY_STRING']

        request['representation'] = urlunsplit(('', '', request['relpath'], request['querystr'], ''))
        request['url'] = urlunsplit((request['scheme'], request['netloc'], request['relpath'], request['querystr'], ''))

        return request

