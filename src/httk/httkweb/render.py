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

import os, shutil, re, errno, StringIO, codecs

def identify_page(srcdir, content_subdir, relative_url, renderers, allow_urls_without_ext=True):
    # Find out base name for regular content
    relative_url_base, relative_url_ext = os.path.splitext(relative_url)
    if relative_url_ext == '' and allow_urls_without_ext:
        pass
    elif relative_url_ext != '.html':
        print "Page request "+relative_url+" has unknown extension: "+relative_url_ext+", denying with file not found."
        raise IOError(errno.ENOENT, os.strerror(errno.ENOENT), relative_url)

    # Identify file name for regular content
    absolute_filename = ''
    for renderer_ext in renderers:
        relative_filename = relative_url_base+"."+renderer_ext
        absolute_filename = os.path.join(srcdir, content_subdir, relative_filename)
        if os.path.exists(absolute_filename):
            break
    else:
        print "No corresponding file:",absolute_filename," cwd:",os.getcwd()
        raise IOError(errno.ENOENT, os.strerror(errno.ENOENT), absolute_filename)

    render_class = renderers[renderer_ext]
    
    return {'relative_filename':relative_filename,'absolute_filename':absolute_filename, 'render_class':render_class}

def render_one_file(absolute_filename, render_class, global_data):

    with codecs.open(absolute_filename, 'r', encoding='utf-8') as f:
        source = f.read()

    renderer = render_class(global_data, source)                
        
    owd = os.getcwd()
    if os.path.dirname(absolute_filename) != '':
        os.chdir(os.path.dirname(absolute_filename))
    
    metadata = renderer.metadata()
    content = renderer.content()
    os.chdir(owd)
    
    return {'content':content, 'metadata':metadata}    


