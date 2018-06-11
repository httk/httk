# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2018 Rickard Armiento
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

import os, sys

import httk
from httk import cout, cerr, cli_modules


help_text = """
usage: httk [--version] [--help] [-C <path>] [-c name=value]
            [--exec-path[=<path>]] [--html-path] [--man-path] [--info-path]
            [-p | --paginate | --no-pager] 
            [--httk-dir=<path>] <command> [<args>]

These are common httk commands used in various situations:

start a project, configuration (see also: httk help project)
   init       Create an empty httk project or reinitialize an existing one

work on the current project (see also: httk help work)
   add        Add a task file or dir to the index of tasks being worked on 
   mv         Move or rename a task file, a directory, or a symlink
   rm         Remove a task file from the working tree and from the index

examine the history and state (see also: httk help info)
   show       Show various types of objects
   status     Show the working tree status
   log        Show log of actions

send tasks to remote machines (see also: httk help remote)
   remote     add and configure access to remote computers
   pull       Fetch from and integrate with another repository or a local branch
   push       Update remote refs along with associated objects
"""

help_footer = """
'httk help -a' and 'httk help -g' list available subcommands and some
concept guides. See 'httk help <command>' or 'httk help <concept>'
to read about a specific subcommand or concept.
""".strip()

def main():
    cout("httk v" + httk.version + " (" + httk.version_date + "), " + httk.copyright_note)
    cout("")
    cout("------------------------------------------------------------------------------------")
    cout("WARNING: the httk cli tool is presently work in progress in preparation for httk v2.")
    cout("         Many functions are not available or does not work as documented.")
    cout("         For now, you should be using the httk-* scripts instead.")
    cout("------------------------------------------------------------------------------------")
    
    argv = sys.argv
    
    args = lambda: None # dict-like object using attributes

    args.commands = []
    args.cwd = os.getcwd()
    args.configopts = {}
    no_options_mode = False
    
    argi = iter(argv)
    argi.next()
    for arg in argi:

        if (not arg.startswith("-") or no_options_mode):
            args.commands += [arg]

        elif not no_options_mode:

            if arg == "--":
                no_options_mode = True

            elif arg == '--version':
                args.commands = ["version"]

            elif arg == '--paginate':
                args.paginate = True

            elif arg == "-C":                
                args.cwd = argi.next()

            elif arg == '-c':
                key,val = argi.next().partition('=')
                args.configopts[key] = val 

            elif arg == '-p':
                args.paginate = True

            elif arg == '--no-pager':
                args.paginate = False

            elif arg == "--httk-dir":                
                args.httk_dir = argi.next()
                
            elif arg == "--help" or arg == "-h":
                args.commands = ["help"] + args.commands

    # Move 'help' to the last position
    if "help" in args.commands:
        args.commands += [args.commands.pop(args.commands.index("help"))]

    if len(args.commands) == 0:
        args.commands = ['help']
        
############## HELP ####################                
    if args.commands[0] == "help":
        cout(help_text)
        for mod in cli_modules.values():
            cout("")
            module = __import__(mod, fromlist=[''])
            cout(module.help_text)
        cout("")
        cout(help_footer)
        httk.dont_print_citations_at_exit()
        exit(0)

############## MODULES ###############

    elif args.commands[0] in cli_modules:
        module = __import__(cli_modules[args.commands[0]], fromlist=[''])
        module.main(args.commands[1:],args)
        exit(0)
        
######################################

    else:
        context = httk.config.get("cli", "context")
        if context is not None:
            if context in cli_modules:
                module = __import__(cli_modules[context], fromlist=[''])
                module.main(args.commands,args)
                exit(0)
                    
        cerr("Unknown httk command:",args.commands[0])
        exit(1)
        
    cout("Nothing to do.")
    httk.dont_print_citations_at_exit()



        
