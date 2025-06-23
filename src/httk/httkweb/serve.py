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

from httk.httkweb import helpers
from httk.httkweb.webgenerator import WebGenerator

def create_serve_callback(srcdir, port, baseurl, renderers, template_engines, function_handlers, debug, config, override_global_data):

    setup = helpers.setup(renderers, template_engines, function_handlers)

    if baseurl == None:
        if port == 80:
            baseurl="http://localhost/"
        else:
            baseurl="http://localhost:"+str(port)+"/"

    default_global_data = {'_use_urls_without_ext':True}

    global_data = helpers.read_config(srcdir, setup['renderers'], default_global_data, override_global_data, config)

    global_data['_baseurl'] = baseurl
    global_data['_basefunctionurl'] = baseurl
    if global_data['_use_urls_without_ext']:
        global_data['_functionext'] = ''
    else:
        global_data['_functionext'] = '.html'
    global_data['_render_mode'] = 'serve'

    webgenerator = WebGenerator(srcdir, global_data, **setup)

    def httk_web_callback(request):

        if request['relpath'] == '':
            request['relpath'] = 'index.html'

        out = webgenerator.retrieve(request['relpath'],request['query'])

        return {'response_code':200, 'content_type':out['mimetype'], 'content':out['content'], 'encoding':'utf-8' }
   
    return httk_web_callback

def serve(srcdir, port=80, baseurl = None, renderers = None, template_engines = None, function_handlers = None, debug=True, config = "config", override_global_data = None):
    from httk.httkweb import webserver

    callback = create_serve_callback(srcdir, port, baseurl, renderers, template_engines, function_handlers, debug, config, override_global_data)
    webserver.startup(callback, port=port, netloc=baseurl, debug=debug)

def create_wsgi_application(srcdir, port=80, baseurl = None, renderers = None, template_engines = None, function_handlers = None, debug=True, config = "config", override_global_data = None, generator=None):
    from httk.httkweb.wsgi import WsgiApplication

    callback = create_serve_callback(srcdir, port, baseurl, renderers, template_engines, function_handlers, debug, config, override_global_data)

    return WsgiApplication(callback, debug=debug)
