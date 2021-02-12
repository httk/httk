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

import os, re
from pprint import pprint

from httk import miniparser
from httk.core.miniparser import ParserError, ParserSyntaxError
#import parser, build_ls, ParserError

ls = None


def parse_optimade_filter(filter_string, verbosity=0):
    # To get diagnostic output, pass argument, e.g.,: verbosity=LogVerbosity(0,parser_verbosity=5))

    parse_tree = parse_optimade_filter_raw(filter_string, verbosity)

    ojf = optimade_parse_tree_to_ojf(parse_tree)
    return ojf


def parse_optimade_filter_raw(filter_string, verbosity=0):
    global ls

    if ls is None:
        initialize_optimade_parser()

    return miniparser.parser(ls, filter_string, verbosity=verbosity)


def initialize_optimade_parser():

    global ls

    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, "optimade_filter_grammar.ebnf")) as f:
        grammar = f.read()

    # Keywords
    literals = ["AND", "NOT", "OR", "KNOWN", "UNKNOWN", "IS", "CONTAINS", "STARTS", "ENDS", "WITH", "LENGTH", "HAS", "ALL", "ONLY", "EXACTLY", "ANY"," ","\t","\n","\r"]

    # Token definitions from Appendix 3
    tokens = {
        "Operator": r'<|<=|>|>=|=|!=',
        "Identifier": "[a-z_][a-z_0-9]*",
        "String": r'"[^"\\]*(?:\\.[^"\\]*)*"',
        "Number": r"[-+]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][-+]?[0-9]+)?",
        "OpeningBrace": r"\(",
        "ClosingBrace": r"\)",
        "Dot": r'\.',
        "Colon": r":",
        "Comma": r","
    }
    partial_tokens = {
        "Number": r"[-+]?[0-9]+\.?[0-9]*[eE]?[-+]?[0-9]*"
    }
    # We don't need these, because they are handled on higher level
    # by the token definitions.
    skip = [
        "EscapedChar", "UnescapedChar", "Punctuator", "Exponent", "Sign",
        "Digits", "Digit", "Letter", "Operator", "UppercaseLetter", "LowercaseLetter", "OpeningBrace", "Dot", "ClosingBrace", "Comma", "Colon"
    ]

    ls = miniparser.build_ls(ebnf_grammar=grammar, start='Filter', ignore=' \t\n',
                  tokens=tokens, partial_tokens=partial_tokens, literals=literals, verbosity=0, skip=skip,
                  remove=[')', '('], simplify=[])  # , simplify=['Term', 'Atom', 'Expression'])

    return ls


def optimade_parse_tree_to_ojf(ast):

    assert(ast[0] == 'Filter')
    return optimade_parse_tree_to_ojf_recurse(ast[1])


def _fix_const(node):
    if node[0] == 'Property':
        assert(node[1][0]=='Identifier')
        return node[1]
    elif node[0] == 'String':
        assert(node[1][-1]=='"')
        assert(node[1][0]=='"')
        return ('String', node[1][1:-1])
    else:
        return node

def optimade_parse_tree_to_ojf_recurse(node, recursion=0):

    tree = [None]
    pos = tree
    arg = 0

    if node[0] in ['Expression', 'ExpressionClause', 'ExpressionPhrase', 'Comparison']:
        n = node[1:]
        if n[0][0] == "NOT":
            assert(arg is not None)
            pos[arg] = ['NOT', None]
            pos = pos[arg]
            arg = 1
            n = list(n)[1:]
        for nn in n:
            if nn[0] in ['Expression', 'ExpressionClause', 'ExpressionPhrase', 'PropertyFirstComparison', 'ConstantFirstComparison', 'PredicateComparison', 'Comparison']:
                assert(arg is not None and pos[arg] is None)
                pos[arg] = optimade_parse_tree_to_ojf_recurse(nn, recursion=recursion+1)
            elif nn[0] in ["AND", "OR"]:
                assert(arg is not None and pos[arg] is not None)
                pos[arg] = [nn[0], tuple(pos[arg]), None]
                pos = pos[arg]
                arg = 2
            elif nn[0] in ["OpeningBrace", "ClosingBrace"]:
                pass
            else:
                pprint(nn)
                raise Exception("Internal error: filter simplify on invalid ast: "+str(nn[0]))
    elif node[0] in ['PropertyFirstComparison', 'ConstantFirstComparison'] :
        assert(arg is not None and pos[arg] is None)

        if node[0] == 'PropertyFirstComparison':
            assert(node[1][0] == 'Property')
            left = ('Identifier',) + tuple([x[1] for x in node[1][1:] if x[0] != 'Dot'])
            #assert(node[1][1][0] == 'Identifier')
            #left = node[1]
        elif node[0] == 'ConstantFirstComparison':
            assert(node[1][0] == 'Constant')
            left = _fix_const(node[1][1])
        else:
            raise Exception("Internal error: filter simplify on invalid ast, unrecognized comparison: "+str(node[0]))
        if node[2][0] == "ValueOpRhs":
            assert(node[2][1][0] == 'Operator')
            op = node[2][1][1]
            assert(node[2][2][0] == 'Value')
            right = _fix_const(node[2][2][1])
            pos[arg] = (op, left, right)
            arg = None
        elif node[2][0] == "FuzzyStringOpRhs":
            assert(node[2][1][0] in ['CONTAINS', 'STARTS', 'ENDS'])
            op = node[2][1][1]
            if node[2][1][0] in ['STARTS', 'ENDS'] and node[2][2][0] == "WITH":
                right = node[2][3]
            else:
                right = node[2][2]
            assert(right[0] == 'Value' or right[0] == 'Property')
            if right[0] == 'Value':
                right = _fix_const(right[1])
            pos[arg] = (op, left, right)
            arg = None
        elif node[2][0] == "KnownOpRhs":
            assert(node[2][1][0] == 'IS')
            op = node[2][1][1]
            assert(node[2][2][0] in ['KNOWN','UNKNOWN'])
            op += "_" + node[2][2][0]
            assert(node[1][0] == 'Property')
            operand = ('Identifier',) + tuple([x[1] for x in node[1][1:] if x[0] != 'Dot'])
            pos[arg] = (op, operand)
            arg = None
        elif node[2][0] == "SetOpRhs":
            assert(node[2][1][0] == 'HAS')
            if node[2][2][0] == 'Operator':
                assert(len(node[2]) == 4)
                op = "HAS"
                inop = node[2][2][1]
                right = node[2][3][1]
                pos[arg] = (op, (inop,), left, (right,))
            elif len(node[2]) == 3:
                op = "HAS_ALL"
                assert(node[2][2][0] == 'Value')
                right = _fix_const(node[2][2][1])
                pos[arg] = (op, ('=',), left, (right,))
            elif len(node[2]) == 4:
                assert(node[2][2][0] in ['ONLY', 'ALL', 'EXACTLY', 'ANY'])
                assert(node[2][3][0] == 'ValueList')
                #if 'Operator' in [x[0] for x in node[2][3][1:]]:
                op = "HAS_"+node[2][2][0]
                inop = None
                right = []
                inops = []
                for x in node[2][3][1:]:
                    if x[0] == 'Operator':
                        assert(inop is None)
                        inop = x[1]
                    elif x[0] == 'Value':
                        inops += [('=' if inop is None else inop)]
                        right += [_fix_const(x[1])]
                        inop = None
                pos[arg] = (op, tuple(inops), left, tuple(right))
                #else:
                #    op = "HAS_"+node[2][2][0]
                #    right = tuple(_fix_const(x[1]) for x in node[2][3][1::2])
                #    pos[arg] = (op, left, right)
            else:
                raise Exception("Internal error: filter simplify on invalid ast, unexpected number of components in set op: "+str(node[2]))
            arg = None
        elif node[2][0] == "SetZipOpRhs":
            assert(node[2][1][0] == 'IdentifierZipAddon')
            left = (left,) + node[2][1][2::2]
            nzip = len(left)
            assert(node[2][2][0] == 'HAS')
            if len(node[2]) == 4:
                assert(node[2][3][0] == 'ValueZip')
                #if 'Operator' in [x[0] for x in node[2][3][1::2]]:
                op = "HAS_ZIP"
                inop = None
                inops = []
                right = []
                for x in node[2][3][1:]:
                    if x[0] == 'Operator':
                        assert(inop is None)
                        inop = x[1]
                    elif x[0] == 'Value':
                        right += [_fix_const(x[1])]
                        inops += [('=' if inop is None else inop)]
                        inop = None
                pos[arg] = (op, tuple(inops), left, tuple(right))
                #else:
                #    op = "HAS_ZIP"
                #    assert(node[2][3][1][0] == 'Value')
                #    right = tuple(_fix_const(x[1]) for x in node[2][3][1::2])
                #    if not nzip==len(right):
                #        raise ParserError("Parser context error: set zip operation with mismatching number of components for:"+str(right)+" lhs:"+str(nzip)+" rhs:"+str(right))
                #    pos[arg] = (op, left, right)

            elif len(node[2]) == 5:
                assert(node[2][3][0] in ['ONLY', 'ALL', 'EXACTLY', 'ANY'])
                assert(node[2][4][0] == 'ValueZipList')
                #if 'Operator' in [x[0] for y in node[2][4][1::2] for x in y[1:]]:
                op = "HAS_ZIP_"+node[2][3][0]
                inops = []
                right = []
                for y in node[2][4][1::2]:
                    inop = None
                    inops += [[]]
                    right += [[]]
                    for x in y[1:]:
                        if x[0] == 'Operator':
                            assert(inop is None)
                            inop = x[1]
                        elif x[0] == 'Value':
                            right[-1] += [_fix_const(x[1])]
                            inops[-1] += [('=' if inop is None else inop)]
                            inop = None
                    inops[-1] = tuple(inops[-1])
                    right[-1] = tuple(right[-1])
                pos[arg] = (op, tuple(inops), left, tuple(right))
                #else:
                #    assert(node[2][3][0] in ['ONLY', 'ALL', 'EXACTLY', 'ANY'])
                #    op = "HAS_ZIP_"+node[2][3][0]
                #    assert(node[2][4][0] == 'ValueZipList')
                #    right = tuple(tuple(_fix_const(y[1]) for y in x[1::2]) for x in node[2][4][1::2])
                #    if not all(nzip==len(x) for x in right):
                #        raise ParserError("Parser context error: set zip operation with mismatching number of components for:"+str(right)+" lhs:"+str(nzip)+" rhs:"+str([len(x) for x in right]))
                #    pos[arg] = (op, left, right)
            else:
                raise Exception("Internal error: filter simplify on invalid ast, unexpected number of components in set op: "+str(node[2]))
            arg = None
        elif node[2][0] == "LengthOpRhs":
            assert(node[2][1][0] == 'LENGTH')
            assert(node[2][2][0] == 'Value' or (node[2][2][0] == 'Operator' and node[2][3][0] == 'Value'))
            if node[2][2][0] == 'Value':
                right = _fix_const(node[2][2][1])
                op = '='
            else:
                op = node[2][2][1]
                right = _fix_const(node[2][3][1])
            pos[arg] = ("LENGTH", left, op, right)
            #left = ('Identifier',) + tuple([x[1] for x in node[1][1:] if x[0] != 'Dot'])
            #assert(node[2][2][0] == 'Value' or (node[2][2][0] == 'Operator' and node[3][2][0] == 'Value'))
            #right = _fix_const(node[2][2][1])
            #pos[arg] = ("LENGTH", op, left, right)
            #arg = None
        else:
            raise Exception("Internal error: filter simplify on invalid ast, unrecognized comparison: "+str(node[2][0]))
    #elif node[0] == 'PredicateComparison':
    #    if node[1][0] == "LengthComparison":
    #        assert(node[1][1][0]=="LENGTH")
    #        assert(node[1][2][0]=="Identifier")
    #        assert(node[1][3][0]=="Operator")
    #        assert(node[1][4][0]=="Value")
    #        left = node[1][2]
    #        right = _fix_const(node[1][4][1])
    #        op = node[1][3][1]
    #        pos[arg] = ("LENGTH", op, left, right)
    #        arg = None
    #    else:
    #        raise Exception("Internal error: filter simplify on invalid ast, unrecognized predicate comparison: "+str(node[1][0]))
    else:
        raise Exception("Internal error: filter simplify on invalid ast, unrecognized node: "+str(node[0]))

    assert(arg is None or pos[arg] is not None)
    return tuple(tree[0])


if __name__ == "__main__":

    import os, sys
    from pprint import pprint

    if len(sys.argv) >= 2:
        input_string = sys.argv[1]
    else:
        input_string ='elements HAS ALL "Ga","Ti" AND (nelements=3 OR nelements=2)'

    filter_ast = parse_optimade_filter(input_string, verbosity=0)

    sys.stdout.write("==== FILTER STRING PARSE RESULT:\n")
    pprint(filter_ast)
    sys.stdout.write("====\n")
