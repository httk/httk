# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2015 Rickard Armiento
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

import inspect
from .crypto import tuple_to_hexhash
from .basic import is_sequence


class HttkTypedProperty(property):

    def __init__(self, property_type, fget=None, fset=None, fdel=None, doc=None):
        super(HttkTypedProperty, self).__init__(fget=fget, fset=fset, fdel=fdel, doc=doc)
        self.property_type = property_type
    pass


def httk_typed_property(t):
    def wrapfactory(func):
        return HttkTypedProperty(lambda: t, fget=func)
    return wrapfactory


def httk_typed_property_delayed(t):
    def wrapfactory(func):
        return HttkTypedProperty(t, fget=func)
    return wrapfactory


def httk_typed_property_resolve(cls, propname):
    for c in cls.__mro__:
        if propname in c.__dict__:
            resolve = c.__dict__[propname]
            if not isinstance(resolve, (HttkPluginWrapper, HttkPluginPlaceholder)):
                return resolve.property_type()
    raise AttributeError
          

def httk_typed_init(t, **kargs):
    def wrapfactory(func):
        func.typed_init = (lambda x=(t, kargs): x)
        return func
    return wrapfactory
            

def httk_typed_init_delayed(t, **kargs):
    def wrapfactory(func):
        func.typed_init = (t, kargs)
        return func
    return wrapfactory


class HttkObject(object):

    @classmethod     
    def types(cls):
        try:
            return cls.types_resolved
        except Exception:
            pass
        
        cls.types_resolved = {}
        typedata = cls.__init__.typed_init()
        inputkeydict = typedata[0]
        data = typedata[1]
        params = cls.__init__.func_code.co_varnames[1:]
        
        keys = []
        for param in params:
            if param in inputkeydict:
                keys += [(param, inputkeydict[param])]
            
        data['keys'] = keys    
        data['name'] = cls.__name__
        data['keydict'] = dict(keys)
        data['init_keydict'] = dict(keys)
        data['derived'] = []
        if not 'index' in data:
            data['index'] = []
        if not 'skip' in data:
            data['skip'] = []

        if not 'hexhash' in data['skip'] and not 'hexhash' in data['index']:
            data['index'] += ['hexhash']            

        for a in [x for x in dir(cls) if not x.startswith('__')]:
            if a in data['skip']:
                continue
            try:
                resolve = httk_typed_property_resolve(cls, a)
                data['derived'] += [(a, resolve)]
                if a in params:
                    data['init_keydict'][a] = resolve
                #print "SETTING TYPES: CLS",cls.__name__," DATA:",a
            except AttributeError:
                pass
        data['derived_keydict'] = dict(data['derived'])

        cls.types_resolved = data
        return data
              
    def to(self, newtype):
        method = "from_"+self.__class__.name
        if hasattr(newtype, method):
            return getattr(newtype, method)(self)
        method = "to_"+newtype.__name__
        if hasattr(self, method):
            return getattr(self, method)()

    @classmethod
    def new_from(cls, other):
        method = "from_"+other.__class__.__name__
        if hasattr(cls, method):
            return getattr(self, method)(other)
        method = "to_"+type.__name__
        if hasattr(self, method):
            return getattr(other, method)()

    @classmethod
    def use(cls, old):
        if isinstance(old, cls):
            return old
        method = "to_"+cls.__class__.__name__
        if hasattr(old, method):
            return getattr(old, method)()
        method = "from_"+old.__class__.__name__
        if hasattr(old, method):
            return getattr(old, method)(old)
        try:
            return cls.create(old)
        except Exception:
            raise
            raise Exception("HttkObject.use: found no way to convert:"+repr(old)+" into "+repr(cls))

    def to_tuple(self, use_hexhash=False):
        self.types_resolved = {}
        keydict = self.types()['keydict']
        params = self.__init__.func_code.co_varnames[1:]
        
        keys = [self.types()['name']]
        for param in params:
            if param in keydict:
                val = getattr(self, param)
                try:                   
                    if issubclass(keydict[param], HttkObject):
                        val = keydict[param].use(val)
                except TypeError as e:
                    pass                
                if use_hexhash and hasattr(val, 'hexhash'):
                    val = val.hexhash
                elif hasattr(val, 'to_tuple'):
                    val = val.to_tuple()
                elif is_sequence(val):
                    out = []
                    for x in val:
                        if use_hexhash and hasattr(x, 'hexhash'):
                            out += [x.hexhash]
                        elif hasattr(x, 'to_tuple'):
                            out += [x.to_tuple()]
                        else:
                            out += [x]
                    val = tuple(out)
                keys += [(param, val)]

        keys = tuple(keys)
        #print "TUPLE:",keys
        return keys
    
    @httk_typed_property(str)
    def hexhash(self):
        if not hasattr(self, '_hexhash') or self._hexhash is None:
            t = self.to_tuple(use_hexhash=True)
            self._hexhash = tuple_to_hexhash(t)
            
        return self._hexhash

    def get_codependent_data(self):
        if hasattr(self, '_codependent_data'):
            return self._codependent_data
        return []

    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.to_tuple() == other.to_tuple():
            return True
        else:
            return False

class HttkPluginWrapper(object):

    def __init__(self, plugin=None):
        self.plugin = plugin
        self.__doc__ = plugin.__doc__

    def __getattr__(self, static, objtype=None):
        return getattr(self.plugin, static)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.plugin(obj)
          

class HttkPlugin(object):

    def __new__(cls, main_instance):
        name = "plugin_"+cls.__name__
        try:
            return getattr(main_instance, name)
        except AttributeError:            
            obj = object.__new__(cls)
            setattr(main_instance, name, obj)
            obj.plugin_init(main_instance)
            return obj


class HttkPluginPlaceholder(object):

    def __init__(self, plugininfo=None):
        self.plugininfo = plugininfo
        
    def __getattr__(self, static, objtype=None):        
        if self.plugininfo is None:
            raise AttributeError("HttkPluginPlaceholder: Attempt to call a static plugin method. You need to load the appropriate plugin first using an appropriate python import.")
        else:
            raise AttributeError("HttkPluginPlaceholder: Attempt to call a static plugin method. You need to load the appropriate plugin first using: "+self.plugininfo)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.plugininfo is None:
            raise AttributeError("HttkPluginPlaceholder: Attempt to use plugin method on object of class:"+str(obj.__class__)+". You need to load the appropriate plugin first using an appropriate python import.")
        else:
            raise AttributeError("HttkPluginPlaceholder: Attempt to use plugin method on object of class:"+str(obj.__class__)+". You need to load the appropriate plugin first using: "+self.plugininfo)

            
