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
import sys, os

from importlib import import_module
from httk.httkweb.helpers import UnquotedStr

class FunctionHandlerHttk(object):
    def __init__(self, function_dir, function_filename, arg_names, global_data, instanced_template_engine = None):
        self.global_data = global_data
        self.function_dir = function_dir
        self.arg_names = arg_names
        self.function_name = function_filename.split(os.extsep)[0]
        self.instanced_template_engine = instanced_template_engine
        self.filename = os.path.join(function_dir, function_filename)
        self.dependency_filenames = [self.filename]

        if instanced_template_engine is not None:
            self.dependency_filenames += instanced_template_engine.get_dependency_filenames()

        sys.path.append(function_dir)
        self.imported_module = import_module(self.function_name)

    def execute(self, args = None):
        if args is None:
            args = {}
        callargs = dict(args)
        callargs['global_data'] = self.global_data
        return self.imported_module.execute(**callargs)

    def execute_and_format(self, args, data):
        output = self.execute(args)
        joint = dict(data)
        joint['result']=output
        return UnquotedStr(self.instanced_template_engine.apply(data=joint))

    def get_dependency_filenames(self):
        return self.dependency_filenames

#        data = dict(self.global_data)
#        data['content'] = page._rendered_content
#        if hasattr(page,_rendered_subcontent) and page._rendered_subcontent is not None:
#            data['subcontent'] = page._rendered_subcontent
#        content = self.httk_tf.format(template,data)
#        data['content'] = content
#        del data['subcontent']
#        return self.httk_tf.format(base_template,data)
