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

# Do import inside class __init__ so that the missing import is only triggered if the class is actually used.

import re, codecs, os

class RenderRst(object):

    def __init__(self, render_dir, render_filename, global_data):

        self.render_dir = render_dir
        self.render_filename = render_filename
        self.global_data = global_data
        self.filename = os.path.join(render_dir, render_filename)

        with codecs.open(self.filename, 'r', encoding='utf-8') as f:
            self.source = f.read()

        try:
            from docutils.core import publish_parts, publish_doctree
        except ImportError:
            raise Exception("Missing docutils python modules.")

        self.publish_parts = publish_parts
        self.publish_doctree = publish_doctree

    def content(self):

        if self.render_dir != '':
            owd = os.getcwd()
            os.chdir( self.render_dir)
        try:
            html = self.publish_parts(self.source, writer_name='html')['html_body']
            # Bugfix: older versions of docutils returns a table with the docinfo inline
            html = re.sub(r"<table class=\"docinfo\"([^\$]+?)</table>", r"", html, re.M)
        finally:
            if  self.render_dir != '':
                os.chdir(owd)

        return html

    def metadata(self):
        # Parse reStructuredText input, returning the Docutils doctree as
        # an `xml.dom.minidom.Document` instance.
        d = {}

        if self.render_dir != '':
            owd = os.getcwd()
            os.chdir(self.render_dir)

        try:

            doctree = self.publish_doctree(self.source)
            docdom = doctree.asdom()

            #print("DOCTREE",doctree)

            # Todo: instead traverse the content of the docinfo node,
            # add tags in there to the dict + handle field_name + field_body section.

            # Get all field lists in the document.
            fields = docdom.getElementsByTagName('field')


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

            if  self.render_dir != '':
                os.chdir(owd)
        finally:
            if self.render_dir != '':
                os.chdir(owd)

        return d
