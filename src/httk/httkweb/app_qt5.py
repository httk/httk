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

import sys, os, StringIO, subprocess, cgitb, urlparse
from httplib import HTTPMessage

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QUrl, pyqtSlot, QObject
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWebEngineCore import QWebEngineUrlSchemeHandler, QWebEngineUrlRequestInterceptor
from PyQt5.QtWebChannel import QWebChannel

import render
import generate

from templateengine_httk import TemplateEngineHttk
from templateengine_templator import TemplateEngineTemplator
from functionhandler_httk import FunctionHandlerHttk

from render_httk import RenderHttk
from render_rst import RenderRst

class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, msg, line, source):
        print 'Console (%s): %s line %d: %s' % (level, source, line, msg)

class Backend(QObject):
    @pyqtSlot(str,result=str)
    def test(self,msg):
        pass
        #print 'call received:'+msg
        #return 'call received:'+msg
   
#class WebEngineUrlRequestInterceptor(QWebEngineUrlRequestInterceptor):
    #def interceptRequest(self, info):
    #    pass
    #    #print "== INTERCEPT",info.requestUrl(),"::",info.resourceType()

class TestIODevice(QtCore.QIODevice):
    def __init__(self, data):
        super(TestIODevice, self).__init__()
        self.open(self.ReadOnly | self.Unbuffered)
        # TODO: do proper file reading
        self._data = str(data.read())
        data.close()
        QtCore.QTimer.singleShot(200, self._dataReceived)

    def _dataReceived(self):
        #print('== RECV')
        self._data = b'foo'
        self.readyRead.emit()

    def bytesAvailable(self):
        count = len(self._data) + super(TestIODevice, self).bytesAvailable()
        #print('== AVAIL', count)
        return count

    def isSequential(self):
        return True

    def readData(self, maxSize):
        #print('== READ', maxSize)
        data, self._data = self._data[:maxSize], self._data[maxSize:]
        #print "** RETURNING:",data
        return data

    def close(self):
        #print('== CLOSE')
        super(TestIODevice, self).close()


class TestHandler(QWebEngineUrlSchemeHandler):

    def __init__(self, srcdir, renderers = None, template_engines = None, function_handlers = None, debug=True, config = None, global_data = None):
        super(TestHandler, self).__init__()

        self.debug = debug

        given_global_data = global_data
        global_data = {}    
    
        global_data['_baseurl'] = 'backend:'
        global_data['_basefunctionurl'] = 'backend:'
        global_data['_functionext'] = ''
        global_data['_render_mode'] = 'app'
    
        if renderers == None:
            renderers = {'httkweb': RenderHttk, 'rst': RenderRst}

        if template_engines == None:
            template_engines = {'httkweb.html': TemplateEngineHttk, 'templator.html': TemplateEngineTemplator}

        if function_handlers == None:
            function_handlers = {'py': FunctionHandlerHttk }            

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

        allow_urls_without_ext = True 
        urls_without_ext = True     
        self._webgenerator = generate.WebGenerator(global_data, srcdir, renderers, template_engines, function_handlers, urls_without_ext=urls_without_ext, allow_urls_without_ext=allow_urls_without_ext)

        
    def requestStarted(self, request):

        headers = {}
        response = 200
                
        url = request.requestUrl()        
        relpath = url.path()
        query = url.query()
        query = dict(urlparse.parse_qsl(query))
         
        #print "== REQUEST STARTED == RELPATH:", relpath, "QUERY:",query
            
        if relpath.startswith("/"):
            relpath = relpath[1:]

        if os.path.basename(relpath) == '':
            relpath = os.path.join(relpath,"index.html")
    
        try:
            output = self._webgenerator.retrieve(relpath, query)
            response = 200
            headers['Content-type'] = output['mimetype']
            content = output['content']
        except IOError as e:
            try:
                output = self._webgenerator.retrieve("404", allow_urls_without_ext=True)
                response = 404
                headers['Content-type'] = output['mimetype']
            except Exception as e:
                response = 500
                headers['Content-type'] = 'text/html'
                if debug:
                    outputstr = cgitb.html(sys.exc_info())
                    raise
                else:
                    outputstr = "<html><body>Could not display 404 error page.</body></html>"
                content = StringIO.StringIO(outputstr)

        except Exception as e:
            response = 500
            headers['Content-type'] = 'text/html'
            if self.debug:
                outputstr = cgitb.html(sys.exc_info())
                raise
            else:
                outputstr = "<html><body>An unexpected server error has occured.</body></html>"
            content = StringIO.StringIO(outputstr)
            
        #self.cgipath = os.path.abspath(os.path.join(self.appdir,path))
        #self.querystring = request.requestUrl().query()

        #if not self.cgipath.startswith(self.appdir):
        #    raise Exception("Unallowed cgi path:"+str(self.cgipath)+" is not "+str(self.appdir))
        #env = {
        #    'PATH':os.defpath,
        #    'QUERY_STRING':self.querystring,
        #    'BACKEND':'app'
        #}        
        #print "ENV",env
        #print "EXEC:",self.cgipath
        #
        #data = subprocess.check_output(self.cgipath, env=env)
        #headerstr, _dummy, self.content = data.partition("\n\n")

        #headerfp = StringIO.StringIO("\n"+data)
        #httpmsg = HTTPMessage(headerfp)
        #httpmsg.readheaders()        

        #for header in httpmsg:
        #    self.setRawHeader(header,httpmsg.getrawheader(header))
        #    print "Set header",header,"=",httpmsg.getrawheader(header)

        #for header in headers:
        #    self.setRawHeader(header,headers['header'])
        
        self._dev = TestIODevice(content)
        mimetype = headers['Content-type'].partition(';')[0]
        request.reply(mimetype, self._dev)

       
def run_app(appdir, renderers = None, template_engines = None, function_handlers = None, config = None, debug = True, global_data = None):
    appdir = os.path.abspath(appdir)
    
    handler = TestHandler(appdir, renderers=renderers, template_engines=template_engines, function_handlers = function_handlers, config=config, debug=debug, global_data=global_data)
    #interceptor = WebEngineUrlRequestInterceptor()

    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()

    # Get screen size
    screen = app.primaryScreen()
    geometry = screen.geometry()
    screen_width = geometry.width()
    screen_height = geometry.height()

    # Base size
    width = min(1080,screen_width)
    height = min(800,screen_height)

    view = QWebEngineView(main_window)
    page = WebEnginePage()
    channel = QWebChannel(page)
    backend = Backend()
    channel.registerObject('backend', backend)

    view.setPage(page)
    view.page().profile().installUrlSchemeHandler(b'backend', handler)
    #view.page().profile().setRequestInterceptor(interceptor)
    view.page().setWebChannel(channel)

    url = "backend:index"
    view.load(QUrl(url))
    main_window.setCentralWidget(view)

    main_window.resize(width,height)

    main_window.show()
    main_window.raise_()

    sys.exit(app.exec_())

    

