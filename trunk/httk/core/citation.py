# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2013 Rickard Armiento
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
using httk by setting 'auto_print_citations_at_exit=true' in httk.cfg

Right now this is mostly a proof of concept code, and was added in response to a concern that co-authors of the software 
would not get credit. We should extend this to add a facility to make it easier to track and acknowledge citations
also of the data being used.
"""
from httk.config import config

module_citations = {}
external_citations = {}

def add_src_citation(module, author):
    if not module in module_citations:
        module_citations[module] = set()
    module_citations[module].add(author)

def add_ext_citation(software, author):
    if not software in external_citations:
        external_citations[software] = set()
    external_citations[software].add(author)

def print_citations():
    authors = {}
    for citation in module_citations:
        module_authors = module_citations[citation]
        for author in module_authors:
            if author in authors:
                authors[author].add(citation)
            else:
                authors[author] = set([citation])

    credits = []
    for author in authors:
        credits.append(author+" ("+(", ".join(authors[author]))+")")

    print ""
    print "===================================================="
    print "This program uses the high-throughput toolkit (httk)"
    print "  (c) 2012-2013",", ".join(credits)
    if external_citations != {}:
        print "From within httk the following software was also used:"
    
        credits = []
        for software in external_citations:
            print "  * "+software+" by "+", ".join(external_citations[software])
    print "===================================================="

auto_print_citations_at_exit=False

def print_citations_at_exit():
    global auto_print_citations_at_exit
    if not auto_print_citations_at_exit:
        import atexit
        atexit.register(print_citations)
        auto_print_citations_at_exit = True

try:
    val = config.get("general", "auto_print_citations_at_exit")
    if val == 'yes':
        print_citations_at_exit()
except Exception:
    pass


