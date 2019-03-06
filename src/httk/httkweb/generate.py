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

import os, render, mimetypes, collections, time, StringIO, codecs

import helpers

class Page(object):
    def __init__(self,meta={}):
        self.title = ''
        self.content = ''
        self.update_metadata(meta)
        self.dependency_filenames = []

    def update_metadata(self, meta):
        for item in meta:
            setattr(self,item,meta[item])
            
    def __str__(self):
        return str(self.content)
    def __repr__(self):
        return str(self.content)

    
class WebGenerator(object):
    
    def __init__(self, global_data, srcdir, renderers, template_engines, function_handlers, content_subdir = 'content', static_subdir='static', urls_without_ext=False, allow_urls_without_ext=True, page_memcache_limit=1000):

        # Setup helper functions for templates to use
        helpers.setup_template_helpers(global_data)
        def access_pages(relative_url,subfield):
            page = self._retrieve_page(relative_url, update_access_timestamp=False)
            return getattr(page, subfield)
        global_data['pages'] = access_pages
        
        self.global_data = global_data
        self.srcdir = srcdir
        self.renderers = renderers
        self.template_engines = template_engines
        self.function_handlers = function_handlers
        self.content_subdir = content_subdir
        self.static_subdir = static_subdir
        self.urls_without_ext = urls_without_ext
        self.allow_urls_without_ext = allow_urls_without_ext
        self.page_memcache_limit = page_memcache_limit
        self.page_memcache = collections.OrderedDict()

    def _render_page(self, relative_filename, render_class, query, page, all_functions = False):

        global_data = dict(self.global_data)
        global_data['page'] = page
        global_data['query'] = query
        try:
            output = render.render_one_file(os.path.join(self.srcdir,self.content_subdir,relative_filename), render_class, global_data)
        except IOError as e:
            raise IOError("Requested page not found")
        
        # Support for web functions
        page.functions = []
        for entry in list(output['metadata']):
            if entry.endswith('-function'):
                function_name, function_args, function_template = output['metadata'][entry].split(':')
                function_execute = True
                function_output_name = entry[:-len('-function')]
                del output['metadata'][entry]
                
                function_args = function_args.split(',')                        
                # Check if all mandatory arguments are present
                if not all((arg.startswith('?') or arg in query) for arg in function_args):
                    if not all_functions:
                        output['metadata'][function_output_name] = ""
                        continue
                    else:
                        function_execute = False
                         
                for function_handler_ext in self.function_handlers:
                    if function_name.endswith(function_handler_ext):
                        function_filename = os.path.join(self.srcdir,"functions",function_name)
                        function_name = function_name[:-len(function_handler_ext)]
                    else:
                        function_filename = os.path.join(self.srcdir,"functions",function_name+"."+function_handler_ext)
                    if os.path.exists(os.path.join(function_filename)):
                        break                    
                else:
                    raise Exception("Could not find function handler for function: "+function_name)


                for template_engine_ext in self.template_engines:
                    if function_template.endswith("."+template_engine_ext):
                        template_filename = os.path.join(self.srcdir,"templates",page.template)
                        function_template = function_template[:-len("."+template_engine_ext)] 
                    else:
                        template_filename = os.path.join(self.srcdir,"templates",function_template+"."+template_engine_ext)
                    if os.path.exists(os.path.join(template_filename)):
                        break
                else:
                    raise Exception("Could not find template for function: "+function_template)

                instanciated_template_engine = self.template_engines[template_engine_ext](os.path.join(self.srcdir,"templates"),function_template+"."+template_engine_ext)                
                instanciated_function = self.function_handlers[function_handler_ext](os.path.join(self.srcdir,"functions"),function_name, function_args, instanciated_template_engine, global_data)
                page.functions += [{'name':function_name, 'output_name':function_output_name, 'instance':instanciated_function, 'execute':function_execute}]
                
        page.update_metadata(output['metadata'])
        page._rendered_content = output['content']

        relroot = os.path.dirname(relative_filename)
        page._relroot = relroot
        if relroot != '.' and relroot != '':
            page.relbaseurl = '/'.join(['..']*relroot.count(os.sep))
        else:
            page.relbaseurl = '.'
        if not hasattr(page,'template'):
            page.template = 'default'
        if hasattr(page,'base_template_'+global_data['_render_mode']):
            page.base_template = getattr(page, 'base_template_'+global_data['_render_mode'])
        else:
            if not hasattr(page,'base_template'):
                page.base_template = 'base_default'

        if self.urls_without_ext:
            relurl = os.path.splitext(relative_filename)[0]
        else:
            relurl = os.path.splitext(relative_filename)[0]+'.html'        
        page.relurl = relurl    
        page.absurl = global_data['_baseurl'] + relurl 
        page.functionurl = global_data['_basefunctionurl'] + os.path.splitext(relative_filename)[0] + global_data['_functionext']

        page._rendered_subcontent = []

        if hasattr(page,'subcontent'):
            for subfile in page.subcontent:
                identity = render.identify_page(self.srcdir, "subcontent", subfile,self.renderers,allow_urls_without_ext=self.allow_urls_without_ext)                
                page._rendered_subcontent += [render.render_one_file(identity['absolute_filename'], identity['render_class'], global_data)['content']]

        # Determine template to use:
        for template_engine_ext in self.template_engines:
            if page.template.endswith("."+template_engine_ext):
                template_filename = os.path.join(self.srcdir,"templates",page.template)
                page.template = page.template[:-len("."+template_engine_ext)] 
            else:
                template_filename = os.path.join(self.srcdir,"templates",page.template+"."+template_engine_ext)
            if os.path.exists(os.path.join(template_filename)):
                break
        else:
            raise Exception("Could not find template for page: "+page.template)

        # Handle query function processing
        for function in page.functions:
            if function['execute']:
                outstr = function['instance'].execute_and_format(query,global_data)                                
                page.update_metadata({function['output_name']:outstr})
        
        instaced_template_engine = self.template_engines[template_engine_ext](os.path.join(self.srcdir,"templates"),page.template+"."+template_engine_ext, page.base_template)
        page.content = instaced_template_engine.apply(page._rendered_content, data=global_data, *page._rendered_subcontent)
        
        page.mimetype = 'text/html'
        page.dependency_filenames += instaced_template_engine.get_dependency_filenames()
        
    def _retrieve_page(self, relative_url, query=None, update_access_timestamp=True, allow_urls_without_ext=None, all_functions = False):

        now = time.time()
        
        if query is None:
            query = {}
        
        canonical_request = (relative_url,all_functions,tuple(sorted(query.items())))
        
        if canonical_request in self.page_memcache:
            page = self.page_memcache[canonical_request]
            # Cache mtime to not run stat more often than once every couple of seconds
            # to efficently handle, e.g, loops that access the page every iteration
            if now < page.timestamp_last_stat + 2:
                mtime = page.timestamp_mtime
            else:
                try:
                    mtime = os.path.getmtime(page.absolute_filename)
                    for filename in page.dependency_filenames:
                        dep_mtime = os.path.getmtime(filename)
                        if dep_mtime > mtime:
                            mtime = dep_mtime
                except IOError:
                    # Handle, e.g., file removal/change of extension
                    mtime = now
                page.timestamp_mtime = mtime
                page.timestamp_last_stat = now
            # Use page cache only if rendering time is after mtime
            if page.timestamp_render > mtime: 
                # Move to the front
                del self.page_memcache[canonical_request]
                self.page_memcache[canonical_request] = page
                if update_access_timestamp:
                    page.timestamp_access = now
                return page
            else:
                del self.page_memcache[canonical_request]                    
            
        if allow_urls_without_ext is None:
            allow_urls_without_ext = self.allow_urls_without_ext

        identity = render.identify_page(self.srcdir, self.content_subdir, relative_url,self.renderers,allow_urls_without_ext=allow_urls_without_ext)
        
        page = Page()
        self.page_memcache[canonical_request] = page
        try:
            page.absolute_filename = identity['absolute_filename']
            page.timestamp_mtime = os.path.getmtime(identity['absolute_filename'])
            page.timestamp_last_stat = now
            page.timestamp_render = now
            self._render_page(identity['relative_filename'], identity['render_class'], query, page, all_functions=all_functions)
        except Exception:
            del self.page_memcache[canonical_request]
            raise
            
        # Make sure we only keep page_memcache_limit number of pages in cache
        if len(self.page_memcache) > self.page_memcache_limit:
            self.page_memcache.popitem()
            
        return page

    def retrieve(self, relative_url, query=None, allow_urls_without_ext=None, all_functions=False):

        # Check static content
        if self.static_subdir != None:
            static_file = os.path.join(self.srcdir,self.static_subdir,relative_url) 
            if os.path.exists(static_file):
                mimetype = mimetypes.MimeTypes().guess_type(static_file)[0]
                if mimetype is None:
                    mimetype = 'application/octet-stream'
                #f = codecs.open(static_file, encoding='utf-8')
                f = open(static_file,'rb')
                return {'content':f, 'mimetype':mimetype}

        page = self._retrieve_page(relative_url, query, allow_urls_without_ext=allow_urls_without_ext, all_functions=all_functions)
        content = StringIO.StringIO(page.content)        
        return {'content':content, 'mimetype':page.mimetype, 'functions':page.functions}
