#!/usr/bin/env python
#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2018 Rickard Armiento
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
import os, sys, codecs, shutil, io, traceback, time

try:
    from urllib.parse import parse_qsl, urlsplit, urlunsplit
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    from urlparse import parse_qsl, urlsplit, urlunsplit
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from httk.core import parse_header, parse_multipart, cgitb_html

class WebError(Exception):
    def __init__(self, message, response_code, response_msg, longmsg=None, content_type='text/plain', encoding='utf-8'):
        super(WebError, self).__init__(message)
        self.content = longmsg if longmsg is not None else message
        self.response_code = response_code
        self.response_msg = response_msg
        self.content_type = content_type
        self.encoding = encoding


class _CallbackRequestHandler(BaseHTTPRequestHandler):

    get_callbacks = []
    post_callbacks = []
    error_callbacks = []
    debug = False
    netloc = 'http://localhost'
    basepath = '/'

    def get_debug_info(self):
        parsed_path = urlsplit(self.path)
        debug_info = {
            'CLIENT': {
                'client_address=%s (%s)' % (self.client_address,
                                            self.address_string()),
                'command=%s' % self.command,
                'path=%s' % self.path,
                'real path=%s' % parsed_path.path,
                'query=%s' % parsed_path.query,
                'request_version=%s' % self.request_version
            },
            'SERVER': {
                'server_version=%s' % self.server_version,
                'sys_version=%s' % self.sys_version,
                'protocol_version=%s' % self.protocol_version,
            }
        }
        return debug_info

    def wfile_write_encoded(self, s, encoding='utf-8'):
        if hasattr(s, 'read'):
            reader = codecs.getreader(encoding)
            # Wrapping the reader doesn't work in
            # Python 3 because of a bug (?)
            # that can be reproduced by the following short script:
            #
            # import encodings
            # import io
            # reader = encodings.utf_8.StreamReader(io.StringIO())
            # reader.read()
            #
            # => TypeError: can't concat str to bytes
            #
            # Hence, we wrap the writer instead
            writer = codecs.getwriter(encoding)
            if isinstance(s,io.StringIO):
                shutil.copyfileobj(s, writer(self.wfile))
            else:
                shutil.copyfileobj(s, self.wfile)
        else:
            self.wfile.write(codecs.encode(s, encoding))

    def do_GET(self):

        starttime_get_request = time.time()

        parsed_path = urlsplit(self.path)
        query = dict(parse_qsl(parsed_path.query, keep_blank_values=True))

        # Figure out what part of the URL is part of netloc and basepath used for hosting, and the rest (=representation)
        relpath = parsed_path.path
        if len(relpath)>0 and relpath[0] == '/':
            relpath = relpath[1:]

        basepath = self.basepath
        if basepath[0] == '/':
            basepath = basepath[1:]

        if not parsed_path.path.startswith(self.basepath):
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile_write_encoded("<html><body>Requested URL not found.</body></html>")
            return

        relpath = relpath[len(basepath):]
        representation = urlunsplit(('', '', relpath, parsed_path.query, ''))

        request = {'url': self.path,
                   'scheme': parsed_path.scheme,
                   'netloc': parsed_path.netloc,
                   'path': parsed_path.path,
                   'querystr': parsed_path.query,
                   'port': parsed_path.port,
                   'baseurl': self.netloc+self.basepath,
                   'representation': representation,
                   'relpath': relpath,
                   'query': query,
                   'postvars': {},
                   'headers': self.headers}

        try:
            for callback in self.get_callbacks:
                output = callback(request)
            self.send_response(output['response_code'])
            self.send_header('Content-type', output['content_type'])
            self.end_headers()
            self.wfile_write_encoded(output['content'], output['encoding'])

        except WebError as e:
            self.send_response(e.response_code, e.response_msg)
            self.send_header('Content-type', e.content_type)
            self.end_headers()
            self.wfile_write_encoded(e.content, e.encoding)

        except IOError as e:
            if len(self.error_callbacks) > 0:
                try:
                    for callback in self.error_callbacks:
                        output = callback(request,e)
                    self.send_response(output['response_code'])
                    self.send_header('Content-type', output['content_type'])
                    self.end_headers()
                    self.wfile_write_encoded(output['content'], output['encoding'])
                    return
                except Exception:
                    pass

            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile_write_encoded("<html><body>Requested URL not found.</body></html>")

        except Exception as e:
            if len(self.error_callbacks) > 0:
                try:
                    for callback in self.error_callbacks:
                        output = callback(request, e)
                    self.send_response(output['response_code'])
                    self.send_header('Content-type', output['content_type'])
                    self.end_headers()
                    self.wfile_write_encoded(output['content'], output['encoding'])
                    return
                except Exception as e2:
                    print("Exception while trying to handle exception when serving webserver response page:",str(e2))
                    raise

            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            if self.debug:
                self.wfile_write_encoded(cgitb_html(sys.exc_info()))
                traceback.print_exc()
            else:
                self.wfile_write_encoded("<html><body>An unexpected server error has occured.</body></html>")

        print("GET request "+self.path+" handled in: {:.6f} sec".format(time.time() - starttime_get_request))

    def do_POST(self):

        starttime_post_request = time.time()

        ctype, pdict = parse_header(self.headers['content-type'])
        if ctype == 'multipart/form-data':
            postvars = parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers['content-length'])
            postvars = dict(parse_qsl(self.rfile.read(length), keep_blank_values=True))
        else:
            postvars = {}

        parsed_path = urlsplit(self.path)
        query = dict(parse_qsl(parsed_path.query, keep_blank_values=True))

        # Figure out what part of the URL is part of netloc and basepath used for hosting, and the rest (=representation)
        relpath = parsed_path.path
        if len(relpath)>0 and relpath[0] == '/':
            relpath = relpath[1:]

        basepath = self.basepath
        if basepath[0] == '/':
            basepath = basepath[1:]

        if not parsed_path.path.startswith(self.basepath):
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile_write_encoded("<html><body>Requested URL not found.</body></html>")
            return

        relpath = relpath[len(basepath):]
        representation = urlunsplit(('', '', relpath, parsed_path.query, ''))

        request = {'url': self.path,
                   'scheme': parsed_path.scheme,
                   'netloc': parsed_path.netloc,
                   'path': parsed_path.path,
                   'querystr': parsed_path.query,
                   'port': parsed_path.port,
                   'baseurl': self.netloc+self.basepath,
                   'representation': representation,
                   'relpath': relpath,
                   'query': query,
                   'postvars': postvars,
                   'headers': self.headers}

        try:
            for callback in self.post_callbacks:
                output = callback(request)
            self.send_response(output['response_code'])
            self.send_header('Content-type', output['content_type'])
            self.end_headers()
            self.wfile_write_encoded(output['content'], output['encoding'])

        except WebError as e:
            self.send_response(e.response_code, e.response_msg)
            self.send_header('Content-type', e.content_type)
            self.end_headers()
            self.wfile_write_encoded(e.content, e.encoding)

        except Exception as e:
            if len(self.error_callbacks) > 0:
                try:
                    for callback in self.error_callbacks:
                        output = callback(request, e)
                    self.send_response(output['response_code'])
                    self.send_header('Content-type', output['content_type'])
                    self.end_headers()
                    self.wfile_write_encoded(output['content'], output['encoding'])
                    return
                except Exception:
                    pass

            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            if self.debug:
                self.wfile_write_encoded(cgitb_html(sys.exc_info()))
            else:
                self.wfile_write_encoded("<html><body>An unexpected server error has occured.</body></html>")

        print("POST request "+self.path+" handled in: {:.6f} sec".format(time.time() - starttime_get_request))

    # Redirect log messages to stdout instead of stderr
    def log_message(self, format, *args):
        print(format % args)


def startup(get_callback, post_callback=None, error_callback=None, port=80, netloc=None, basepath='/', debug=False):

    if post_callback is None:
        post_callback = get_callback

    if netloc is None:
        if port == 80:
            netloc = "http://localhost"
        else:
            netloc = "http://localhost:"+str(port)

    _CallbackRequestHandler.debug = debug
    _CallbackRequestHandler.netloc = netloc
    _CallbackRequestHandler.basepath = basepath
    _CallbackRequestHandler.get_callbacks += [get_callback]
    _CallbackRequestHandler.post_callbacks += [post_callback]
    if error_callback is not None:
        _CallbackRequestHandler.error_callbacks += [error_callback]

    server = None
    try:
        server = HTTPServer(('', port), _CallbackRequestHandler)
        print('Started httk webserver on port:', port)
        sys.stdout.flush()
        # Don't start serve_forever if we are inside automatic testing, etc.
        if "HTTK_DONT_HOLD" not in os.environ:
            server.serve_forever()

    except KeyboardInterrupt:
        print('Received keyboard interrupt, shutting down the httk web server')
        raise

    finally:
        if server is not None:
            server.socket.close()
            print('Server shutdown complete.')
