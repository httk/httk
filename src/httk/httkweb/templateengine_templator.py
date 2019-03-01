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
import os

from collections import namedtuple

class TemplateEngineTemplator(object):
    def __init__(self, template_dir, template, base_template, data):
        try:
            from web.template import render
        except ImportError:
            raise Exception("Missing docutils python modules.")
        self.render = render
        self.template_dir = template_dir
        self.template = os.path.splitext(template)[0]
        self.base_template = base_template #+".templator.html"
        self.data = dict(data)
        self.dependency_filenames = [os.path.join(self.template_dir,base_template+".templator.html"),
                                     os.path.join(self.template_dir,template)]
    
    def apply(self, content, *subcontent):
        templator = self.render(self.template_dir,base=self.base_template,globals=self.data)
        output = unicode(getattr(templator,self.template)(content,*subcontent))
        return output
        
    def get_dependency_filenames(self):
        return self.dependency_filenames
