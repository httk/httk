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

import os, shutil, re

import web

from docutils.core import publish_parts, publish_doctree

class Page(object):
    def __init__(self,meta):
        for item in meta:
            setattr(self,item,meta[item])
        if 'title' not in meta:
            self.title = ''
        if '_content' not in meta:
            self._content = ''            
    def __str__(self):
        return self._content
    def __repr__(self):
        return self._content
        
def render_rst(source):
    html = publish_parts(source, writer_name='html')['html_body']
    # Bugfix: older versions of docutils returns a table with the docinfo inline
    html = re.sub(r"<table class=\"docinfo\"([^\$]+?)</table>", r"", html, re.M)

    return html

def get_rst_docinfo(source):
    # Parse reStructuredText input, returning the Docutils doctree as
    # an `xml.dom.minidom.Document` instance.
    doctree = publish_doctree(source)
    docdom = doctree.asdom()

    #print "DOCTREE",doctree

    # Todo: instead traverse the content of the docinfo node,
    # add tags in there to the dict + handle field_name + field_body section.

    # Get all field lists in the document.
    fields = docdom.getElementsByTagName('field')

    d = {}

    for field in fields:
        # I am assuming that `getElementsByTagName` only returns one element.
        field_name = field.getElementsByTagName('field_name')[0]
        field_name_str = field_name.firstChild.nodeValue.lower()
        field_body = field.getElementsByTagName('field_body')[0]

        if field_name_str.endswith("-list"):
            field_name_str = field_name_str[:-len("-list")]
            if field_body.firstChild.tagName == 'bullet_list':
                d[field_name_str] = [x.firstChild.firstChild.nodeValue for c in field_body.childNodes for x in c.childNodes]
            else:
                d[field_name_str] = [c.firstChild.nodeValue for c in field_body.childNodes]
        else:
            d[field_name_str] = "\n\n".join(c.firstChild.toxml() for c in field_body.childNodes)

    return d

#def read_rst_file(source):    
#    docinfo = get_rst_docinfo(source)    
#    if 'layout' in docinfo:
#        layout = docinfo['layout']
#    else:
#        layout = 'single'        
#    return {'layout': layout, 'data':docinfo, 'content':render_rst(source)}

def render_website(srcdir,outdir,baseurl):
    owd = os.getcwd()

    pages = {}

    global_data = {'render_rst':render_rst, 'baseurl':baseurl, 'email':'', 'social':'', 'copyright':'', 'pages':pages}
    
    # Read global config
    configpath = os.path.join(srcdir,'config.rst')
    if os.path.exists(configpath):
        with open(configpath, 'r') as f:
            source = f.read()
        os.chdir(srcdir)
        config = get_rst_docinfo(source)
        os.chdir(owd)        
        global_data.update(config)
        
    #render = web.template.render(os.path.join(srcdir,'templates'),base='layout',globals=global_data)

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
            if filename.endswith(".rst"):
                with open(os.path.join(root,filename), 'r') as f:
                    source = f.read()
                os.chdir(srcdir)
                page = Page(get_rst_docinfo(source))
                os.chdir(owd)
                page._source = source 
                page._relroot = relroot
                if relroot != '.':
                    page.relbaseurl = '/'.join(['..']*relpath.count(os.sep))
                else:
                    page.relbaseurl = '.'
                if not hasattr(page,'layout'):
                    page.layout = 'default'
                if not hasattr(page,'base_layout'):
                    page.base_layout = 'layout'                    
                pages[full_rel_filename] = page
                relurl = os.path.splitext(full_rel_filename)[0]+'.html'
                page.relurl = relurl
            else:
                continue

        for full_rel_filename in pages:
            print "Generating page:",full_rel_filename

            page = pages[full_rel_filename]
            page._content = render_rst(page._source)
            del page._source 
            relroot = page._relroot            
            
            render = web.template.render(os.path.join(srcdir,'templates'),base=page.base_layout,globals=dict(global_data))
            if hasattr(page,'subcontent'):
                subcontent = []
                for subfile in [x.strip() for x in page.subcontent]:
                    with open(os.path.join(srcdir,"subcontent",subfile), 'r') as f:
                        source = f.read()
                    os.chdir(srcdir)
                    subcontent += [render_rst(source)['content']]
                    os.chdir(owd)
                result = getattr(render,page.layout)(page,*subcontent)
            else:
                result = getattr(render,page.layout)(page)
                
            with open(os.path.join(outdir,page.relurl),'w') as f:
                f.write(str(result))

            
if __name__ == '__main__':
    here = os.path.dirname(os.path.realpath(__file__))
    srcdir = os.path.join(here,"dbweb-src")
    outdir = os.path.join(here,"dbweb-public")
    
    render_website(srcdir,outdir,'http://127.0.0.1/')

    
