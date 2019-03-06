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

import SocketServer, shutil, os, urlparse, cgitb, sys
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

from templateengine_httk import TemplateEngineHttk
from templateengine_templator import TemplateEngineTemplator
from render_httk import RenderHttk
from render_rst import RenderRst
from functionhandler_httk import FunctionHandlerHttk

import generate
import render

def serve(srcdir, port=80, baseurl = None, renderers = None, template_engines = None, function_handlers = None, allow_urls_without_ext = True, debug=True, config = None, global_data = None):

    if baseurl == None:
        if port == 80:
            baseurl="http://localhost/"
        else:
            baseurl="http://localhost:"+str(port)+"/"

    given_global_data = global_data
    global_data = {}
        
    if renderers == None:
        renderers = {'httkweb': RenderHttk, 'rst': RenderRst}

    if template_engines == None:
        template_engines = {'httkweb.html': TemplateEngineHttk, 'templator.html': TemplateEngineTemplator}

    if function_handlers == None:
        function_handlers = {'py': FunctionHandlerHttk}
      
    # Read global config
    if isinstance(config,dict):
        global_data.update(config)
    else:
        if config is None:
            config = "config"
        try:
            identity = render.identify_page(srcdir, "", config,renderers,allow_urls_without_ext=True)   
            configdata = render.render_one_file(identity['absolute_filename'], identity['render_class'], {})['metadata']
            global_data.update(configdata)
        except IOError:
            if config == None:
                print "Warning: no site configuration provided, and no file exists in "+str(srcdir)+"/config.(something)"
            else:
                print "Could not find site configuration at "+str(srcdir)+"/"+str(config)+".(something)"

    if given_global_data is not None:
        global_data.update(given_global_data)

    urls_without_ext = 'urls_without_ext' in global_data and global_data['urls_without_ext'] in ['yes', 'true', 'y', True]     

    global_data['_baseurl'] = baseurl
    global_data['_basefunctionurl'] = baseurl
    if urls_without_ext:
        global_data['_functionext'] = ''
    else:
        global_data['_functionext'] = '.html'
    global_data['_render_mode'] = 'serve'    
    
    webgenerator = generate.WebGenerator(global_data, srcdir, renderers, template_engines, function_handlers, urls_without_ext=urls_without_ext, allow_urls_without_ext=allow_urls_without_ext)
    
    class Httk_http_handler(BaseHTTPRequestHandler):
        _webgenerator = webgenerator
        
        def do_GET(self):
            parsed_path = urlparse.urlparse(self.path)
                        
            relpath = parsed_path.path
            query = dict(urlparse.parse_qsl(parsed_path.query))

            if relpath[0] == '/':
                relpath = relpath[1:]

            if os.path.basename(relpath) == '':
                relpath = os.path.join(relpath,"index.html")
                
            debug_info = [
                'CLIENT VALUES:',
                'client_address=%s (%s)' % (self.client_address,
                                            self.address_string()),
                'command=%s' % self.command,
                'path=%s' % self.path,
                'real path=%s' % parsed_path.path,
                'query=%s' % parsed_path.query,
                'request_version=%s' % self.request_version,
                '',
                'SERVER VALUES:',
                'server_version=%s' % self.server_version,
                'sys_version=%s' % self.sys_version,
                'protocol_version=%s' % self.protocol_version,
                '',
                'HEADERS RECEIVED:',
                ]

            try:
                output = self._webgenerator.retrieve(relpath,query)
                self.send_response(200)
                self.send_header('Content-type',output['mimetype'])
                self.end_headers()
                # Send the html message
                shutil.copyfileobj(output['content'],self.wfile)
            except IOError as e:
                try:
                    output = self._webgenerator.retrieve("404", allow_urls_without_ext=True)
                    self.send_response(404)
                    self.send_header('Content-type',output['mimetype'])
                    self.end_headers()
                    # Send the html message
                    shutil.copyfileobj(output['content'],self.wfile)
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type','text/html')
                    self.end_headers()
                    if debug:
                        self.wfile.write(cgitb.html(sys.exc_info()))
                        raise
                    else:
                        self.wfile.write("<html><body>Could not display 404 error page.</body></html>")                            
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type','text/html')
                self.end_headers()
                print "== EXCEPTION OCCURED WHILE SERVING:",parsed_path
                if debug:
                    self.wfile.write(cgitb.html(sys.exc_info()))
                    raise
                else:
                    self.wfile.write("<html><body>An unexpected server error has occured.</body></html>")                    
            return            

    server = None
    try:
        server = HTTPServer(('', port), Httk_http_handler)
        print 'Started httk webserver on port ' , port
        server.serve_forever()

    except KeyboardInterrupt:
        print 'Received keyboard interrupt, shutting down the httk web server'

    finally:
        if server is not None:
            server.socket.close()
            print 'Server shutdown complete.'

        
if __name__ == '__main__':
    serve("dbweb-src", port=8080)

