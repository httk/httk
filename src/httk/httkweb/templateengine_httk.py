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

# Closely inspired from
#   https://makina-corpus.com/blog/metier/2016/the-worlds-simplest-python-template-engine
#   https://github.com/ebrehault/superformatter

import string, os, codecs

class HttkTemplateFormatter(string.Formatter):

    def format_field(self, value, spec):
        if spec.startswith('repeat:'):
            template = spec.partition(':')[-1]
            if type(value) is dict:
                value = value.items()
            return ''.join([self.format(template,item=item,**self.data) for item in value])
        elif spec == 'call' or spec.startswith('call:'):
            args = spec.split(":")
            return value(*args[1:])
        elif spec.startswith('if:'):
            return (value and spec.partition(':')[-1]) or ''
        else:
            return super(HttkTemplateFormatter, self).format_field(value, spec)

class TemplateEngineHttk(object):
    def __init__(self, template_dir, template, base_template, data):
        try:
            from web.template import render
        except ImportError:
            raise Exception("Missing docutils python modules.")
        self.render = render
        self.template_dir = template_dir
        self.template = template
        self.base_template = base_template+".httkweb.html"
        self.data = dict(data)
        self.httk_tf = HttkTemplateFormatter()
        self.httk_tf.data = data
        self.dependency_filenames = [os.path.join(self.template_dir,self.template), os.path.join(self.template_dir,self.base_template)]
        
    def apply(self, content, *subcontent):
        with codecs.open(os.path.join(self.template_dir,self.template),encoding='utf-8') as f:
            template = f.read()
        with codecs.open(os.path.join(self.template_dir,self.base_template),encoding='utf-8') as f:
            base_template = f.read()

        self.data['content'] = content        
        self.data['subcontent'] = subcontent

        output = self.httk_tf.format(template,**self.data)
        self.data['content'] = output
        del self.data['subcontent']
        return self.httk_tf.format(base_template,**self.data)

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
    

    
