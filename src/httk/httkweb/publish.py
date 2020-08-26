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

import os, shutil, codecs

from httk.httkweb import helpers
from httk.httkweb.webgenerator import WebGenerator

def publish(srcdir,outdir,baseurl,renderers = None, template_engines = None, function_handlers = None, config="config", override_global_data = None):

    setup = helpers.setup(renderers, template_engines, function_handlers)

    default_global_data = {'_use_urls_without_ext':False}

    global_data = helpers.read_config(srcdir, setup['renderers'], default_global_data, override_global_data, config)

    global_data['_baseurl'] = baseurl
    global_data['_basefunctionurl'] = baseurl + 'cgi-bin/'
    global_data['_functionext'] = '.cgi'
    global_data['_render_mode'] = 'publish'

    webgenerator = WebGenerator(srcdir, global_data, **setup)

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
            shutil.copystat(os.path.join(root,dirname),os.path.join(outdir,relroot,dirname))
        for filename in files:
            full_rel_filename = os.path.relpath(os.path.join(root,filename),root)
            full_rel_url, __dummy = os.path.splitext(full_rel_filename)
            full_rel_output_filename = full_rel_url + '.html'

            output = webgenerator.retrieve(full_rel_url,all_functions=True)
            if(len(output['functions'])>0):
                print("WARNING: "+full_rel_url+" has dynamic functions: " + (", ".join([x['name'] for x in output['functions']])))
                print("These must be translated into cgi scripts, which is not yet automated.")

            f_in = output['content']
            with codecs.open(os.path.join(outdir,full_rel_output_filename),'w',encoding='utf-8') as f_out:
                shutil.copyfileobj(f_in,f_out)
            f_in.close()

if __name__ == '__main__':
    here = os.path.dirname(os.path.realpath(__file__))
    srcdir = os.path.join(here,"dbweb-src")
    outdir = os.path.join(here,"dbweb-public")

    # Name has changed?
    # publish_website(srcdir, outdir, baseurl='.')
    #publish(srcdir, outdir, baseurl='.')
