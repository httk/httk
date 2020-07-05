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

import sys, os.path, inspect

_realpath = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))

if sys.version_info < (3, 4):

    from imp import find_module, load_module

    def submodule_import_external(modulepath, pkg):
        pathstr = os.path.join(_realpath, modulepath)

        try:
            fp, pathname, description = find_module(pkg, [pathstr])
        except ImportError as e:
            return e
        try:
            mod = load_module(pkg, fp, pathname, description)
        finally:
            # since we may exit via an exception, close fp explicitly
            if fp:
                fp.close()
        return mod

else: # sys.version_info >= (3, 4)

    import importlib
    
    loader_details = (
        importlib.machinery.ExtensionFileLoader,
        importlib.machinery.EXTENSION_SUFFIXES
    )

    def submodule_import_external(modulepath, pkg):
        pathstr = os.path.join(_realpath, modulepath)
        
        toolsfinder = importlib.machinery.FileFinder(modulepath, loader_details)
        spec =  toolsfinder.find_spec(pkg)
                
        # To mimic the behavior of imp.find_module, it seems we also need to test this
        if spec is None:
            spec = importlib.util.find_spec(pkg)

        if spec is None:
            raise ImportError("Could not find module")
        
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
            
        return mod
    
