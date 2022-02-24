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
import re, operator
from pprint import pprint

from httk.optimade.error import TranslatorError
from httk.optimade.httk_entries import httk_entry_info, httk_recognized_prefixes

from httk.atomistic import Structure
from httk.atomistic.results import Result_TotalEnergyResult
from httk.atomistic.results.elasticresult import Result_ElasticResult

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
    elif fulltype == 'unknown':
        return val[1]
    raise TranslatorError("Type mismatch in filter, expected:"+fulltype+", query has:"+val[0], 400, "Bad request")

constant_types = ['String','Number']

table_mapper = {
    'structures': Structure,
    # 'calculations': Result_TotalEnergyResult,
    'calculations': Result_ElasticResult,
}

invert_op = {'!=': '!=', '>':'<', '<':'>', '=':'=', '<=': '>=', '>=': '<='}
_python_opmap = {'!=': '__ne__', '>': '__gt__', '<': '__lt__', '=': '__eq__', '<=': '__le__', '>=': '__ge__', 'STARTS':'startswith','ENDS':'endswith'}

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
        if left[1] not in entry_info:
            if left[1].startswith(httk_recognized_prefixes):
                raise TranslatorError("Filter invokes unrecognized property name: "+left[1], 400, "Bad request")
            else:
                #TODO: this should warn
                handler = unknown_has_handler
                values = format_value('list of unknown',right)
        else:
            values = format_value(entry_info[left[1]]['fulltype'],right)
            handler = handlers[left[1]]['HAS']
        if ops != tuple(['=']*len(values)):
            raise TranslatorError("HAS queries with non-equal operators not implemented yet.", 501, "Not implemented")
        search_expr, needs_post = handler(left[1], ops, values, search_variable, node[0], inv_toggle)
    elif node[0] in ['LENGTH']:
        left = node[1]
        op = node[2]
        right = node[3]
        assert(left[0] == 'Identifier')
        if right[0] == 'Identifier':
            raise TranslatorError("LENGTH comparisons with non-constant right hand side not implemented.", 501, "Not implemented")
        if right[0] != 'Number':
            raise TranslatorError("LENGTH comparison can only be done with Numbers. Unexpected right hand side type:"+right[0], 501, "Not implemented")
        if left[1] not in entry_info:
            if left[1].startswith(httk_recognized_prefixes):
                raise TranslatorError("Filter invokes unrecognized property name: "+left[1], 400, "Bad request")
            else:
                #TODO: this should warn
                handler = unknown_length_handler
                values = format_value('list of unknown',right)
        else:
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
            if left[1] not in entry_info:
                if left[1].startswith(httk_recognized_prefixes):
                    raise TranslatorError("Filter invokes unrecognized property name: "+left[1], 400, "Bad request")
                else:
                    #TODO: this should warn
                    handler = unknown_comparison_handler
                    value = format_value('unknown',right)
            else:
                handler = handlers[left[1]]['comparison']
                value = format_value(entry_info[left[1]]['fulltype'],right)
            search_expr = handler(left[1], op, value, search_variable)
    elif node[0] in ['ENDS', 'STARTS', 'CONTAINS']:
        op = node[0]
        left = node[1]
        right = node[2]
        assert(left[0] == 'Identifier')
        if right[0] == 'Identifier':
            raise TranslatorError("Identifier vs. Identifier string comparisons not implemented.", 501, "Not implemented")
        if left[1] not in entry_info:
            if left[1].startswith(httk_recognized_prefixes):
                raise TranslatorError("Filter invokes unrecognized property name: "+left[1], 400, "Bad request")
            else:
                #TODO: this should warn
                handler = unknown_stringmatching_handler
                values = format_value('unknown',right)
        else:
            handler = handlers[left[1]]['stringmatching']
            value = format_value(entry_info[left[1]]['fulltype'],right)
        search_expr = handler(left[1], value, node[0], search_variable)
    elif node[0] in ['IS_UNKNOWN', 'IS_KNOWN']:
        left = node[1]
        assert(left[0] == 'Identifier')
        if left[1] not in entry_info:
            if left[1].startswith(httk_recognized_prefixes):
                raise TranslatorError("Filter invokes unrecognized property name: "+left[1], 400, "Bad request")
            else:
                #TODO: this should warn
                handler = unknown_unknown_handler
        else:
            handler = handlers[left[1]]['unknown']
        search_expr = handler(left[1], search_variable, node[0])
    else:
        pprint(node)
        raise TranslatorError("Unexpected translation error at: "+str(node[0]), 500, "Internal server error.")
    assert(search_expr is not None)
    return search_expr, needs_post

def true_handler(search_variable):
    return getattr(getattr(search_variable,'hexhash'),'__eq__')(getattr(search_variable,'hexhash'))

def false_handler(search_variable):
    return getattr(getattr(search_variable,'hexhash'),'__ne__')(getattr(search_variable,'hexhash'))

def unknown_unknown_handler(entry, search_variable, unknown_type):
    if unknown_type=='IS_UNKNOWN':
        return true_handler(search_variable)
    elif unknown_type=='IS_KNOWN':
        return false_handler(search_variable)
    raise TranslatorError("Unexpected unknown operator type", 500, "Internal server error.")

def known_unknown_handler(entry, search_variable, unknown_type):
    if unknown_type=='IS_UNKNOWN':
        return false_handler(search_variable)
    elif unknown_type=='IS_KNOWN':
        return true_handler(search_variable)
    raise TranslatorError("Unexpected unknown operator type", 500, "Internal server error.")

def unknown_comparison_handler(entry, ops, values, search_variable):
    return false_handler(search_variable)

def unknown_stringmatching_handler(entry, values, stringmatching_type, search_variable):
    return false_handler(search_variable)

def unknown_has_handler(entry, op, value, search_variable, has_type, inv_toggle):
    return false_handler(search_variable)

def unknown_length_handler(entry, op, value, search_variable):
    return false_handler(search_variable)

def string_handler(entry, op, value, search_variable):
    httk_op = _python_opmap[op]
    return getattr(getattr(search_variable,entry),httk_op)(value)

def stringmatching_handler(entry, value, stringmatching_type, search_variable):
    escaped_value = value.replace("\\","\\\\").replace("%","\\%").replace("_","\\_")
    if stringmatching_type == 'ENDS':
        return getattr(getattr(search_variable,entry),'like')('%'+escaped_value)
    elif stringmatching_type == 'STARTS':
        return getattr(getattr(search_variable,entry),'like')(escaped_value+'%')
    elif stringmatching_type == 'CONTAINS':
        return getattr(getattr(search_variable,entry),'like')('%'+escaped_value+'%')
    else:
        raise TranslatorError("Unexpected stringmatching operator type", 500, "Internal server error.")

def constant_comparison_handler(val1, op, val2, search_variable):
    op = _python_opmap[op]
    if getattr(operator,op)(val1,val2):
        return true_handler(search_variable)
    else:
        return false_handler(search_variable)

def constant_stringmatching_handler(val1, op, val2, stringmatching_type, search_variable):
    op = _python_opmap[op]
    if getattr(val1,op)(val2):
        return true_handler(search_variable)
    else:
        return false_handler(search_variable)

def number_handler(entry, op, value, search_variable):
    httk_op = _python_opmap[op]
    return getattr(getattr(search_variable,entry),httk_op)(value)

def timestamp_handler(entry, op, value, search_variable):
    raise TranslatorError("Timestamp comparison not yet implemented.", 501, "Not implemented.")

def set_handler(entry, ops, values, inv, has_type, search_variable):
    if has_type == 'HAS_ALL':
        if not inv:
            search = getattr(getattr(search_variable,entry),'has_any')(values[0])
            for value in values[1:]:
                search = search & (getattr(getattr(search_variable,entry),'has_any')(value))
            return search, False
        else:
            search = getattr(getattr(search_variable,entry),'has_inv_any')(values[0])
            for value in values[1:]:
                search = search & (getattr(getattr(search_variable,entry),'has_inv_any')(value))
            return search, True
    elif has_type == 'HAS_ANY':
        if not inv:
            return getattr(getattr(search_variable,entry),'has_any')(*values), False
        else:
            return getattr(getattr(search_variable,entry),'has_inv_any')(*values), True
    elif has_type == 'HAS_ONLY':
        if not inv:
            return getattr(getattr(search_variable,entry),'has_only')(*values), True
        else:
            return getattr(getattr(search_variable,entry),'has_inv_only')(*values), True

def constant_set_handler(val1, ops, val2, has_type, inv, search_variable):
    if has_type == 'HAS_ALL':
        if (set(val2) <= set(val1)):
            return true_handler(search_variable), False
        else:
            return false_handler(search_variable), False
    elif has_type == 'HAS_ANY':
        if set(val2).isdisjoint(val1):
            return false_handler(search_variable), False
        else:
            return true_handler(search_variable), False
    elif has_type == 'HAS_ONLY':
        if (set(val1) <= set(val2)):
            return true_handler(search_variable), False
        else:
            return false_handler(search_variable), False

def structure_features_set_handler(values, ops, inv, has_type, search_variable):
    # Any HAS ANY, HAS ALL, HAS ONLY operation will check for precense of an identifier in structure_features.
    # For now we don't support any structure features, hence, all such comparisons return False
    return getattr(getattr(search_variable,'hexhash'),'__ne__')(getattr(search_variable,'hexhash')), False

def structure_features_length_handler(op, value, search_variable):
    # structure_features is assumed to always be empty
    if value == 0:
        return getattr(getattr(search_variable,'hexhash'),'__eq__')(getattr(search_variable,'hexhash'))
    else:
        return getattr(getattr(search_variable,'hexhash'),'__ne__')(getattr(search_variable,'hexhash'))

optimade_field_handlers = {
    'structures': {
        'id': {
            'comparison': lambda entry, op, value, search_variable: string_handler('__id', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
            'stringmatching': lambda entry, value, stringmatching_type, search_variable: stringmatching_handler('__id', value, stringmatching_type, search_variable)
        },
        'type': {
            'comparison': lambda entry, op, value, search_variable: constant_comparison_handler(value, op, 'structures', search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
            'stringmatching': lambda entry, value, stringmatching_type, search_variable: constant_stringmatching_handler(value, 'structures', stringmatching_type, search_variable)
        },
        'elements': {
            'HAS': lambda entry, ops, values, search_variable, has_type, inv: set_handler('formula_symbols', ops, values, inv, has_type, search_variable),
            'length': lambda entry, op, value, search_variable: number_handler('number_of_elements', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
        },
        'nelements': {
            'comparison': lambda entry, op, value, search_variable: number_handler('number_of_elements', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
        },
        'nperiodic_dimensions': {
            'comparison': lambda entry, op, value, search_variable: constant_comparison_handler(value, op, 3, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
        },
        'dimension_types': {
            'HAS': lambda entry, ops, values, search_variable, has_type, inv: constant_set_handler(values, ops, [1, 1, 1], has_type, inv, search_variable),
            'length': lambda entry, op, value, search_variable: constant_comparison_handler(value, op, 3, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
        },
        'chemical_formula_descriptive': {
            'comparison': lambda entry, op, value, search_variable: string_handler('formula', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
            'stringmatching': lambda entry, value, stringmatching_type, search_variable: stringmatching_handler('formula', value, stringmatching_type, search_variable)
        },
        'structure_features': {
            'HAS': lambda entry, ops, values, search_variable, has_type, inv: structure_features_set_handler(values, ops, inv, has_type, search_variable),
            'length': lambda entry, op, value, search_variable: structure_features_length_handler(op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
        },

        # These have been added by hpleva:
        # TODO: The 'comparison' etc. do not match the property, e.g. 'nsites', they have just been copy-pasted from above.
        'nsites': {
            'comparison': lambda entry, op, value, search_variable: number_handler('number_of_elements', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
        },
        'species_at_sites': {
            'comparison': lambda entry, op, value, search_variable: number_handler('number_of_elements', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
        },
        'cartesian_site_positions': {
            'comparison': lambda entry, op, value, search_variable: number_handler('number_of_elements', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
        },
        'chemical_formula_anonymous': {
            'comparison': lambda entry, op, value, search_variable: string_handler('anonymous_formula', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
            'stringmatching': lambda entry, value, stringmatching_type, search_variable: stringmatching_handler('anonymous_formula', value, stringmatching_type, search_variable)
        },
        'chemical_formula_reduced': {
            'comparison': lambda entry, op, value, search_variable: string_handler('formula', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
            'stringmatching': lambda entry, value, stringmatching_type, search_variable: stringmatching_handler('formula', value, stringmatching_type, search_variable)
        },
    },
    'calculations': {
        'id': {
            'comparison': lambda entry, op, value, search_variable: string_handler('__id', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
            'stringmatching': lambda entry, value, stringmatching_type, search_variable: stringmatching_handler('__id', value, stringmatching_type, search_variable)
        },
        'type': {
            'comparison': lambda entry, op, value, search_variable: constant_comparison_handler(value, op, 'calculations', search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
            'stringmatching': lambda entry, value, stringmatching_type, search_variable: constant_stringmatching_handler(value, 'calculations', stringmatching_type, search_variable)
        },
        '_httk_total_energy': {
            'comparison': lambda entry, op, value, search_variable: number_handler('total_energy', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
        },
        '_httk_structure_id': {
            'comparison': lambda entry, op, value, search_variable: string_handler('structure_Structure_sid', op, value, search_variable),
            'unknown': lambda entry, search_variable, unknown_type: known_unknown_handler(entry, search_variable, unknown_type),
            'stringmatching': lambda entry, value, stringmatching_type, search_variable: stringmatching_handler('structure_Structure_sid', value, stringmatching_type, search_variable)
        },
    }
}
