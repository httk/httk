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

from __future__ import print_function
import string, os, sys, codecs
import inspect

# Retain python2 compatibility without a dependency on httk.core
if sys.version[0] == "2":
    # Note:
    # The "html" module is not a builtin in Python 2.
    # If it happens to be installed, we still do not
    # want to use it since it is old (last updated in 2011,
    # version 1.16). Use the builtin cgi module to get the
    # escape funtion instead.

    from cgi import escape
    unicode_type=unicode
else:
    from html import escape
    unicode_type=str

from httk.httkweb.helpers import UnquotedStr

class HttkTemplateFormatter(string.Formatter):

    def format_field(self, value, spec, quote=None, args = None, kwargs = None):
        if spec == 'unquoted' or spec.startswith('unquoted:'):
            output = self.format_field(value, spec[len('unquoted::'):],quote=False, args=args, kwargs=kwargs)
            return output
        elif spec == 'quote' or spec.startswith('quote:'):
            output = self.format_field(value, spec[len('quote::'):],quote=True, args=args, kwargs=kwargs)
            return output
        elif spec.startswith('repeat:'):
            template = spec.partition('::')[-1]
            new_kwargs = dict(kwargs) if kwargs is not None else {}
            if 'item' in new_kwargs:
                new_kwargs['items'] = [new_kwargs['item']] + new_kwargs['items'] if 'items' in new_kwargs else []
            if 'index' in new_kwargs:
                new_kwargs['indices'] = [new_kwargs['index']] + new_kwargs['indices'] if 'indices' in new_kwargs else []
            def update_and_return(update):
                new_kwargs.update(update)
                return new_kwargs
            if type(value) is dict:
                return ''.join([self.format(template,**(update_and_return({'item':value[i], 'index':i}))) for i in value])
            else:
                return ''.join([self.format(template,**(update_and_return({'item':value[i], 'index':i}))) for i in range(len(value))])
        elif spec == 'call' or spec.startswith('call:'):
            callargs, _sep, newspec = spec.partition("::")
            callargs = callargs.split(":")
            callargs = [self.get_field(x[1:-1],quote=quote,args=args,kwargs=kwargs)[0] if (x.startswith('{') and x.endswith('}')) else x for x in callargs]
            result = value(*callargs[1:])
            return self.format_field(result, newspec, quote=quote, args=args, kwargs=kwargs)
        elif spec.startswith('getitem:') or spec.startswith('getattr:'):
            x, _dummy, newspec =  spec.partition(':')[2].partition('::')
            idx = self.get_field(x[1:-1],args=args,kwargs=kwargs)[0] if (x.startswith('{') and x.endswith('}')) else x
            try:
                val = value[idx] if spec.startswith('getitem:') else getattr(value,idx)
            except TypeError:
                try:
                    val = value[int(idx)] if spec.startswith('getitem:') else ''
                except TypeError:
                    return ''
            # TODO: Check if the unicode conversion really is necessary here,
            # or if we can make sure val is always unicode.
            if newspec == '':
                return unicode_type(val)
            else:
                return self.format_field(val, newspec, quote=quote, args=args, kwargs=kwargs)
        elif spec.startswith('if:') or spec.startswith('if-not:') or spec.startswith('if-set:') or spec.startswith('if-unset:'):
            outcome = (spec.startswith('if:') and value) or (spec.startswith('if-not:') and not value) or (spec.startswith('if-set:') and value is not None) or (spec.startswith('if-unset:') and value is None)
            if not outcome:
                return ''
            template = spec.partition('::')[-1]
            return self.format(template, **kwargs)
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
            if quote and (not hasattr(self,'quote') or self.quote == True):
                output = escape(output,quote=True)
                #output = output.replace(":", "&#58;")
                output = output.replace("'", "&apos;")
            #if type(value) != unicode and type(value) != str:
            #    return output + "("+str(type(value))+":"+str(quote)+":"+str(e)+")"
            #else:
            return output

    def get_field(self, field_name, args, kwargs):
        # Handle a key not found
        # In Python 3 the 'menuitems' field_name should be 'menuitems-list'?
        # if six.PY3:
            # if field_name == "menuitems":
                # field_name = "menuitems-list"
        try:
            val = super(HttkTemplateFormatter, self).get_field(field_name, args, kwargs)
            # if six.PY3:
                # if val[0] == "i":
                    # val = ("index", field_name)
            # Python 3, 'super().get_field(field_name, args, kwargs)' works
        except (KeyError, AttributeError):
            val = None, field_name
        return val

    def vformat(self, format_string, args, kwargs, used_args=None, recursion_depth=None):
        if used_args is None:
            used_args = set()
            result = self.vformat(format_string, args, kwargs, used_args, 10)
            self.check_unused_args(used_args, args, kwargs)
            return result
        else:
            if recursion_depth < 0:
                raise ValueError('Max string recursion exceeded')
            result = []
            for literal_text, field_name, format_spec, conversion in \
                    self.parse(format_string):

                # output the literal text
                if literal_text:
                    result.append(literal_text)

                # if there's a field, output it
                if field_name is not None:
                    # this is some markup, find the object and do
                    #  the formatting

                    # given the field_name, find the object it references
                    #  and the argument it came from
                    obj, arg_used = self.get_field(field_name, args, kwargs)
                    used_args.add(arg_used)

                    # do any conversion on the resulting object
                    obj = self.convert_field(obj, conversion)

                    # expand the format spec, if needed
                    format_spec = self.vformat(format_spec, args, kwargs, used_args, recursion_depth-1)

                    # format the object and append to the result
                    result.append(self.format_field(obj, format_spec, args=args, kwargs=kwargs))

            return ''.join(result)


class TemplateEngineHttk(object):
    def __init__(self, template_dir, template_filename, base_template_filename = None):
        self.template_dir = template_dir
        self.template_filename = template_filename
        self.filename = os.path.join(template_dir, template_filename)

        self.dependency_filenames = [self.filename]
        if base_template_filename is not None:
            self.base_filename = os.path.join(self.template_dir, base_template_filename)
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

        output = self.httk_tf.format(template, **data)

        if self.base_filename is not None:
            with codecs.open(self.base_filename, encoding='utf-8') as f:
                base_template = f.read()

                data['content'] = UnquotedStr(output)
                del data['subcontent']

                output = self.httk_tf.format(base_template, **data)

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

if __name__ == "__main__":
    tf = HttkTemplateFormatter()
    # Turn off auto-quoting
    tf.quote = False

    class ExampleStrRepr(object):
        def __str__(self):
            return 'str'
        def __repr__(self):
            return 'repr'

    class ExampleAttribute(object):
        x = 'tree'
        y = [{'i':'one', 'j':'two'},'z']

    class ExampleFormatter(object):
        def __format__(self, f):
            if (f == 'test'):
                return "This is an ExampleFormatter test"
            return 'I am the ExampleFormatter'

    # Many examples adapted from https://pyformat.info/

    print("== Simple strings")
    print(tf.format("Strings:       '{a}' '{b}'",a="one", b="two"))
    print(tf.format("Align:         '{a:>10}' '{a:10}' '{a:_<10}' '{a:^10}'",a='test'))
    print(tf.format("Truncate:      '{a:.10}'",a='this string is too long'))
    print(tf.format("Truncate and pad:  '{a:20.10}'",a='this string is too long'))
    print(tf.format("Str or repr:   '{0!s}' '{0!r}' '{0}'",ExampleStrRepr()))
    from datetime import datetime
    print(tf.format("Std class support:  '{a:%Y-%m-%d %H:%M}'",a=datetime(2010,1,2,3,4)))
    print(tf.format("Own Class support:  '{a:test}' '{a}'",a=ExampleFormatter()))

    print("== Simple numbers")
    print(tf.format("Integers:      '{a}' '{a:d}'",a=42))
    print(tf.format("Floats:        '{a:f}'",a=3.141592653589793))
    print(tf.format("Number padding:'{a:06.2f}'",a=3.141592653589793))
    print(tf.format("Sign:          '{a:+d}' '{b:+d}' '{a:=+5d}'",a=42,b=-42))

    print("== Element access")
    print(tf.format("Dicts:          '{a[one]}' '{a[two]}'",a={'one':'1', 'two':'2'}))
    print(tf.format("Lists:          '{a[1]}' '{a[2]}'",a=[1,2,3,4,5]))
    print(tf.format("Attributes:     '{a.x}'",a=ExampleAttribute))
    print(tf.format("Combitations:   '{a.y[0][i]}'",a=ExampleAttribute))

    print("== Parameterization")
    print(tf.format("Alignment and width: '{a:{align}{width}}'".format(a='test', align='^', width='10')))
    print(tf.format("Precision:           '{a:.{prec}} = {b:.{prec}f}'".format(a='Test', b=2.7182, prec=3)))
    print(tf.format("Embedded:            '{a:{prec}} = {b:{prec}}'".format(a='Long text here', b=2.7182, prec='.3')))
    print(tf.format("Width and precision: '{:{width}.{prec}f}'".format(2.7182, width=5, prec=2)))
    print(tf.format("Embedded class:      '{a:{dfmt} {tfmt}}'".format(a=datetime(2010,1,2,3,4), dfmt='%Y-%m-%d', tfmt='%H:%M')))

    print("********** Functionality from superformatter (with a slight format change for repeat) **************")

    print(tf.format("Loops: '{chapters:repeat::Chapter {{item}}, }'", chapters=["I", "II", "III", "IV"]))
    print(tf.format("Calls: '{name.upper:call}'", name="eric"))
    print(tf.format("Tests: '{t:if:hello}' '{f:if:hello}' '{name:if:hello}' '{empty:if:hello}'", name="eric", empty="", t=True, f=False))
    print(tf.format("Test and nesting: 'Action: Back / Logout {manager:if:/ Delete {id}}'", manager=True, id=34))

    print("********** New functionality here **************")

    # Hint: escaped {{ }} are needed to call varibale contents inside nested formatting, which always occur after ::,
    # (If used without nesting, then the content is replaced on the level above, which, e.g., does not contain the item from a loop.)
    print("== Loops")
    print(tf.format("Indexed loops: '{chapters:repeat::Chapter {{index}}={{item}},}'", chapters=["I", "II", "III", "IV"]))
    print(tf.format("Nested loops: '{l:repeat::{{k:repeat::{{{{item}}}}({{item}})}}, }'", l=[1,2,3,4],k=["a","b","c","d"]))
    print(tf.format("Nested formatting: '{b:repeat:: {{a:.{{item}}f}},}'", a=3.141592653589793, b=["2","4","8","16"]))
    print()
    print("== Indirection")
    print(tf.format("Item access indirection: '{a:getitem:{b}}' '{c:getitem:{d}}'",a={'x':1, 'y':2}, b='x', c=["0","1","2","3"], d=2))
    print(tf.format("Attribute access indirection: '{a:getattr:{b}}'",a=ExampleAttribute, b='x'))
    print(tf.format("Attribute access indirection with formatting: '{a:getattr:{b}::>10}'",a=ExampleAttribute, b='x'))
    print()
    print("== Calls")
    print(tf.format("Calls with args: '{name.rstrip:call:,four}'", name="one,two,three,four"))
    print(tf.format("Calls with formatting: '{name.rstrip:call:,four::>20}'", name="one,two,three,four"))
    print(tf.format("Calls with argument indirection: '{name.rstrip:call:{remove}::>20}'", name="one,two,three,four", remove=",four"))
    print()
    print("== Conditionals")
    print(tf.format("With formatting: '{t:if::hello {{name:>10}}}'", name="eric", empty="", t=True, f=False))
    print(tf.format("Negation:        '{t:if-not::hello}' '{f:if-not::hello}'", empty="", t=True, f=False))
    print(tf.format("Unset:           '{empty:if::hello}' '{empty:if-unset::hello}' '{empty:if-set::hello}' '{unset:if-unset::hello}'", empty=""))
    print()
    print("== Advanced")
    print(tf.format("Item access indirection inside loops: '{a:repeat:: {{a:getitem:{{{{index}}}}}}}'",a=[5,6,7,8]))
    print()
    print("== Quoting")
    tf.quote = True
    print(tf.format("Autoquoting:                '{a}'",a="<i need to be quoted, \"indeed\" said the cat's hat>"))
    print(tf.format("Avoid quoting:              '{a:unquoted}'",a="<i need to be quoted, \"indeed\" said the cat's hat>"))
    print(tf.format("Quoting + formatting:       '{a:unquoted::>70}'",a="<i need to be quoted, \"indeed\" said the cat's hat>"))
    print(tf.format("Unquoted string: '{a}       '",a=UnquotedStr("<i need to be quoted, \"indeed\" said the cat's hat>")))
    print(tf.format("Overriding unquoted string: '{a:quote}'",a=UnquotedStr("<i need to be quoted, \"indeed\" said the cat's hat>")))
