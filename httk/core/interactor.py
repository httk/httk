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

import argparse, re

class str_constraints(object):
    def __init__(self,regex, description=None):
        self.regex = regex
        self.description = None
        
    def validate(self,s):
        return re.match(self.regex,s)

class int_constraints(object):
    def __init__(self, description=None):
        self.constraint = None
        self.description = None
        
    def validate(self,s):
        return True    

str_constraints_id = str_constraints('^[a-z][a-z0-9]*$',"Lower case letters, 0-9, no space, must start with a letter")
str_contsraints_any = str_constraints('^.*$',"Free text input")
int_constraints_any = int_constraints("Any integer")

class console(object):
    def __init__(self,verbosity=2):
        self.verbosity = verbosity
    
    def request_str(self,msg,constraints=str_contsraints_any, arg=None):
        if arg != None:
            if constraints.validate(arg):
                return arg
            else:
                raise Exception("httk.interactor.request_int: Not a valid input.")
        while True:
            if constraints.description and self.verbosity >= 2:
                msg = (msg+" ("+constraints.description+"): ")
            else:
                msg = (msg+": ")
            if self.verbosity >= 1:
                result = raw_input(msg)
            else:
                result = raw_input()
            if constraints.validate(result):
                return result
            raise Exception("Could not parse entry")
            
    def request_int(self,msg,constraints=int_constraints_any, arg=None):
        if arg != None:
            if constraints.validate(arg):
                return arg
            else:
                raise Exception("httk.interactor.request_int: Not valid input.")
            
        while True:
            resultstr = self.request_str(self,msg)
            try:
                result = int(resultstr)
                if constraints.validate(result):
                    return result
            except:
                raise Exception("Console: Could not parse entry")
        
    def msg(self,*msg,**keys):
        if ('verbosity' in keys and keys['verbosity'] <= self.verbosity) or ('verbosity' not in keys and 2 <= self.verbosity):
            for m in msg:
                print m,

class console_noninteractive(console):
    def __init__(self,verbosity=2):
        console.__init__(self,verbosity)
    
    def request_str(self,msg,constraints=str_contsraints_any):
        raise Exception("Input needed during a noninteractive session")

    def request_int(self,msg,constraints=int_constraints_any):
        raise Exception("Input needed during a noninteractive session")

def create(args):
    if args.veryquiet:
        verbosity = 0
    elif args.quiet:
        verbosity = 1
    elif args.verbose == None:
        verbosity = 2
    else:
        verbosity = args.verbose
    
    if args.interaction == 'console':
        if args.noninteractive:
            return console_noninteractive(verbosity=verbosity)
        else:
            return console(verbosity=verbosity)
    raise Exception("httk.core.interactor: Unknown user interaction form requested.")

class verbosity_action(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        # print 'values: {v!r}'.format(v=values)
        if values==None:
            values='1'
        try:
            values=int(values)
        except ValueError:
            values=values.count('v')+1
        setattr(args, self.dest, values)
    
def setup_argparse(parser):
    parser.add_argument('-n', dest='noninteractive', action='store_true', help='Never ask for user input')
    parser.add_argument('-c', dest='interaction', action='store_const', help='User input on console',const='console', default='console')
    parser.add_argument('-v', nargs='?', action=verbosity_action, dest='verbose')
    parser.add_argument('-q', dest='quiet', action='store_true', help='no non-essential output')
    parser.add_argument('-Q', dest='veryquiet', action='store_true', help='no ouput what so ever, except errors')

    