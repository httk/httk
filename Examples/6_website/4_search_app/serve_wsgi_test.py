#!/usr/bin/env python3

'''
This uses Python's build-in WSGI-server meant for testing.
To use WSGI in production, plese see 'serve.wsgi'.
'''

from httk.httkweb import serve
from httk.httkweb import create_wsgi_application
from wsgiref.simple_server import make_server, WSGIRequestHandler

class StdoutLoggingWSGIRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        print(format % args)

application = create_wsgi_application("src", port=8080)
srv = make_server('localhost', 8080, application, handler_class=StdoutLoggingWSGIRequestHandler)
srv.serve_forever()
