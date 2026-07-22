#!/usr/bin/env python
#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2020 Rickard Armiento
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


from httk.optimade.validation.response import *
from httk.optimade.validation.base_info import *
from httk.optimade.validation.entry import *
from httk.optimade.validation.headers import *

all_tests = [
    {'name':'base_info', 'relurl':'/info', 'test':validate_base_info_request, 'validation':validate_base_info},

    {'name':'headers', 'relurl':'/info', 'test':validate_headers, 'validation':None},    
    
    {'name':'structures', 'relurl':'/all', 'test':validate_response_request, 'validation':validate_response},
    {'name':'structures', 'relurl':'/structures', 'test':validate_response_request, 'validation':validate_response},
    {'name':'structures_info', 'relurl':'/structures/info', 'test':validate_response_request, 'validation':validate_response},
    {'name':'calculations', 'relurl':'/calculations', 'test':validate_response_request, 'validation':validate_response},
    {'name':'calculations_info', 'relurl':'/calculations/info', 'test':validate_response_request, 'validation':validate_response},

    {'name':'structures_single_entry', 'relurl':'/structures', 'test':validate_single_entry_request, 'validation':validate_response},
    {'name':'calculations_single_entry', 'relurl':'/calculations', 'test':validate_single_entry_request, 'validation':validate_response},
    
]

def run(base_url, tests = None):
    
    results = {}
    
    for test in all_tests:
        if tests == None or test['name'] in tests:
            results[test['name']] = test['test'](base_url, test['relurl'])
        
    return results


