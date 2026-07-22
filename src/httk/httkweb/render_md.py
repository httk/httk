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

# Do import inside _render(self) so that the missing import is only triggered if the class is actually used.

import re, codecs, os

class RenderMd(object):

    def __init__(self, render_dir, render_filename, global_data):

        self.html = None
        self.meta = None
        self.render_dir = render_dir
        self.render_filename = render_filename
        self.global_data = global_data
        self.filename = os.path.join(render_dir, render_filename)

    def _render(self):

        try:
            import markdown
            import yaml
        except ImportError:
            raise Exception("Missing markdown python module.")

        with codecs.open(self.filename, 'r', encoding='utf-8') as f:
            source = f.read()

        # chdir to the render_dir temporarily while rendering to handle includes etc. that needs to be parsed relative to the render_dir
        if self.render_dir != '':
            owd = os.getcwd()
            os.chdir(self.render_dir)
        try:
            md = markdown.Markdown(output_format="html5",
                           extensions = ['mdx_math', 'codehilite', 'fenced_code', 'meta'],
                           extension_configs={'mdx_math': {"enable_dollar_delimiter": False}})

            self.html = md.convert(source)
            meta = md.Meta
        finally:
            if self.render_dir != '':
                os.chdir(owd)


        # Reprocess the strange builtin python markdown metadata parser output as proper yaml
        yamlstr = ""
        for field in meta:
            yamlstr += field+": "+"\n".join(meta[field])+"\n"

        self.meta = yaml.safe_load(yamlstr)


    def content(self):
        if not self.html:
            self._render()
        return self.html

    def metadata(self):
        if not self.meta:
            self._render()
        return self.meta
