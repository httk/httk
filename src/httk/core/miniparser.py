#!/usr/bin/env python
#
# Copyright 2019 Rickard Armiento
#
# This file, miniparser.py, originates from the
# high-throughput toolkit (httk) [http://httk.org] which is licensed
# under the GNU AFFERO GENERAL PUBLIC LICENSE version 3 or later.
# However, this specific file were isolated and granted a more
# permissive license to help implementing parsers in other projects.
# (But please contribute updates and report bugs to the httk version,
# found via http://httk.org.)
#
# The license terms for this file is given below. 
#
# -------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------

'''
================
LR(1) miniparser
================

Introduction
------------

A relatively bare-bones LR(1) parser that parses strings into abstract 
syntax trees (ast) for generic languages. Python 2 and 3 compatible. 
Language grammars can be given in textual EBNF. 

A simple usage example::

    from miniparser import parser

    ls = {
      'ebnf_grammar': """
         S = E ;
         E = T, '+', E ;
         E = T ;
         T = id ;    
      """,
      'tokens': {'id': '[a-zA-Z][a-zA-Z0-9_]*'}
    }

    input_string = "Test + Test"

    result = parser(ls, input_string)
    print(result)

Usage example of a simple grammar for balanced parentheses. This
also shows using inline regex via an EBNF special sequence::
 
    from miniparser import parser
    ls = {
      'ebnf_grammar': """
         Expr = Group 
              | Expr , Expr 
              | id ;
         Group = '(', Expr, ')' ;
         id = ? [a-zA-Z0-9 _]+ ? ;
      """,
      'remove': ['(',')'],
      'simplify': ['Expr']
    }

    input_string = "Outer ( Inner ( Inside ) Further outside )"

    result = parser(ls, input_string)
    print(result)

Note: in the above examples, the parse tables are generated on the
first call to parse, and then cached inside the 'ls' dict. 
However, if one wants to pre-generate the parse tables (e.g., for
looking at them), that can be done by calling build_ls(ls=ls) 
before parse. You can, if you want, save the 'ls' variable to disk
(e.g. using pickle). However, since a modern computer builds the parse 
tables in a time comparable with starting up the python interpreter,
this may not be so useful.

For documentation on the parameters in the ls dict, see help(build_ls).


Detailed description
--------------------

This is roughly how the parser operates:

1. It takes as input:

   1.1. An EBNF grammar in text format for the language it is
        supposed to parse: `ebnf_grammar`.

   1.2. Some other meta-info about the language that defines, e.g.,
      terminals (elements that are not further simplified), etc.

   1.3. A string to parse.

2. The fist time this langague is parsed, the parser builds up the 
   necessary data structures for the language using the function 
   `build_ls`. The steps are:

   2.1. The parser uses itself to parse `ebnf_grammar` into
        an ast representation of the grammar: `ebnf_grammar_ast`.

        To do this, it uses an already provided ast of the EBNF
        language itself (but which can also be recreated by the parser
        itself as shown in the examples at the end of the file under
        __name__ == "__main__".)

   2.2. The `ebnf_grammar_ast` is translated to a more BNF-like abstract
        form that expands alteration, optionals, groupings, and
        repetitions into separate rules: `bnf_grammar_ast`.

   2.3. The `bnf_grammar_ast` is processed into a `rule_table`. 
        This is a dictionary that maps every symbol to a list of
        possible right hand sides in the production rules.

   2.4. The `rule_table` is used to build a table of the FIRST(symbol)
        function in LR parsing.  It maps all symbols on a list of
        terminals that may be the very first thing seen in the input
        when matching that production rule: `first_table`.

   2.5. The `rule_table`and the `first_table` are used to build
        the ACTION and GOTO tables in LR parsing. These encode
        a state machine that for every starting state S tells
        the machine to either shift or reduce, and when doing so,
        the state the machine progresses to: `action_table` and
        `goto_table`.

3. The parse string is processed the python generator `lexer`, 
   which splits the input into lexical tokens.

4. The LR state machine is initialized in its starting state.  Tokens
   are read from the lexer, and shift/reduce actions and state changes
   are made according to `action_table` and `goto_table`. The results
   of the parsing are collected on the symbol stack in the from of an ast. 
    
5. When all input has been reduced into the starting symbol, the 
   ast connected to that symbol is returned.


Diagnostic output
-----------------

- You can add verbosity=<int> as an argument to both the `parser` and the `build_ls`
  function to get that level of diagnostic output.

- For more fine-tuned output, set verbosity = LogVerbosity(verbosity, [<flags>])
  flags can be various flags that can be found in the source code.

  Known flags at the time of writing: 

  - `print_all_tokens=True` lets makes the parser have the lexer process 
    all input first and prints all tokens before the parsing starts.

  - `<function name>_verbosity = <verbosity level>` adjusts the verbosity level 
    for just that one function. For example:
  
      parser(ls, source, verbosity=LogVerbosity(0,parser_verbosity=3))

  prints out diagnostic output on level 3 for the parser function, but
  skips any other diagnostic output.

- If you do not want the default behavior of printing diagnostic output on stdout, 
  both parser and build_ls takes the argument logger=<function>, which redirects
  all diagnostic output to that function. The function should have the signature: 

      logger(*args,**kargs):    

  where the args is the diagnostic info being printed, and the keyword arguments
  communicates flags. In particular, pretty=True indicates that complex objects 
  are passed which would benefit from using, e.g., pprint.pprint to typeset the output.
'''

import sys, re, pprint, itertools

#### The hard-coded language definition we use to parse grammars given in EBNF

ls_ebnf = {

    'ebnf_grammar': """
        Optional = "[" , Rhs , "]" ;
        Repetition = "{" , Rhs , "}" ;
        Grouping = "(" , Rhs , ")" ;
        Alteration = Rhs , "|" , Rhs ;
        Concatenation = Rhs , "," , Rhs ;

        Rhs = identifier 
             | terminal 
             | special
             | Optional
             | Repetition
             | Grouping
             | Alteration
             | Concatenation ;

        Rule = identifier , "=" , Rhs , ";" ;
        Grammar = { Rule } ;
    """,

    'start': 'Grammar',
    'ignore': ' \t\n',
    'comment_markers': [('(*', '*)')],
    'literals': ['[', ']', '{', '}', '(', ')', '|', ',', ';', '='],
    'precedence': (('left', '|'), ('left', ',')),
    'tokens': {'identifier': '[a-zA-Z][a-zA-Z0-9_]*',
               'terminal': r'"([^\\"]|.)*"|' + r"'([^\\']|.)*'",
               #'terminal': r'"([^\\"]|\\.)*"|' + r"'([^\\']|\\.)*'",
               'special': r'\?[^?]*\?'},
    'simplify': ['Rhs'],
    'remove': ['[', ']', '{', '}', '(', ')', '|', ',', ';', '='],
    'aggregate': ['Grammar', 'Alteration', 'Concatenation'],

    'ebnf_grammar_ast': ('Grammar',
                         ('Rule', ('identifier', 'Optional'), ('Concatenation', ('terminal', '"["'), ('identifier', 'Rhs'), ('terminal', '"]"'))),
                         ('Rule', ('identifier', 'Repetition'), ('Concatenation', ('terminal', '"{"'), ('identifier', 'Rhs'), ('terminal', '"}"'))),
                         ('Rule', ('identifier', 'Grouping'), ('Concatenation', ('terminal', '"("'), ('identifier', 'Rhs'), ('terminal', '")"'))),
                         ('Rule', ('identifier', 'Alteration'), ('Concatenation', ('identifier', 'Rhs'), ('terminal', '"|"'), ('identifier', 'Rhs'))),
                         ('Rule', ('identifier', 'Concatenation'), ('Concatenation', ('identifier', 'Rhs'), ('terminal', '","'), ('identifier', 'Rhs'))),
                         ('Rule', ('identifier', 'Rhs'), ('Alteration', ('identifier', 'identifier'), ('identifier', 'terminal'), ('identifier', 'special'),
                                                          ('identifier', 'Optional'), ('identifier', 'Repetition'), ('identifier', 'Grouping'),
                                                          ('identifier', 'Alteration'), ('identifier', 'Concatenation'))),
                         ('Rule', ('identifier', 'Rule'), ('Concatenation', ('identifier', 'identifier'), ('terminal', '"="'),
                                                           ('identifier', 'Rhs'), ('terminal', '";"'))),
                         ('Rule', ('identifier', 'Grammar'), ('Repetition', ('identifier', 'Rule'))))
}


#### Custom Exceptions

class ParserError(Exception):
    pass


class ParserGrammarError(ParserError):
    pass


class ParserInternalError(ParserError):
    pass


class ParserSyntaxError(ParserError):
    def __init__(self, *args):
        super(ParserError, self).__init__(args[0])
        self.info = args[1]
        self.line = args[2]
        self.pos = args[3]
        self.linestr = args[4]
    pass


#### Helpers to assist logging and debugging

def logger(*args, **kargs):
    """
    This is the default logging function for diagnostic output. It
    prints the output in `args` on stdout.

    Args:
      loglevel: the level designated to the diagnostic output
      args: list of arguments to print out
      kargs: keyword flags. These are:
                pretty=True: formats the output using pprint.pprint(arg).
    """
    if 'pretty' in kargs:
        pretty = kargs['pretty']
    else:
        pretty = False

    for i in range(len(args)):
        if pretty:
            pprint.pprint(args[i])
        else:
            if i > 0:
                sys.stdout.write(" ")
            sys.stdout.write(str(args[i]))
    if not pretty:
        sys.stdout.write("\n")
    sys.stdout.flush()

# Verbosity can be given as just an intger, or as
# an instance of the class below, which allows
# sending verbosity flags.


class LogVerbosity(object):
    """
    Class to send in as keyword argument for verbosity to fine-tune 
    diagnostic output from certain functions.

    Set the keyword argument as follows::

         verbosity = LogVerbosity(verbosity, [<flags>])

    flags can be various flags that can be found in the source code, e.g., 
    `print_all_tokens=True` lets makes the parser have the lexer process 
    all input first and prints all tokens before the parsing starts.

    Specifically, set `<function name>_verbosity = <verbosity level>`
    to adjust the verbosity level for just that one function. For example::

        parser(ls, source, verbosity=LogVerbosity(0,parser_verbosity=3))

    prints out diagnostic output on level 3 for the parser function, but
    skips any other diagnostic output.
    """

    def __init__(self, verbosity, **flags):
        """
        Create LogVerbosity object. 

        Args:
          verbosity(int): main verbosity level to display
          flags: keywords to adjust output of diagnostic information
              (see help(LogVerbosity) for more info.)
        """
        self.verbosity = verbosity
        self.flags = flags
        for flag in flags:
            setattr(self, flag, flags[flag])

    def _get_verbosity(self, caller):
        if hasattr(self, caller+"_verbosity"):
            return getattr(self, caller+"_verbosity")
        else:
            return self.verbosity

    def __gt__(self, other):
        return self._get_verbosity(sys._getframe(1).f_code.co_name) > other

    def __ge__(self, other):
        return self._get_verbosity(sys._getframe(1).f_code.co_name) >= other

    def __lt__(self, other):
        return self._get_verbosity(sys._getframe(1).f_code.co_name) < other

    def __le__(self, other):
        return self._get_verbosity(sys._getframe(1).f_code.co_name) <= other    

    def __eq__(self, other):
        return self._get_verbosity(sys._getframe(1).f_code.co_name) == other

    def __sub__(self, other):
        return self(self.verbosity - other, **self.flags)

#### Main functions


def parser(ls, source, verbosity=0, logger=logger):
    """
    This is a fairly straightforward implementation of an LR(1) parser.
    It should do well for parsing somewhat simple grammars.

    The parser takes a language specification (ls), 
    and a string to parse (source). The string is then parsed according 
    to that ls into a syntax tree, which is returned.

    An ls is produced by calling the function `build_ls` (see help(build_ls))

    Args:
      ls: language specification produced by build_ls.
      source: source string to parse.
    """
    if 'parse_table' not in ls:
        build_ls(ls=ls, verbosity=verbosity, logger=logger)

    tokens = lexer(source, ls['tokens'], ls['partial_tokens'], ls['literals'], ls['ignore'], ls['comment_markers'], verbosity=verbosity, logger=logger)    

    if hasattr(verbosity, 'print_all_tokens') and verbosity.print_all_tokens == True:
        tokens = list(tokens)
        logger("==== TOKENS")
        logger(tokens, pretty=True)
        logger("====")
        tokens = iter(tokens)

    action_table = ls['parse_table']['action']
    goto_table = ls['parse_table']['goto']
    symbol_stack = []
    state_stack = [1]
    symbol, inp, pos = next(tokens)

    while True:
        if verbosity >= 3:
            logger("STATE", state_stack[-1], symbol, loglevel=1)
        if verbosity == 4:
            logger("SYMBOL STACK:", " ".join([repr(x[0]) for x in symbol_stack]), ".", symbol, loglevel=2)
        elif verbosity >= 5:
            logger("SYMBOL STACK:", loglevel=3)
            logger(symbol_stack, pretty=True, loglevel=3)
        if symbol in action_table[state_stack[-1]]:
            action, arg = action_table[state_stack[-1]][symbol]
        else:
            if symbol is None:
                raise ParserSyntaxError("Parser syntax error: unexpected end of input at line: " +
                                        str(pos[0])+", pos: "+str(pos[1])+":\n"+str(pos[2])+"\n"+(" "*(pos[1]-1))+"^",
                                        "unexpected end of input", pos[0], pos[1], pos[2])
            else:
                raise ParserSyntaxError("Parser syntax error: unexpected <"+str(symbol)+"> at line: " +
                                        str(pos[0])+", pos: "+str(pos[1])+":\n"+str(pos[2])+"\n"+(" "*(pos[1]-1))+"^",
                                        "unexpected symbol", pos[0], pos[1], pos[2])
        if action == 'shift':
            if verbosity >= 3:
                logger("PARSE ACTION SHIFT", arg, loglevel=1)
            if symbol is None:
                raise ParserSyntaxError("Parser syntax error: Unexpected end of input at line: "+str(pos[0])+", pos: " +
                                        str(pos[1])+":\n"+str(pos[2])+"\n"+(" "*(pos[1]-1))+"^",
                                        "unexpected end of input", pos[0], pos[1], pos[2])
            symbol_stack += [(symbol, inp)]
            state_stack += [arg]
            try:
                symbol, inp, pos = next(tokens)
            except StopIteration:
                symbol, inp = (None, None)
        elif action == 'reduce':
            subnodes = symbol_stack[-len(arg[1]):]
            symbol_stack = symbol_stack[:-len(arg[1])]
            filtered_subnodes = []
            for node in subnodes:
                if node[0] in ls['simplify'] or node[0][0] == '_':
                    filtered_subnodes += node[1:]
                elif node[0] in ls['aggregate']:
                    collect = []
                    for subsubnode in node[1:]:
                        if subsubnode[0] == node[0]:
                            collect += subsubnode[1:]
                        else:
                            collect += [subsubnode]                    
                    filtered_subnodes += [tuple([node[0]] + collect)]
                elif node[0] not in ls['remove']:
                    filtered_subnodes += [node]
            symbol_stack += [tuple([arg[0]] + filtered_subnodes)]
            state_stack = state_stack[:-len(arg[1])]
            new_state = goto_table[state_stack[-1]][arg[0]]
            state_stack += [new_state]
            if verbosity >= 3:
                logger("PARSE ACTION REDUCE: ", arg[0], "<-", arg[1], loglevel=1), " AND GOTO: ", new_state                        
        elif action == 'accept':
            break
        else:
            raise ParserInternalError("Parser internal error: unknown instruction in parse table:"+str(action))
    if len(symbol_stack) > 1:
        raise ParserInternalError("Parser internal error: unexpected state after completed parse:"+str([x[0] for x in symbol_stack]))                    

    if symbol_stack[0][0] in ls['simplify']:
        symbol_stack[0] = symbol_stack[0][1:]

    return symbol_stack[0]


def split_chars_strip_comments(source, comment_markers):
    """
    Helper function for the lexer that reads input and strips comments, while
    keeping track of absolute position in the file.

    Args:
      source (str): input string
      comment_markers (list of tuples): a list of entries (start_marker, end_marker) 
        that designate comments. A marker can be end-of-line or end with end-of-line, but 
        multiline comment separators are not allowed, i.e., no characters may follow 
        the end-of-line.        
    """
    # Speed things up if there are no comment markers
    if len(comment_markers) == 0:
        l = 0        
        for line in source.splitlines(True):
            l += 1
            p = 0
            for c in line:
                p += 1
                yield c, (l, p, line.rstrip('\n'))
        return

    comment_start_markers = [x[0] for x in comment_markers]
    comments_dict = dict([(x[0], x[1]) for x in comment_markers])
    comment_end_marker = None
    l = 0

    for line in source.splitlines(True):
        l += 1
        p = 0
        sline = line.rstrip('\n')
        # We are not in a comment, and no comment start marker is found, just keep going        
        if comment_end_marker is None and not any([line.find(x) != -1 for x in comment_start_markers]):
            for c in line:
                p += 1
                pos = (l, p, sline)
                yield c, pos
            continue
        # We are in a comment, and no comment end marker is found, dump whole line
        if comment_end_marker is not None and line.find(comment_end_marker) == -1:
            continue

        # Comments start and/or stop at this line, filter them out while keeping position info
        poslist = [(l, i, sline) for i in range(len(line))]
        while len(line) > 0:
            if comment_end_marker is not None:
                idx = line.find(comment_end_marker)
                if idx != -1:
                    line = line[idx+len(comment_end_marker):]
                    poslist = poslist[idx:]
                    comment_end_marker = None
                else:
                    line = ""
                    poslist = []
            idxs = [line.find(x) for x in comment_start_markers]
            filtered_idxs = [x for x in idxs if x != -1]
            if len(filtered_idxs) > 0:
                idx = min(filtered_idxs)
                comment_end_marker = comments_dict[comment_start_markers[idxs.index(idx)]]
                for i in range(idx):
                    yield line[i], poslist[i]
                line = line[idx:]
                poslist = poslist[idx:]
            # We are not in a comment now, and there is no more comment start marker
            else:
                for c, pos in zip(line, poslist):
                    yield c, pos
                line = ""
                poslist = []

def lexer(source, tokens, partial_tokens, literals, ignore, comment_markers=[], verbosity=0, logger=logger):
    """
    A generator that turn source into tokens.

    Args:
      source (str): input string
      tokens (dict): a dictonary that maps all tokens of the 
                     language on regular expressions that match them. 
      partial_tokens (dict): a dictionary that maps token names on
                     regular expressions for partial token matches.
                     This is used to allow finding longer matches if
                     there is intermediate length input that does not
                     match. E.g., to match 5.32e6 as a number instead
                     as as Number(5.32) + Identifier(e) + Number(6).
      literals (list): a list of single character strings that are
                     to be treated as literals.

    """
    seen_token, seen_token_pos, seen_token_len = None, None, None
    last_good_pos = (0, 0, "")
    last_good_pos_next = (0, 0, "")

    token_regexes = dict([(x, re.compile("("+tokens[x]+r')\Z')) for x in tokens.keys()])
    partial_token_regexes = dict([(x, re.compile("("+partial_tokens[x]+r')\Z')) for x in partial_tokens.keys()])
    all_token_regexes = set(tokens.keys()) | set(partial_tokens.keys())
    
    prescan = iter(split_chars_strip_comments(source, comment_markers))
    pushback = ""
    stack = ""
    c = None

    class MatchFound(Exception):
        pass
    
    while c != '' or len(pushback)>0 or seen_token is not None: 
        if len(pushback)>0:
            c = pushback[0]
            pushback = pushback[1:]
        else:
            try:
                c, pos = next(prescan)
            except StopIteration:
                c = ''
        stack += c
        
        if verbosity >= 5:
            logger("LEX INPUT:'"+c+"'")
            
        if last_good_pos_next is None:
            last_good_pos_next = pos

        if c != '':                
            try:
                for l in literals.union(ignore):
                    if stack == l:
                        seen_token, seen_token_pos, seen_token_len = l, pos, len(l)
                        last_good_pos, last_good_pos_next = pos, None
                        raise MatchFound()

                for t in all_token_regexes:
                    if t in token_regexes and token_regexes[t].match(stack) is not None:
                        seen_token, seen_token_pos, seen_token_len = t, pos, len(stack)
                        last_good_pos, last_good_pos_next = pos, None
                        raise MatchFound()
                    elif t in partial_token_regexes and partial_token_regexes[t].match(stack) is not None:
                        raise MatchFound()
            except MatchFound:
                continue
                
        if seen_token is not None:
            if seen_token not in ignore:
                if verbosity >= 4:
                    logger("LEX YIELD:", (seen_token, stack[:seen_token_len]))
                yield (seen_token, stack[:seen_token_len], seen_token_pos)
            pushback += stack[seen_token_len:]
            stack = ""
            seen_token, seen_token_pos, seen_token_len = None, None, None

    if stack != "":
        if last_good_pos is not None:
            if last_good_pos_next is not None:
                pos = last_good_pos_next
            else:
                pos = last_good_pos
        raise ParserSyntaxError("Parser lexing error: Unrecognized symbol starting at line: " +
                                str(pos[0])+", pos: "+str(pos[1])+":\n"+str(pos[2])+"\n"+(" "*(pos[1]-1))+"^",
                                "unrecognized symbol", pos[0], pos[1], pos[2])
    if verbosity >= 4:
        logger("LEX YIELD:", (None, None))
    yield (None, None, pos)


def build_ls(ebnf_grammar=None, tokens={}, partial_tokens={}, literals=None, precedence=[], ignore=" \t\n", simplify=[], aggregate=[], start=None, skip=[], remove=[], comment_markers=[], ls=None, verbosity=0, logger=logger):
    """
    Build a language specification from an ebnf grammar and some meta-info of the language.

    Args:
         ebnf_grammar (str): a string containing the ebnf describing the language.
         tokens (dict,optional): a dict of token names and the regexs that defines them, they
             are considered terminals in the parsing. (They may also be defined
             as production rules in the ebnf, but if so, those definitions are ignored.)
         partial_tokens (dict): a dictionary that maps token names on
                     regular expressions for partial token matches.
                     This is used to allow finding longer matches if
                     there is intermediate length input that does not
                     match. E.g., to match 5.32e6 as a number instead
                     as as Number(5.32) + Identifier(e) + Number(6).
         literals (list of str): a list of strings of 1 or more characters which 
             define literal symbols of the language (i.e, the tokenizer name the 
             tokens the same as the string), if not given, an attemt is made to 
             auto-extract them from the grammar. 
         precedence (list,optional): list of tuples of the format (associativity, symbol, ...),
             the order of this list defines the precedence of those symbols,
             later in the list = higher precedence. The associativity 
             can be 'left', 'right', or 'noassoc'.  
         ignore (str,optional): a string of characters, or a list of strings for symbols,
             which are withheld by the tokenizer. (This is commonly used to skip emitting 
             whitespace tokens, while still supprting whitespace inside tokens, 
             e.g., quoted strings.)
         simplify (list,optional): a list of symbol identifiers that are simplified away
             when the parse tree is generated. 
         aggregate (list,optional): a list of symbol identifiers that when consituting 
             consequtive nodes are 'flattened', removing the ambiguity of left or right 
             associativity.
         start (str,optional): the start (topmost) symbol of the grammar. A successful
             parsing means reducing all input into this symbol.      
         remove (list): list of symbols to just skip in the output parse tree 
             (useful to, e.g., skip uninteresting literals).
         skip (list): list of rules to completely ignore in the grammar.
             (useful to skip rules in a complete EBNF which reduces the tokens 
             into single characters entities, when one rather wants to handle
             those tokens by regex:es by passing the token argument)
         ls (dict): As an alternative to giving the above parameters, a dict can
             be given with the same attributes as the arguments defined above.
    """
    _ls = {
        'ebnf_grammar': ebnf_grammar,
        'tokens': tokens,
        'partial_tokens': partial_tokens,
        'precedence': precedence,
        'ignore': set(ignore),
        'simplify': simplify,
        'aggregate': aggregate,
        'start': start,
        'literals': literals,
        'skip': skip,
        'remove': remove,
        'comment_markers': comment_markers
    }

    if ls is not None:
        for entry in _ls:
            if entry not in ls:
                ls[entry] = _ls[entry]
        _ls = ls
    ls = _ls

    if not isinstance(ls['ignore'], set):
        ls['ignore'] = set(ls['ignore'])

    if 'bnf_grammar_ast' not in ls:
        if ('ebnf_grammar' not in ls) and ('ebnf_grammar_ast' not in ls):
            raise ParserGrammarError("Parser grammar error: build_ls needs at least one of ebnf_grammar, ebnf_grammar_ast, or bnf_grammar_ast.")
        if 'ebnf_grammar_ast' not in ls:
            # First bootstrap ls_ebnf if it also is missing its parse table
            if 'parse_table' not in ls_ebnf:
                build_ls(ls=ls_ebnf, verbosity=0, logger=logger)
            ls['ebnf_grammar_ast'] = parser(ls_ebnf, ls['ebnf_grammar'], verbosity=verbosity, logger=logger)
        ls['bnf_grammar_ast'] = _ebnf_grammar_to_bnf(ls['ebnf_grammar_ast'], ls['tokens'], ls['skip'])

    if ls['start'] is None:
        ls['start'] = ls['bnf_grammar_ast'][0][0]

    if ls['literals'] is None:
        ls['literals'] = set()
        ls['nonliterals'] = set()
        for rule in ls['bnf_grammar_ast']:
            if rule[0] not in ls['skip'] and rule[0] not in ls['tokens']:
                ls['nonliterals'].add(rule[0])
        for rule in ls['bnf_grammar_ast']:
            for term in rule[1]:
                if (term not in ls['nonliterals']):
                    ls['literals'].add(term)
        if verbosity >= 1:
            logger("Auto-extracted literals:", ls['literals'])
            logger("Auto-extracted non-literals:", ls['nonliterals'])

    if not isinstance(ls['literals'], set):
        ls['literals'] = set(ls['literals'])        

    if 'terminals' not in ls:
        ls['terminals'] = set(ls['tokens'].keys())         
        ls['terminals'].update(ls['literals'])
        # The 'nothing' (epsilon) symbol
        ls['terminals'].add(None)

    if verbosity >= 1:
        logger("Literals:", ls['literals'])
        logger("Terminals:", ls['terminals'])

    if 'rule_table' not in ls:
        ls['rule_table'] = _build_rule_table(ls['bnf_grammar_ast'], ls['terminals'], ls['skip'])
        if verbosity >= 1:
            logger("==== RULE TABLE")
            logger(ls['rule_table'], pretty=True)
            logger("====")

    if 'first_table' not in ls:
        ls['first_table'] = _build_first_table(ls['rule_table'], ls['terminals'])
        if verbosity >= 2:
            logger("==== FIRST TABLE")
            logger(ls['first_table'], pretty=True)
            logger("====")

    if 'parse_table' not in ls:
        ls['parse_table'] = _build_parse_tables(ls['rule_table'], ls['first_table'], ls['terminals'], ls['start'], ls['precedence'])
        if verbosity >= 3:
            logger("==== ACTION TABLE")
            logger(ls['parse_table']['action'], pretty=True)
            logger("====")
            logger("==== GOTO TABLE")
            logger(ls['parse_table']['goto'], pretty=True)
            logger("====")

    return ls


#### Helper functions    

def _build_rule_table(bnf_grammar_ast, terminals, skip):
    """
    Args:
      bnf_grammar_ast: grammar on bnf ast form produced by _ebnf_grammar_to_bnf
      terminals (list): list of terminals of the language

    Returns:
      A dict that maps every non-terminal to a list of 
      right hand sides of production rules from that non-terminal.
    """
    rule_table = {}    
    for rule in bnf_grammar_ast:
        lhs = rule[0]
        rhs = rule[1]
        if lhs in terminals or lhs in skip:
            continue        
        if lhs not in rule_table:
            rule_table[lhs] = []
        rule_table[lhs] += [rhs]        
    return rule_table


def _build_first_table(rule_table, terminals):
    """
    Args:
      rule_table: a rule table produced by _build_rule_table
      terminals (list): list of terminals of the language

    Returns:
      A dict of the FIRST(symbol) function in LR parsing.  It maps all
      symbols on a list of terminals that may be the very first thing
      seen in the input when matching that production rule.
    """
    first = {}
    lastcount = 0

    for terminal in terminals:
        first[terminal] = set([terminal])
    for symbol in rule_table:
        first[symbol] = set()

    while True:
        count = 0
        for symbol in rule_table:
            for rhs_alts in rule_table[symbol]:
                if len(rhs_alts) > 0:
                    first[symbol].update(first[rhs_alts[0]])
            count += len(first[symbol])
        if count == lastcount:
            break
        lastcount = count            
    return first


def _closure(items, rule_table, first_table, terminals):
    """
    Args:
      items: a list of LR "items" to get the CLOSURE set for.
      rule_table: a rule table produced by _build_rule_table
      first_table: a first table produced by _build_first_table 
      terminals (list): list of terminals of the language

    Returns:
      A set of all LR "items" that form the CLOSURE of the given items.
    """
    c = set(items)

    while True:
        new = set(c)
        for i in c:
            lookahead = i[2]
            pos = i[3]
            if len(i[1]) == pos:
                continue
            elif len(i[1]) == pos+1:
                symbol = i[1][pos]
                ts = [lookahead]
            else: 
                symbol = i[1][pos]
                if i[1][pos+1] not in first_table:
                    raise ParserGrammarError("Encountered EBNF symbol not in grammar or terminals: '"+str(i[1][pos+1])+"'")
                ts = first_table[i[1][pos+1]]

            if symbol not in terminals:
                productions = rule_table[symbol]
                for p in productions:
                    for t in ts:
                        new.add((symbol, p, t, 0))

        if new == c:
            break
        c = new

    return frozenset(c)


def _build_parse_tables(rule_table, first_table, terminals, start, precedence):
    """
    Args:
      rule_table: a rule table produced by _build_rule_tables
      first_table: a first table produced by _build_first_table 
      terminals (list): extra symbols apart from tokens and literals that are to
         be treated as terminals
      start (str,optional): the start (topmost) symbol of the grammar. A successful
         parsing means reducing all input into this symbol.      

    Returns:
        A parse_table dict with two tables 'action_table' and 'goto_table' 
        which encode a state machine that for every starting state S tells
        the LR state machine to either shift or reduce, and when doing so,
        the state the machine progresses to.
    """

    if start not in rule_table:
        raise ParserGrammarError("Parser grammar exception: start symbol '"+str(start)+"' is not in grammar.")

    start_item = (None, (start, None), False, 0)
    start_cl = _closure([start_item], rule_table, first_table, terminals)
    states_table = {}

    def _find_or_create_state(cl):
        if cl in states_table:
            return states_table[cl]
        else:
            state = len(states_table)+1
            states_table[cl] = state
            return state

    precedence_table = {}
    for i in range(len(precedence)):
        for pred in precedence[i][1:]:
            precedence_table[pred] = (i, precedence[i][0])

    def precedence_check(symbol, rhs):
        if symbol not in precedence_table:
            return 'unknown'
        found = 0
        for othersym in rhs:
            if othersym in precedence_table:
                found += 1
                foundsym = othersym
        if found == 1:
            if symbol == foundsym:
                if precedence_table[symbol][1] == 'left':
                    return 'reduce'
                elif precedence_table[symbol][1] == 'right':
                    return 'shift'
                else:
                    assert(precedence_table[symbol][1] == 'nonassoc')
                    return 'empty'                    
            else:
                if precedence_table[symbol][0] > precedence_table[foundsym][0]:
                    return 'shift'
                else:
                    return 'reduce'
        else:
            return 'unknown'

    action_table = {}
    goto_table = {}
    parse_table = {'action': action_table, 'goto': goto_table}
    warnings = {}

    todo = [start_cl]

    while len(todo) > 0:

        cl = todo.pop()
        state = _find_or_create_state(cl)

        if state in action_table and state in goto_table:
            continue

        itemdict = {}
        for item in cl:
            lhs = item[0]
            pos = item[3]
            rhs = item[1]            
            if len(rhs) > pos:
                arg = rhs[pos]
            else:
                arg = None
            if arg not in itemdict:
                itemdict[arg] = []
            itemdict[arg] += [item]

        action_table[state] = {}
        goto_table[state] = {}

        for symbol in itemdict:
            new_state_items = set()

            for item in itemdict[symbol]:
                lhs = item[0]
                pos = item[3]
                rhs = item[1]
                lookahead = item[2]        

                if len(rhs) > pos:
                    if symbol is None:
                        action_table[state][symbol] = ('accept', None)
                    else:                    
                        newitem = (lhs, rhs, lookahead, pos+1)
                        new_state_items.add(newitem)                    
                else:
                    if lookahead not in action_table[state]:
                        action_table[state][lookahead] = ('reduce', (lhs, rhs))
                    elif action_table[state][lookahead][0] == 'shift':
                        check = precedence_check(lookahead, rhs)
                        if check == 'reduce':
                            action_table[state][lookahead] = ('reduce', (lhs, rhs))
                        elif check == 'shift':
                            pass
                        elif check == 'empty':
                            del action_table[state][lookahead]
                        else:
                            assert(check == 'unknown')
                            if lookahead not in warnings:
                                warnings[lookahead] = []
                            if (lhs, rhs) not in warnings[lookahead]:
                                warnings[lookahead] = [(lhs, rhs)]
                    else:
                        assert(action_table[state][lookahead][0] == 'reduce')                        
                        raise ParserGrammarError("reduce/reduce conflict in state " +
                                                 str(state)+" for symbol:"+str(lookahead)+":\n"+str(action_table[state][lookahead][1])+" vs "+str((lhs, rhs)))

            if len(new_state_items) > 0:
                new_cl = _closure(new_state_items, rule_table, first_table, terminals)
                new_state = _find_or_create_state(new_cl)
                if symbol in terminals:
                    if symbol not in action_table[state]:
                        action_table[state][symbol] = ('shift', new_state)
                    elif action_table[state][symbol][0] == 'shift':
                        raise ParserGrammarError("shift/shift conflict in state "+str(state)+" for symbol:"+str(symbol))
                    else:                        
                        assert(action_table[state][symbol][0] == 'reduce')
                        rhs = action_table[state][symbol][1][1]
                        check = precedence_check(symbol, rhs)
                        if check == 'shift':
                            action_table[state][symbol] = ('shift', new_state)
                        elif check == 'reduce':
                            pass
                        elif check == 'empty':
                            del action_table[state][symbol]
                        else:
                            assert(check == 'unknown')
                            if symbol not in warnings:
                                warnings[symbol] = []
                            if action_table[state][symbol][1] not in warnings[symbol]:
                                warnings[symbol] += [action_table[state][symbol][1]]
                            action_table[state][symbol] = ('shift', new_state)
                else:
                    goto_table[state][symbol] = new_state
                todo.append(new_cl)                    

    for warning in warnings:
        logger("WARNING: shift/reduce conflict solved by shift for symbol:'"+str(warning)+"', involving rules:")
        logger(warnings[warning], pretty=True)

    return parse_table


def _ebnf_to_bnf_rhs(rhs, bnf_grammar_ast, lhs_name='', recursion=0):
    """
    Args:
      rhs: a right hand side of a EBNF grammar rule.
      bnf_grammar_ast: a list of BNF grammar rules that this function
          can add to when expanding repetition-type rules. 

    Returns:
        A list of BNF grammar rules that correspond to the EBNF rhs.

    Modifies:
        bnf_grammar_ast to include extra rules if needed.
    """
    # Just a literal
    if rhs[0] in ls_ebnf['literals']:
        return [(rhs,)]

    op = rhs[0]
    if op == 'identifier':
        return [(rhs[1],)]
    if op == 'special':
        special = (rhs[1][0].strip('?') + rhs[1][1:-1] + rhs[1][-1].strip('?')).strip()
        rule_names = [x[0] for x in bnf_grammar_ast]
        i = 1
        while (('_special_'+lhs_name+"_"+str(i)) in rule_names) or (('?_special'+str(i)) in rule_names):
            i += 1
        repstr = '_special_'+lhs_name+"_"+str(i)
        bnf_grammar_ast += [('?'+repstr, (special,))]
        return [(repstr,)]
    elif op == 'terminal':
        return [(ebnf_unqote(rhs[1][1:-1]),)]

    elif op == 'Concatenation':
        new_rhs = []
        for part in rhs[1:]:
            new_rhs += [_ebnf_to_bnf_rhs(part, bnf_grammar_ast, lhs_name=lhs_name, recursion=recursion+1)]
        concat = [tuple(z for y in x for z in y if z is not None) for x in itertools.product(*new_rhs)]
        return concat

    elif op == 'Alteration':
        new_rhs = []
        for part in rhs[1:]:
            new_rhs += _ebnf_to_bnf_rhs(part, bnf_grammar_ast, lhs_name=lhs_name, recursion=recursion+1)
        return new_rhs

    elif op == 'Optional':
        new_rhs = _ebnf_to_bnf_rhs(rhs[1], bnf_grammar_ast, lhs_name=lhs_name, recursion=recursion+1)
        new_rhs += [()]
        return new_rhs

    elif op == 'Grouping':
        return _ebnf_to_bnf_rhs(rhs[1], bnf_grammar_ast, lhs_name=lhs_name, recursion=recursion+1)

    elif op == 'Repetition':
        rule_names = [x[0] for x in bnf_grammar_ast]
        i = 1
        while ('_repeat_'+lhs_name+'_'+str(i)) in rule_names:
            i += 1
        repstr = '_repeat_'+lhs_name+'_'+str(i)
        new_rhs = _ebnf_to_bnf_rhs(rhs[1], bnf_grammar_ast, lhs_name=lhs_name, recursion=recursion+1)
        for nr in new_rhs:
            bnf_grammar_ast += [tuple([repstr] + [tuple(list(nr) + [repstr])])]
            bnf_grammar_ast += [tuple([repstr] + [tuple(list(nr))])]
        return [(repstr,), ()]
    else:
        raise ParserGrammarError("Parser grammar error: unrecognized symbol in grammar ast:"+str(op))


def _ebnf_grammar_to_bnf(ebnf_grammar_ast, tokens, skip):
    """
    Converts/expands an EBNF ast grammar into a BNF ast grammar.

    Args:
      ebnf_grammar_ast: an ast representation of the EBNF grammar
          as produced by parser when ebnf_ls is used for the 
          language specification.
      tokens (dict): a dictionary defining tokens of the language.
      skip (list): skip the rules for these symbols.

    Returns:
        An ast BNF representation of the grammar.
    """
    bnf_grammar = []

    assert(ebnf_grammar_ast[0] == 'Grammar')
    for rule in ebnf_grammar_ast[1:]:
        assert(rule[0] == 'Rule')
        lhs = rule[1]
        assert(lhs[0] == 'identifier')
        symbol = lhs[1]
        if symbol in tokens or symbol in skip:
            continue        
        rhs = rule[2]
        new_rhs_list = _ebnf_to_bnf_rhs(rhs, bnf_grammar, lhs_name=symbol)
        for rhs in new_rhs_list:
            bnf_grammar += [(symbol, rhs)]

    tokens.update([(x[0][1:], x[1][0]) for x in bnf_grammar if x[0].startswith("?")])

    bnf_grammar = tuple(x for x in bnf_grammar if not x[0].startswith("?"))

    return bnf_grammar

def ebnf_unqote(s):
    s = s.replace(r'\t','\t')
    s = s.replace(r'\n','\n')
    s = s.replace(r'\r','\r')
    # Skip support for general escapes so that '\' does what one expects
    #s = '\\'.join([x.replace('\\','') for x in s.split('\\\\')])
    return s
    
# If this python file is run as a program, 
# Parse the EBNF description of EBNF using the
# language specification for EBNF and check
# that it returns the same as is already provided.

if __name__ == "__main__":

    result = parser(ls_ebnf, ls_ebnf['ebnf_grammar'])

    pprint.pprint(result)    

    assert(result == ls_ebnf['ebnf_grammar_ast'])



