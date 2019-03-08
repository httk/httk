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

import string, os, codecs, cgi

from helpers import UnquotedStr

class HttkTemplateFormatter(string.Formatter):

    def format_field(self, value, spec, quote=None):
        if spec == 'unquoted' or spec.startswith('unquoted:'):
            output = self.format_field(value, spec[len('unquoted:'):],quote=False)
            return output
        elif spec == 'quote' or spec.startswith('quote:'):
            output = self.format_field(value, spec[len('quote:'):],quote=True)
            return output
        elif spec.startswith('repeat:'):
            template = spec.partition(':')[-1]
            if type(value) is dict:
                value = value.items()
            return ''.join([self.format(template,item=item,**self.data) for item in value])
        elif spec.startswith('repeat-index:'):
            template = spec.partition(':')[-1]
            if type(value) is dict:
                value = value.items()
            return ''.join([self.format(template,index=index,**self.data) for index in range(len(value))])
        elif spec == 'call' or spec.startswith('call:'):
            args = spec.split(":")
            args = [self.get_field(x[1:-1],{},self.data)[0] if (x.startswith('{') and x.endswith('}')) else x for x in args]
            return value(*args[1:])
        elif spec.startswith('if:'):
            split = spec.split(':')
            if len(split)>2:
                return (value and split[1]) or split[2]
            else:
                return (value and split[1]) or ''
        elif spec.startswith('if-set:'):
            split = spec.split(':')                           
            if value is not None:
                return split[1]
            elif len(split)>2:
                return split[2]
            else:
                return ''    
        elif value==None: 
            return ""
        else:
            output = super(HttkTemplateFormatter, self).format_field(value, spec)
            if quote is None:
                try:
                    if isinstance(value,UnquotedStr):
                        quote = False
                    else:
                        quote = True
                except TypeError:
                    quote = True
            if quote:
                output = cgi.escape(output,quote=True)
                output = output.replace(":", "&#58;") 
                output = output.replace("'", "&apos;") 
            #if type(value) != unicode and type(value) != str:
            #    return output + "("+str(type(value))+":"+str(quote)+":"+str(e)+")"
            #else:
            return output

    def get_field(self, field_name, args, kwargs):
        # Handle a key not found
        try:
            val=super(HttkTemplateFormatter, self).get_field(field_name, args, kwargs)
            # Python 3, 'super().get_field(field_name, args, kwargs)' works
        except (KeyError, AttributeError):
            val=None,field_name 
        return val 

class TemplateEngineHttk(object):
    def __init__(self, template_dir, template_filename, base_template_filename = None):
        self.template_dir = template_dir
        self.template_filename = template_filename
        self.filename = os.path.join(template_dir, template_filename)
        
        self.dependency_filenames = [self.filename]
        if base_template_filename is not None:
            self.base_filename = os.path.join(self.template_dir,base_template_filename)
            self.dependency_filenames += [self.base_filename]            
        else:
            self.base_filename = None

        self.httk_tf = HttkTemplateFormatter()
        
    def apply(self, content = None, data = None, *subcontent):

        if data == None:
            data = {}
        else:
            data = dict(data)
        self.httk_tf.data = data
        
        with codecs.open(self.filename,encoding='utf-8') as f:
            template = f.read()

        data['content'] = content        
        data['subcontent'] = subcontent

        output = self.httk_tf.format(template,**data)
        
        if self.base_filename is not None:
            with codecs.open(self.base_filename,encoding='utf-8') as f:
                base_template = f.read()
                
                data['content'] = UnquotedStr(output)
                del data['subcontent']
                
                output = self.httk_tf.format(base_template,**data)
                
        return output

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
    

    
