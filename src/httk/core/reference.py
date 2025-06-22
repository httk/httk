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
    
    @httk_typed_init({'ref': str, 'authors': [Author], 'editors': [Author],
                      "journal": str, "journal_issue": str, "journal_volume": str,
                      "page_first": str, "page_last": str,
                      "title": str, "year": str,            
                      "book_publisher": str,
                      "book_publisher_city": str, "book_title": str},
                     index=['ref', 'authors', 'journal', 'journal_issue', 'journal_volume', 'page_first', 'page_last', 'title', 'year', 'book_publisher', 'book_publisher_city', 'book_title'])
    def __init__(self, ref, authors=None, editors=None, journal=None, journal_issue=None, journal_volume=None, 
                 page_first=None, page_last=None, title=None, year=None, book_publisher=None,
                 book_publisher_city=None, book_title=None):
        """
        Private constructor, as per httk coding guidelines. Use .create method instead.
        """                  
        self.ref = ref
        self.authors = authors
        self.editors = editors
        self.journal = journal
        self.journal_issue = journal_issue
        self.journal_volume = journal_volume
        self.page_first = page_first
        self.page_last = page_last
        self.year = year
        self.title = title
        self.book_publisher = book_publisher
        self.book_publisher_city = book_publisher_city        
        self.book_title = book_title        

    def __str__(self):
        return "[(reference) "+self.ref+"]"
        
    @classmethod
    def create(cls, ref=None, authors=None, editors=None, journal=None, journal_issue=None, journal_volume=None, 
               page_first=None, page_last=None, title=None, year=None, book_publisher=None,
               book_publisher_city=None, book_title=None):
        """
        Create a Reference object.
        """        
        if ref is None:
            ref = ""
            if authors is not None:
                ref += ", ".join([x.given_names+" "+x.last_name for x in authors])
            if book_title is None:
                if journal is not None:
                    ref += ", "+journal
                if journal_volume is not None:
                    ref += " "+str(journal_volume)
                if page_first is not None:
                    ref += ", "+str(page_first)
                if year is not None:
                    ref += " ("+str(year)+")"
            else:
                if title is not None:
                    ref += ", "+title+" in "
                ref += book_title
                if page_first is not None:
                    ref += ", "+str(page_first)
                if editors is not None:
                    ref += ", ed. ".join([x.given_names+" "+x.last_name for x in editors])                
                if year is not None:
                    yearstr = ", "+str(year)
                else:
                    yearstr = ""
                if book_publisher is not None:
                    if book_publisher_city is None:
                        ref += " ("+book_publisher+yearstr+")"
                    else:
                        ref += " ("+book_publisher+","+book_publisher_city+yearstr+")"
         
        return cls(ref, authors=authors, editors=editors, journal=journal, journal_issue=journal_issue, journal_volume=journal_volume, 
                   page_first=page_first, page_last=page_last, title=title, year=year, book_publisher=book_publisher,
                   book_publisher_city=book_publisher_city, book_title=book_title)

   
def main():
    pass

if __name__ == "__main__":
    main()
    
    
