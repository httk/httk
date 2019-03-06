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

import os, shutil, re, codecs
import render
import generate

from templateengine_httk import TemplateEngineHttk
from templateengine_templator import TemplateEngineTemplator
from render_httk import RenderHttk
from render_rst import RenderRst
from functionhandler_httk import FunctionHandlerHttk

def render_website(srcdir,outdir,baseurl,renderers = None, template_engines = None, function_handlers = None, config=None, global_data = None):

    given_global_data = global_data
    global_data = {}    
            
    global_data['_baseurl'] = baseurl
    global_data['_basefunctionurl'] = baseurl + 'cgi-bin/'
    global_data['_render_mode'] = 'publish'
    global_data['_functionext'] = '.cgi'
    
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

    urls_without_ext = 'urls_without_ext' in global_data and global_data['urls_without_ext'] in ['yes', 'true', 'y']
    webgenerator = generate.WebGenerator(global_data, srcdir, renderers, template_engines, function_handlers, urls_without_ext=urls_without_ext, allow_urls_without_ext=True)    
        
    for root, dirs, files in os.walk(os.path.join(srcdir,"static")):
        relroot = os.path.relpath(root, os.path.join(srcdir,"static"))
        for dirname in dirs:
            os.mkdir(os.path.join(outdir,relroot,dirname))
            shutil.copystat(os.path.join(root,dirname),os.path.join(outdir,relroot,dirname))
        for filename in files:
            shutil.copy2(os.path.join(root,filename), os.path.join(outdir,relroot,filename))

    for root, dirs, files in os.walk(os.path.join(srcdir,"content")):
        relroot = os.path.relpath(root, os.path.join(srcdir,"content"))
        for dirname in dirs:
            os.mkdir(os.path.join(outdir,relroot,dirname))
            shutil.copystat(os.path.join(root,d),os.path.join(outdir,relroot,dirname))
        for filename in files:
            full_rel_filename = os.path.relpath(os.path.join(root,filename),root)
            full_rel_url, full_rel_filename_ext = os.path.splitext(full_rel_filename)
            full_rel_output_filename = full_rel_url + '.html'
            
            output = webgenerator.retrieve(full_rel_url,all_functions=True)
            if(len(output['functions'])>0):
                print "WARNING: "+full_rel_url+" has dynamic functions: " + (", ".join([x['name'] for x in output['functions']]))
                print "These must be translated into cgi scripts, which is not yet automated."
            
            f_in = output['content']
            with codecs.open(os.path.join(outdir,full_rel_output_filename),'w',encoding='utf-8') as f_out:
                shutil.copyfileobj(f_in,f_out)
            f_in.close()
                
if __name__ == '__main__':
    here = os.path.dirname(os.path.realpath(__file__))
    srcdir = os.path.join(here,"dbweb-src")
    outdir = os.path.join(here,"dbweb-public")
    
    render_website(srcdir,outdir,baseurl='.')

    
