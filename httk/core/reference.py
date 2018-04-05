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

from httk.core.httkobject import HttkObject, httk_typed_init


class Author(HttkObject):

    """
    Object for keeping track of tags for other objects
    """
    #@classmethod
    #def types(cls):
    #    return cls.types_declare((('reference',str),),
    #                             index=('reference'))
    
    @httk_typed_init({'last_name': str, 'given_names': str}, index=['last_name', 'given_names'])    
    def __init__(self, last_name, given_names):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """
        self.last_name = last_name
        self.given_names = given_names

    def __str__(self):
        return "[(Author) "+self.given_names+" "+self.last_name+"]"
        
    @classmethod
    def create(cls, last_name, given_names):
        """
        Create a Author object.
        """        
        return cls(last_name, given_names)


class Reference(HttkObject):

    """
    A reference citation
    """
    #@classmethod
    #def types(cls):
    #    return cls.types_declare((('reference',str),),
    #                             index=('reference'))
    
    @httk_typed_init({'ref': str, 'authors': [Author], 'authorsstr': str, 'journal': str, 'volume': str,
                      'firstpage': str, 'lastpage': str, 'year': str,
                      'publisher': str, 'publisher_extra': str},
                     index=['ref', 'authorsstr', 'journal', 'volume', 'firstpage', 'lastpage', 'year', 'publisher'])
    def __init__(self, ref, authors=None, authorsstr=None, journal=None, volume=None, firstpage=None, lastpage=None, year=None, publisher=None, publisher_extra=None):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """                  
        self.ref = ref
        self.authors = authors
        self.authorsstr = authorsstr
        self.journal = journal
        self.volume = volume
        self.firstpage = firstpage
        self.lastpage = lastpage
        self.year = year
        self.publisher = publisher
        self.publisher_extra = publisher_extra        

    def __str__(self):
        return "[(reference) "+self.ref+"]"
        
    @classmethod
    def create(cls, ref, authors=None):
        """
        Create a Reference object.
        """        
        # TODO: Sanely parse bibliographic info
        
        return cls(ref, authors=authors)

   
def main():
    pass

if __name__ == "__main__":
    main()
    
    
