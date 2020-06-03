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

import os, sys, mimetypes, collections, time

from httk.httkweb import helpers
from httk.httkweb.helpers import UnquotedStr
from _ast import Or

if sys.version_info[0] == 3:
    from io import StringIO
else:
    from StringIO import StringIO

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

    def __init__(self, srcdir, global_data, renderers, template_engines, function_handlers):

        # Setup the crucial pages function
        def access_pages(relative_url,subfield):
            page = self._retrieve_page(relative_url, update_access_timestamp=False, query = False)
            return getattr(page, subfield)
        global_data['pages'] = access_pages

        self.global_data = global_data
        self.srcdir = srcdir
        self.renderers = renderers
        self.template_engines = template_engines
        self.function_handlers = function_handlers
        self.page_memcache = collections.OrderedDict()
        self.page_memcache_index = {}

        self.static_dir = os.path.join(srcdir, global_data['_static_subdir'])
        self.content_dir = os.path.join(srcdir, global_data['_content_subdir'])
        self.functions_dir = os.path.join(srcdir, global_data['_functions_subdir'])
        self.templates_dir = os.path.join(srcdir, global_data['_template_subdir'])
        self.subcontent_dir = os.path.join(srcdir, global_data['_subcontent_subdir'])
        self.page_memcache_limit = global_data['_page_memcache_limit']

        self.allow_urls_without_ext = global_data['_allow_urls_without_ext']
        self.use_urls_without_ext = global_data['_use_urls_without_ext']

        try:
            init_function_info = helpers.identify(os.path.join(srcdir,'functions'), 'init', function_handlers, allow_urls_without_ext=True)
        except IOError:
            pass
        else:
            init_function = init_function_info['class'](os.path.join(srcdir,'functions'), 'init', {}, global_data)
            init_function.execute()

    def _render_page(self, relative_filename, render_class, query, page, all_functions = False):

        global_data = dict(self.global_data)
        global_data['page'] = page
        global_data['query'] = query
        try:
            render_output = render_class(self.content_dir, relative_filename, global_data)
        except IOError as e:
            raise IOError("Requested page not found")

        metadata = render_output.metadata()
        content = render_output.content()

        # Support for web functions
        page.functions = []
        for entry in list(metadata):
            if entry.endswith('-function'):
                function_name, function_args, function_template = metadata[entry].split(':')
                function_execute = True
                function_output_name = entry[:-len('-function')]
                del metadata[entry]

                if function_args.strip() == '':
                    function_args = []
                else:
                    function_args = function_args.split(',')
                # Check if all mandatory arguments are present
                if not all( ( (arg.startswith('?') or (not arg.startswith('!') and arg in query) or (arg.startswith('!') and arg[1:] not in query) ) for arg in function_args ) ):
                    if not all_functions:
                        metadata[function_output_name] = ""
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
                instanciated_function = self.function_handlers[function_handler_ext](os.path.join(self.srcdir,"functions"),function_name, function_args, global_data, instanciated_template_engine)
                page.functions += [{'name':function_name, 'output_name':function_output_name, 'instance':instanciated_function, 'execute':function_execute}]

        page.update_metadata(metadata)
        page._rendered_content = content

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

        if self.use_urls_without_ext:
            relurl = os.path.splitext(relative_filename)[0]
        else:
            relurl = os.path.splitext(relative_filename)[0]+'.html'
        page.relurl = relurl
        page.absurl = global_data['_baseurl'] + relurl
        page.functionurl = global_data['_basefunctionurl'] + os.path.splitext(relative_filename)[0] + global_data['_functionext']

        page._rendered_subcontent = []

        if hasattr(page,'subcontent'):
            for subfile in page.subcontent:
                identity = helpers.identify(self.subcontentdir, subfile, self.renderers, allow_urls_without_ext=True)
                page._rendered_subcontent += [UnquotedStr(identity['render_class'](self.subcontentdir, identity['relative_filename'], global_data)['content'])]

        # Determine template to use:
        template_identity = helpers.identify(self.templates_dir, page.template, self.template_engines, allow_urls_without_ext=True)

        # Handle query function processing
        for function in page.functions:
            if function['execute']:
                outstr = function['instance'].execute_and_format(query,global_data)
                page.update_metadata({function['output_name']:outstr})
                #print("RESULT OF RUN:",outstr,"::",function['output_name'])

        base_template_identity = helpers.identify(self.templates_dir,page.base_template,self.template_engines, allow_urls_without_ext=True)
        instaced_template_engine = template_identity['class'](self.templates_dir, template_identity['relative_filename'], base_template_identity['relative_filename'])
        page.content = instaced_template_engine.apply(UnquotedStr(page._rendered_content), data=global_data, *page._rendered_subcontent)

        page.mimetype = 'text/html'
        page.dependency_filenames += instaced_template_engine.get_dependency_filenames()

    def _retrieve_page(self, relative_url, query=None, update_access_timestamp=True, allow_urls_without_ext=None, all_functions = False):

        now = time.time()
        page = None

        no_query = query is False
        if query is None or query is False:
            query = {}

        canonical_request = (relative_url,all_functions,tuple(sorted(query.items())))

        if canonical_request in self.page_memcache:
            page = self.page_memcache[canonical_request]
        elif no_query and relative_url in self.page_memcache_index:
            # Get last key from of OrderedDict
            canonical_request = next(reversed(self.page_memcache_index[relative_url]))
            page = self.page_memcache[canonical_request]

        if page is not None:
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

        identity = helpers.identify(self.content_dir, relative_url,self.renderers,
                allow_urls_without_ext=allow_urls_without_ext)

        page = Page()
        if relative_url not in self.page_memcache_index:
            self.page_memcache_index[relative_url] = collections.OrderedDict()
        self.page_memcache_index[relative_url][canonical_request] = True
        self.page_memcache[canonical_request] = page

        try:
            page.absolute_filename = identity['absolute_filename']
            page.timestamp_mtime = os.path.getmtime(identity['absolute_filename'])
            page.timestamp_last_stat = now
            page.timestamp_render = now
            self._render_page(identity['relative_filename'], identity['class'],
                    query, page, all_functions=all_functions)
        except Exception:
            del self.page_memcache[canonical_request]
            del self.page_memcache_index[relative_url][canonical_request]
            if len(self.page_memcache_index[relative_url]) == 0:
                del self.page_memcache_index[relative_url]
            raise

        # Make sure we only keep page_memcache_limit number of pages in cache
        if len(self.page_memcache) > self.page_memcache_limit:
            prune_key = self.page_memcache.popitem()[0]
            del self.page_memcache_index[prune_key[0]][prune_key]
            if len(self.page_memcache_index[prune_key[0]]) == 0:
                del self.page_memcache_index[prune_key[0]]

        return page

    def retrieve(self, relative_url, query=None, allow_urls_without_ext=None, all_functions=False):

        # Check static content
        if self.static_dir != None:
            static_file = os.path.join(self.static_dir,relative_url)
            if os.path.exists(static_file):
                mimetype = mimetypes.MimeTypes().guess_type(static_file)[0]
                if mimetype is None:
                    mimetype = 'application/octet-stream'
                #f = codecs.open(static_file, encoding='utf-8')
                f = open(static_file,'rb')
                return {'content':f, 'mimetype':mimetype}

        page = self._retrieve_page(relative_url, query, allow_urls_without_ext=allow_urls_without_ext, all_functions=all_functions)
        content = StringIO(page.content)
        return {'content':content, 'mimetype':page.mimetype, 'functions':page.functions}
