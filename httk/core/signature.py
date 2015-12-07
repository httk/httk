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

from .httkobject import HttkObject, httk_typed_init


class SignatureKey(HttkObject):

    """
    """    

    @httk_typed_init({'keydata': str, 'description': str})    
    def __init__(self, keydata, description):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """    
        self.keydata = keydata
        self.description = description        
        
    @classmethod
    def create(cls, keydata, description):
        """
        Create a Computation object.
        """        
        return cls(keydata, description)
    

class Signature(HttkObject):

    """
    """    
    @httk_typed_init({'signature_data': str, 'key': SignatureKey})    
    def __init__(self, signature_data, key):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """    
        self.signature_data = signature_data
        self.key = key
        
    @classmethod
    def create(cls, signature_data, key):
        """
        Create a Computation object.
        """        
        return cls(signature_data, key)
    

def main():
    import httk.db
    
    backend = httk.db.backend.Sqlite('database.sqlite')
    store = httk.db.store.SqlStore(backend)
    #codeobj = httk.db.register_code(store, 'db_import_2','1.0',['httk'])        
    #print "==== Name of this code:",codeobj.name

if __name__ == "__main__":
    main()
    
    
