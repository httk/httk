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
    
    def __init__(self, global_data, srcdir, renderers, template_engines, content_subdir = 'content', static_subdir='static', urls_without_ext=False, allow_urls_without_ext=True, page_memcache_limit=1000):

        def access_pages(relative_url,subfield):
            page = self._retrieve_page(relative_url, update_access_timestamp=False)
            return getattr(page, subfield)

        global_data['pages'] = access_pages
        
        self.global_data = global_data
        self.srcdir = srcdir
        self.renderers = renderers
        self.template_engines = template_engines
        self.content_subdir = content_subdir
        self.static_subdir = static_subdir
        self.urls_without_ext = urls_without_ext
        self.allow_urls_without_ext = allow_urls_without_ext
        self.page_memcache_limit = page_memcache_limit
        self.page_memcache = collections.OrderedDict()

    def _render_page(self, relative_filename, render_class, page):

        global_data = dict(self.global_data)
        global_data['page'] = page
        try:
            output = render.render_one_file(os.path.join(self.srcdir,self.content_subdir,relative_filename), render_class, global_data)
        except IOError as e:
            raise IOError("Requested page not found")

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
        if not hasattr(page,'base_template'):
            page.base_template = 'base_default'                    

        if self.urls_without_ext:
            relurl = os.path.splitext(relative_filename)[0]
        else:
            relurl = os.path.splitext(relative_filename)[0]+'.html'        
        page.relurl = relurl    

        page._rendered_subcontent = []

        if hasattr(page,'subcontent'):
            for subfile in page.subcontent:
                identity = render.identify_page(self.srcdir, "subcontent", subfile,self.renderers,allow_urls_without_ext=allow_urls_without_ext)                
                page._rendered_subcontent += [render_one_file(identity['absolute_filename'], identity['render_class'], global_data)['content']]

        # Determine template to use:
        for template_engine_ext in self.template_engines:
            if page.template.endswith(template_engine_ext):
                template_filename = os.path.join(self.srcdir,"templates",page.template)
            else:
                template_filename = os.path.join(self.srcdir,"templates",page.template+"."+template_engine_ext)
            if os.path.exists(os.path.join(template_filename)):
                break
        else:
            raise Exception("Could not find template for page: "+page.template)
        
        template_engine = self.template_engines[template_engine_ext](os.path.join(self.srcdir,"templates"),page.template+"."+template_engine_ext, page.base_template, global_data)
        
        page.content = template_engine.apply(page._rendered_content, *page._rendered_subcontent)
        page.mimetype = 'text/html'
        page.dependency_filenames += template_engine.get_dependency_filenames()
        
    def _retrieve_page(self, relative_url, update_access_timestamp=True, allow_urls_without_ext=None):

        now = time.time()
        
        if relative_url in self.page_memcache:
            page = self.page_memcache[relative_url]
            # Cache mtime to not run stat more often than once every couple of seconds
            # to efficently handle, e.g, loops that access the page every iteration
            if now < page.timestamp_last_stat + 2:
                mtime = page.timestamp_mtime
            else:
                try:
                    mtime = os.path.getmtime(page.absolute_filename)
                    print "CHECK MTIME", page.dependency_filenames
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
                del self.page_memcache[relative_url]
                self.page_memcache[relative_url] = page
                if update_access_timestamp:
                    page.timestamp_access = now
                return page
            else:
                del self.page_memcache[relative_url]                    
            
        if allow_urls_without_ext is None:
            allow_urls_without_ext = self.allow_urls_without_ext

        identity = render.identify_page(self.srcdir, self.content_subdir, relative_url,self.renderers,allow_urls_without_ext=allow_urls_without_ext)
        
        page = Page()
        self.page_memcache[relative_url] = page
        try:
            page.absolute_filename = identity['absolute_filename']
            page.timestamp_mtime = os.path.getmtime(identity['absolute_filename'])
            page.timestamp_last_stat = now
            page.timestamp_render = now
            self._render_page(identity['relative_filename'], identity['render_class'], page)
        except Exception:
            del self.page_memcache[relative_url]
            raise
            
        # Make sure we only keep page_memcache_limit number of pages in cache
        if len(self.page_memcache) > self.page_memcache_limit:
            OrderedDict.popitem()
            
        return page

    def retrieve(self, relative_url, allow_urls_without_ext=None):

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

        page = self._retrieve_page(relative_url, allow_urls_without_ext=allow_urls_without_ext)
        content = StringIO.StringIO(page.content)        
        return {'content':content, 'mimetype':page.mimetype}
