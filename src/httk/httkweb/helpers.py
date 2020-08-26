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

import os, errno

class UnquotedStr(object):
    def __init__(self,val):
        self.val = val
    def __str__(self):
        return str(self.val)
    def __repr__(self):
        return str(self.val)

def setup_template_helpers(global_data):

    def first_value(*vals):
        for val in vals:
            if val:
                return val

    #def getitem(a,i):
        #try:
        #    return global_data[a][i]
        #except TypeError:
        #    return global_data[a][int(i)]
    #    try:
    #        return a[i]
    #    except TypeError:
    #        return a[int(i)]

    global_data['first_value'] = first_value
    # global_data['getitem'] = getitem


def identify(topdir, relative_url, ext_to_class_mapper, allow_urls_without_ext=True):

    relative_url_base, __dummy, url_ext = relative_url.partition(os.extsep)
    if relative_url_base != '' and (url_ext == '' and not allow_urls_without_ext):
        raise IOError(errno.ENOENT, os.strerror(errno.ENOENT), relative_url)

    if relative_url_base == '':
        relative_url_base = 'index'

    # Identify file name for regular content
    absolute_filename = ''
    for ext in ext_to_class_mapper:
        relative_filename = relative_url_base+"."+ext
        absolute_filename = os.path.join(topdir, relative_filename)
        if os.path.exists(absolute_filename):
            break
    else:
        #print("Identify failed:",relative_url,relative_url_base,os.path.join(topdir,relative_url), "extensions examined:", [ext for ext in ext_to_class_mapper])
        raise IOError(errno.ENOENT, os.strerror(errno.ENOENT), os.path.join(topdir,relative_url))

    return {'relative_url_base':relative_url_base,'url_ext':url_ext,'absolute_filename':absolute_filename,'relative_filename':relative_filename,'class':ext_to_class_mapper[ext]}

def read_config(srcdir, renderers, default_global_data = None, override_global_data = None, config = "config"):

        # Set defaults
        global_data = {'_content_subdir': 'content', '_static_subdir':'static', '_subcontent_subdir':'subcontent',
                       '_functions_subdir': '_functions', '_template_subdir': 'templates',
                       '_use_urls_without_ext':True, '_allow_urls_without_ext':True, '_page_memcache_limit':1000}

        if default_global_data is not None:
            global_data.update(default_global_data)

        # Read global config
        try:
            config_info = identify(srcdir, config, renderers, allow_urls_without_ext=True)
        except IOError:
            if config is None:
                print("Warning: no site configuration provided, and no file exists in "+str(srcdir)+"/config.(something)")
            else:
                print("Could not find site configuration at "+str(srcdir)+"/"+str(config)+".(something)")
        else:
            configdata = config_info['class'](srcdir, config_info['relative_filename'], global_data).metadata()
            global_data.update(configdata)

        # Setup helper functions for templates to use
        setup_template_helpers(global_data)

        if override_global_data is not None:
            global_data.update(override_global_data)

        # Fix types of some settings (these must be set, as they are set in the defaults above)
        global_data['_use_urls_without_ext'] = global_data['_use_urls_without_ext'] in ['yes', 'true', 'y', True]
        global_data['_allow_urls_without_ext'] = global_data['_allow_urls_without_ext'] in ['yes', 'true', 'y', True]
        global_data['_page_memcache_limit'] = int(global_data['_page_memcache_limit'])

        return global_data

def setup(renderers, template_engines, function_handlers):
    if renderers is None:
        from httk.httkweb.render_httk import RenderHttk
        from httk.httkweb.render_rst import RenderRst
        renderers = {'httkweb': RenderHttk, 'rst': RenderRst}

    if template_engines is None:
        from httk.httkweb.templateengine_httk import TemplateEngineHttk
        from httk.httkweb.templateengine_templator import TemplateEngineTemplator
        template_engines = {'httkweb.html': TemplateEngineHttk, 'templator.html': TemplateEngineTemplator}

    if function_handlers is None:
        from httk.httkweb.functionhandler_httk import FunctionHandlerHttk
        function_handlers = {'py': FunctionHandlerHttk}

    return {'renderers':renderers, 'template_engines':template_engines, 'function_handlers':function_handlers}
