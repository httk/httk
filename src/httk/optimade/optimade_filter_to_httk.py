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

from .error import TranslatorError

from httk.atomistic import Structure
from httk.atomistic.results import Result_TotalEnergyResult

constant_types = ['String','Number']

columns_mapper = {
    'structures': {
        'id': 'id',
        'local_id': 'local_id',
        'modification_date': 'modification_date',
        'elements': 'formula_symbols',
        'nelements': 'number_of_elements',
        'chemical_formula_descriptive': 'chemical_formula',
        'formula_prototype': 'formula_prototype'
    },
    'calculations': {
        'id': 'id',
        'local_id': 'local_id',
        'modification_date': 'modification_date',
    }
}

table_mapper = {
    'structures': Structure,
    'calculations': Result_TotalEnergyResult
}

def optimade_filter_to_httk(filter_ast, entries, searcher):

    search_variables = []

    for entry in entries:
        search_variable = searcher.variable(table_mapper[entry])
        searcher.output(search_variable,entry)
        search_variables += [search_variable]

        if filter_ast is not None:
            search_expr = optimade_filter_to_httk_recurse(filter_ast, search_variable, columns_mapper[entry], optimade_valid_columns_per_entry[entry])
            searcher.add(search_expr)

    return searcher


def optimade_filter_to_httk_recurse(node, search_variable, columns_mapper, columns_handlers, recursion=0):

    search_expr = None

    if node[0] in ['AND']:
        search_expr = optimade_filter_to_httk_recurse(node[1], search_variable, columns_mapper, columns_handlers, recursion=recursion+1)
        search_expr = search_expr and optimade_filter_to_httk_recurse(node[2], search_variable, columns_mapper, columns_handlers, recursion=recursion+1)
    if node[0] in ['OR']:
        search_expr = optimade_filter_to_httk_recurse(node[1], search_variable, columns_mapper, columns_handlers, recursion=recursion+1)
        search_expr = search_expr or optimade_filter_to_httk_recurse(node[2], search_variable, columns_mapper, columns_handlers, recursion=recursion+1)
    elif node[0] in ['NOT']:
        search_expr = not optimade_filter_to_httk_recurse(node[1], search_variable, columns_mapper, columns_mapper, columns_handlers, recursion=recursion+1)
    elif node[0] in ['HAS_ALL', 'HAS_ANY', 'HAS_ONLY']:
        ops = node[1]
        left = node[2]
        right = node[3]
        assert(left[0] == 'Identifier')
        column = columns_mapper[left[1]]
        argtype, handler = columns_handlers[left[1]]
        values = []
        for el in right:
            assert(el[0] in constant_types)
            assert(argtype[0] == 'List')
            assert(el[0] == argtype[1])
            if argtype == "Number":
                try:
                    values += [int(el[1])]
                except ValueError:
                    values += [float(el[1])]
            else:
                values += [el[1]]
        if ops != tuple(['=']*len(values)):
            raise TranslatorError("HAS queries with non-equal operators not implemented yet.", 501, "Not implemented.")
        search_expr = handler(column, ops, values, search_variable, node[0])
    elif node[0] in ['LENGTH']:
        raise TranslatorError("LENGTH queries not implemented yet.", 501, "Not implemented.")
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
            assert(left[0] == 'Identifier')
            column = columns_mapper[left[1]]
            argtype, handler = columns_handlers[left[1]]
            assert(right[0] in constant_types)
            assert(right[0] == argtype)
            if right[0] == "Number":
                try:
                    value = int(right[1])
                except ValueError:
                    value = float(right[1])
            else:
                value = right[1]
            search_expr = handler(column, op, value, search_variable)
    else:
        pprint(node)
        raise TranslatorError("Unexpected translation error", 500, "Internal server error.")
    return search_expr


_httk_opmap = {'!=': '__ne__', '>': '__gt__', '<': '__lt__', '=': '__eq__', '<=': '__le__', '>=': '__ge__'}


def string_handler(entry, op, value, search_variable):
    httk_op = _httk_opmap[op]
    return getattr(getattr(search_variable,entry),httk_op)(value)

def number_handler(entry, op, value, search_variable):
    httk_op = _httk_opmap[op]
    return getattr(getattr(search_variable,entry),httk_op)(value)

def timestamp_handler(entry, op, value, search_variable):
    raise TranslatorError("Timestamp comparison not yet implemented.", 501, "Not implemented.")

def elements_handler(entry, ops, values, search_variable, has_type):
    if has_type == 'HAS_ALL':
        search = getattr(getattr(search_variable,entry),'is_in')(values[0])
        for value in values[1:]:
            search = search & (getattr(getattr(search_variable,entry),'is_in')(value))
    elif has_type == 'HAS_ANY':
        search = getattr(getattr(search_variable,entry),'is_in')(*values)
    elif has_type == 'HAS_ONLY':
        raise TranslatorError("HAS ONLY queries not implemented yet.", 501, "Not implemented.")

    return search

def elements_ratios_handler(entry, op, value, search_variable):
    raise TranslatorError("Elements ratios comparison not yet implemented.", 501, "Not implemented.")

def structure_features_handler(entry, op, value, search_variable):
    raise TranslatorError("Structure features comparison not yet implemented.", 501, "Not implemented.")

optimade_valid_columns_per_entry = {
    'structures': {
        'id': ('String', lambda entry, op, value, search_variable: string_handler('hexhash', op, value[1:-1], search_variable)),
        'type': ('String', string_handler),
        'immutable_id': ('String', string_handler),
        'last_modified': ('String', timestamp_handler),
        'elements': (('List','String'), elements_handler),
        'nelements': ('Number', number_handler),
        'elements_ratios': (('List','Numbers'), elements_ratios_handler),
        'chemical_formula_descriptive': ('String', string_handler),
        'chemical_formula_reduced': ('String', string_handler),
        'chemical_formula_anonymous': ('String', string_handler),
        'formula_prototype': ('String', string_handler),
        'nelements': ('Number', number_handler),
        'nsites': ('Number', number_handler),
        'structure_features': (('List','String'), structure_features_handler),
    },
    'calculations': {
        'id': ('String', string_handler),
        'modification_date': ('String', timestamp_handler),
    },
    'references': {
        'id': ('String', string_handler),
        'modification_date': ('String', timestamp_handler),
    }
}

optimade_valid_response_fields = {
    'structures': ['id', 'modification_date', 'elements',
                   'nelements', 'chemical_formula', 'formula_prototype'],
    'calculations': ['id', 'modification_date']
}

