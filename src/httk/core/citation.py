# -*- coding: utf-8 -*- 
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

"""
Keep track of citation information for different parts of httk, so that this info can be printed out on program exit.
Turn on either explicitly by calling httk.config.print_citations_at_exit() from your program, or implicitly for all software
using httk by setting 'auto_print_citations_at_exit=yes' in httk.cfg

Right now this is mostly a proof of concept code, and was added in response to a concern that co-authors of the software 
would not get credit. We should extend this to add a facility to make it easier to track and acknowledge citations
also of the data being used.
"""
from collections import OrderedDict
from ..versioning import httk_version, httk_copyright_note, httk_version_date

# TODO: Convert to using real instances of the core.reference.Reference class instead.

from httk.config import config
from .reference import Reference, Author

module_citations = OrderedDict()
external_citations = OrderedDict()


def add_src_citation(module, author):
    if module not in module_citations:
        module_citations[module] = set()
    module_citations[module].add(author)


def add_ext_citation(software, author):
    if software not in external_citations:
        external_citations[software] = set()
    external_citations[software].add(author)


auto_print_citations_at_exit = False
cancel_print_citations = False


def print_citations():
    global cancel_print_citations
    if cancel_print_citations:
        return
    #authors = {}
    #for citation in module_citations:
    #    module_authors = module_citations[citation]
    #    for author in module_authors:
    #        if author in authors:
    #            authors[author].add(citation)
    #        else:
    #            authors[author] = set([citation])
    #
    #creditlist = []
    #for author in authors:
    #    creditlist.append(author+" ("+(", ".join(authors[author]))+")")

    print ""
    print "=================================================================="
    print "This program used the high-throughput toolkit"
    print "  httk v" + httk_version + " (" + httk_version_date + "), " + httk_copyright_note
    print 
    print "Credits for httk modules used in this run:"
    for module in module_citations:
        print "  ("+module+")", ",".join(module_citations[module])
        #print ", ".join(creditlist)
    if external_citations != {}:
        print "From within httk the following software was also used:"
    
        creditlist = []
        for software in external_citations:
            print "  * "+software+" by "+", ".join(external_citations[software])
    print "=================================================================="


def print_citations_at_exit():
    global auto_print_citations_at_exit, cancel_print_citations
    if not auto_print_citations_at_exit:
        import atexit
        atexit.register(print_citations)
        auto_print_citations_at_exit = True
    cancel_print_citations = False


def dont_print_citations_at_exit():
    global cancel_print_citations
    auto_print_citations_at_exit = False
    cancel_print_citations = True

try:
    val = config.get("general", "auto_print_citations_at_exit")
    if val == 'yes':
        print_citations_at_exit()
except Exception:
    pass

httk_author_rickard_armiento = Author.create(u"Armiento", u"Rickard")
httk_author_torbjorn_bjorkman = Author.create(u"Björkman", u"Torbjörn")
httk_reference_main = Reference.create(ref="The high-throughput toolkit (httk) (2012-2015)", authors=[httk_author_rickard_armiento, httk_author_torbjorn_bjorkman])
