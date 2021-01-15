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

'''
This file provides functions to translate an OPTIMaDe filter string into an SQL query.
'''

from __future__ import print_function
import re
from pprint import pprint

from httk.optimade.error import TranslatorError
from httk.optimade.httk_entries import httk_entry_info

from httk.atomistic import Structure
from httk.atomistic.results import Result_TotalEnergyResult

def format_value(fulltype, val, allow_null=False):
    if fulltype.startswith('list of '):
        if not isinstance(val[0], tuple):
            raise TranslatorError("Type mismatch in filter, query had single value when list of values was expected.", 400, "Bad request")
        inner_fulltype = fulltype[len('list of '):]
        outvals = []
        for v in val:
            outvals += [format_value(inner_fulltype, v, allow_null=allow_null)]
        return outvals
    elif allow_null and val[0] == 'Null':
        return None
    elif fulltype == 'integer':
        if val[0] in ['Number']:
            return int(val[1])
    elif fulltype == 'float':
        if val[0] in ['Number']:
            return float(val[1])
    elif fulltype == 'string':
        if val[0] in ['String']:
            return val[1]
    raise TranslatorError("Type mismatch in filter, expected:"+fulltype+", query has:"+val[0], 400, "Bad request")

constant_types = ['String','Number']

table_mapper = {
    'structures': Structure,
}

invert_op = {'!=': '!=', '>':'<', '<':'>', '=':'=', '<=': '>=', '>=': '<='}
_python_opmap = {'!=': '__ne__', '>': '__gt__', '<': '__lt__', '=': '__eq__', '<=': '__le__', '>=': '__ge__'}

def optimade_filter_to_httk(filter_ast, entries, searcher):

    search_variables = []

    for entry in entries:
        search_variable = searcher.variable(table_mapper[entry])
        searcher.output(search_variable,entry)
        search_variables += [search_variable]

        if filter_ast is not None:
            search_expr, needs_post = optimade_filter_to_httk_recurse(filter_ast, search_variable, entry, False)
            searcher.add(search_expr)
            if needs_post:
                searcher.add_all(search_expr)

    return searcher


def optimade_filter_to_httk_recurse(node, search_variable, entry, inv_toggle, recursion=0):

    search_expr = None
    needs_post = False
    handlers = optimade_field_handlers[entry]
    entry_info = httk_entry_info[entry]['properties']

    if node[0] in ['AND']:
        search_expr, needs_post = optimade_filter_to_httk_recurse(node[1], search_variable, entry, inv_toggle, recursion=recursion+1)
        rhs_search_expr, rhs_needs_post = optimade_filter_to_httk_recurse(node[2], search_variable, entry, inv_toggle, recursion=recursion+1)
        needs_post = needs_post or rhs_needs_post
        search_expr = search_expr & rhs_search_expr
    elif node[0] in ['OR']:
        search_expr, needs_post = optimade_filter_to_httk_recurse(node[1], search_variable, entry, inv_toggle, recursion=recursion+1)
        rhs_search_expr, rhs_needs_post = optimade_filter_to_httk_recurse(node[2], search_variable, entry, inv_toggle, recursion=recursion+1)
        needs_post = needs_post or rhs_needs_post
        search_expr = search_expr | rhs_search_expr
    elif node[0] in ['NOT']:
        search_expr, needs_post = optimade_filter_to_httk_recurse(node[1], search_variable, entry, not inv_toggle, recursion=recursion+1)
        search_expr = ~ search_expr
    elif node[0] in ['HAS_ALL', 'HAS_ANY', 'HAS_ONLY']:
        ops = node[1]
        left = node[2]
        right = node[3]
        assert(left[0] == 'Identifier')
        values = format_value(entry_info[left[1]]['fulltype'],right)
        handler = handlers[left[1]][node[0]]
        if ops != tuple(['=']*len(values)):
            raise TranslatorError("HAS queries with non-equal operators not implemented yet.", 501, "Not implemented.")
        search_expr = handler(left[1], ops, values, search_variable, node[0], inv_toggle)
        if inv_toggle or node[0] == 'HAS_ONLY':
            needs_post = True
    elif node[0] in ['LENGTH']:
        left = node[1]
        op = node[2]
        right = node[3]
        assert(left[0] == 'Identifier')
        if right[0] == 'Identifier':
            raise TranslatorError("LENGTH comparisons with non-constant right hand side not implemented.", 501, "Not implemented")
        if right[0] != 'Number':
            raise TranslatorError("LENGTH comparison can only be done with Numbers. Unexpected right hand side type:"+right[0], 501, "Not implemented")
        handler = handlers[left[1]]['length']
        assert(entry_info[left[1]]['fulltype'].startswith("list of "))
        value = format_value("integer",right)
        search_expr = handler(left[1], op, value, search_variable)
    elif node[0] in ['>', '>=', '<', '<=', '=', '!=']:
        op = node[0]
        left = node[1]
        right = node[2]
        if left[0] in constant_types and right[0] in constant_types:
            raise TranslatorError("Constant vs. Constant comparisons not implemented.", 501, "Not implemented")
        elif left[0] == 'Identifier' and right[0] == 'Identifier':
            raise TranslatorError("Identifier vs. Identifier comparisons not implemented.", 501, "Not implemented")
        else:
            if right[0] == 'Identifier' and left[0] in constant_types:
                left, right = right, left
                op = invert_op[op]
            assert(left[0] == 'Identifier')
            handler = handlers[left[1]]['comparison']
            value = format_value(entry_info[left[1]]['fulltype'],right)
            search_expr = handler(left[1], op, value, search_variable)
    else:
        pprint(node)
        raise TranslatorError("Unexpected translation error", 500, "Internal server error.")
    assert(search_expr is not None)
    return search_expr, needs_post

def string_handler(entry, op, value, search_variable):
    httk_op = _python_opmap[op]
    return getattr(getattr(search_variable,entry),httk_op)(value)

def constant_comparison_handler(val1, op, val2, search_variable):
    op = _python_opmap[op]
    # This is an ugly hack to handle the fact that (I think?) httk isn't capable of doing constant comparisons in a search
    if getattr(val1,op)(val2):
        return getattr(getattr(search_variable,'hexhash'),'__eq__')(getattr(search_variable,'hexhash'))
    else:
        return getattr(getattr(search_variable,'hexhash'),'__ne__')(getattr(search_variable,'hexhash'))

def number_handler(entry, op, value, search_variable):
    httk_op = _python_opmap[op]
    return getattr(getattr(search_variable,entry),httk_op)(value)

def timestamp_handler(entry, op, value, search_variable):
    raise TranslatorError("Timestamp comparison not yet implemented.", 501, "Not implemented.")

def set_all_handler(entry, ops, values, inv, search_variable):
    #if not inv:
    #    return getattr(getattr(search_variable,entry),'has_all')(*values)
    #else:
    #    return getattr(getattr(search_variable,entry),'has_inv_all')(*values)
    if not inv:
        search = getattr(getattr(search_variable,entry),'has_any')(values[0])
        for value in values[1:]:
            search = search & (getattr(getattr(search_variable,entry),'has_any')(value))
        return search
    else:
        search = getattr(getattr(search_variable,entry),'has_inv_any')(values[0])
        for value in values[1:]:
            search = search & (getattr(getattr(search_variable,entry),'has_inv_any')(value))
        return search

    #search = getattr(getattr(search_variable,entry),'is_in')(values[0])
    #for value in values[1:]:
    #    search = search & (getattr(getattr(search_variable,entry),'is_in')(value))
    #return search

def set_any_handler(entry, ops, values, inv, search_variable):
    if not inv:
        return getattr(getattr(search_variable,entry),'has_any')(*values)
    else:
        return getattr(getattr(search_variable,entry),'has_inv_any')(*values)
    #return getattr(getattr(search_variable,entry),'is_in')(*values)

def set_only_handler(entry, ops, values, inv, search_variable):
    if not inv:
        return getattr(getattr(search_variable,entry),'has_only')(*values)
    else:
        return getattr(getattr(search_variable,entry),'has_inv_only')(*values)

def structure_features_set_handler(op, value, inv, search_variable, has_type):
    # Any HAS ANY, HAS ALL, HAS ONLY operation will check for precense of an identifier in structure_features.
    # For now we don't support any structure features, hence, all such comparisons return False
    return getattr(getattr(search_variable,'hexhash'),'__ne__')(getattr(search_variable,'hexhash'))

def structure_features_length_handler(op, value, search_variable):
    # structure_features is assumed to always be empty
    print("HXXXERE",value)
    if value == 0:
        return getattr(getattr(search_variable,'hexhash'),'__eq__')(getattr(search_variable,'hexhash'))
    else:
        return getattr(getattr(search_variable,'hexhash'),'__ne__')(getattr(search_variable,'hexhash'))

optimade_field_handlers = {
    'structures': {
        'id': {
            'comparison': lambda entry, op, value, search_variable: string_handler('hexhash', op, value, search_variable)
        },
        'type': {
            'comparison': lambda entry, op, value, search_variable: constant_comparison_handler(value, op, 'structures', search_variable)
        },
        'elements': {
            'HAS_ALL': lambda entry, ops, values, search_variable, has_type, inv: set_all_handler('formula_symbols', ops, values, inv, search_variable),
            'HAS_ANY': lambda entry, ops, values, search_variable, has_type, inv: set_any_handler('formula_symbols', ops, values, inv, search_variable),
            'HAS_ONLY': lambda entry, ops, values, search_variable, has_type, inv: set_only_handler('formula_symbols', ops, values, inv, search_variable),
            'length': lambda entry, op, value, search_variable: number_handler('number_of_elements', op, value, search_variable)
        },
        'nelements': {
            'comparison': lambda entry, op, value, search_variable: number_handler('number_of_elements', op, value, search_variable)
        },
        'chemical_formula_descriptive': {
            'comparison': lambda entry, op, value, search_variable: string_handler('chemical_formula', op, value, search_variable)
        },
        'structure_features': {
            'HAS': lambda entry, ops, values, search_variable, has_type, inv: structure_features_set_handler(values, ops, inv, search_variable, 'HAS'),
            'HAS_ALL': lambda entry, ops, values, search_variable, has_type, inv: structure_features_set_handler(values, ops, inv, search_variable, 'HAS_ALL'),
            'HAS_ANY': lambda entry, ops, values, search_variable, has_type, inv: structure_features_set_handler(values, ops, inv, search_variable, 'HAS_ANY'),
            'length': lambda entry, op, value, search_variable: structure_features_length_handler(op, value, search_variable)
        }
    },
}
