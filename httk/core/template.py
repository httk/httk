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
import shlex, StringIO, os, sys, shutil
from string import Template
from .basic import mkdir_p


def apply_template(template, output, envglobals=None, envlocals=None):
    """
    Simple Python template engine. 

    The file 'template' is turned into a new file 'output' replacing the following:
    $name -> the value of the variable 'name' in the scope provided by locals and globals. 
    $(python statement) -> result of evaluating the python statment.
    ${some python code} -> text on stdout from running that python code.

    Note: it is safe for the code inside the template 
    to load the file it eventually will replace.
    """

    if envlocals is None:
        envlocals = {}
    else:
        envlocals = envlocals.copy()

    if envglobals is None:
        envglobals = {}
    else:
        envglobals = envglobals.copy()

    # Read template and substitute $name entries
    template_file = open(template, 'r')
    ## shlex does not work with unicode, hence the .encode('ascii') to make sure the result is not unicode
    result_step1 = Template(Template(template_file.read()).safe_substitute(envlocals)).safe_substitute(envglobals).encode('ascii')
    template_file.close()

    # Substitute $(some python code) entries
    result_step2 = ''
    lexer = shlex.shlex(result_step1)
    lexer.whitespace = ''
    eval_nesting = 0
    exec_nesting = 0
    for token in lexer:
        if(eval_nesting == 0 and exec_nesting == 0):
            if(token == '\\'):
                token += lexer.get_token()
            if(token == '$'):
                token += lexer.get_token()
            if(token == '$('):  # eval command
                eval_nesting = 1
                command = ''
                continue
            if(token == '${'):  # exec command
                exec_nesting = 1
                command = ''
                continue
            if(token == '\\$'):  # escaped $ -> send $ to output
                token = '$'
            result_step2 += token

        elif(exec_nesting != 0):
            if(token == '{'):
                exec_nesting += 1
            if(token == '}'):
                exec_nesting -= 1
            if(exec_nesting == 0):
                sys.stdout = StringIO.StringIO()
                try:
                    exec(command, envglobals, envlocals) 
                except:
                    print "Failed to execute:"+command
                    raise 
                result_step2 += sys.stdout.getvalue()
                if result_step2.endswith('\n'):
                    result_step2 = result_step2[:-1]
                sys.stdout = sys.__stdout__                
                continue
            command += token

        elif(eval_nesting != 0):
            if(token == '('):
                eval_nesting += 1
            if(token == ')'):
                eval_nesting -= 1
            if(eval_nesting == 0):
                try:
                    result_step2 += str(eval(command, envglobals, envlocals)) 
                except:
                    print "Failed to eval:"+command
                    raise 
                continue
            command += token            

    # Write output, but first remove file if it already exists, this is done explicitly
    # to handle symlinks in a sane way; i.e., they are replaced by the instantiated template,
    # and the file the symlink is pointing at is NOT changed.
    if os.path.exists(output):
        os.remove(output)    
    output_file = open(output, 'w')
    output_file.write(result_step2)
    output_file.close()


def apply_templates(inputpath, outpath, template_suffixes="template", envglobals=None, envlocals=None, mkdir=True):
    """
    Apply one or a series of templates throughout directory tree.

    template_suffixes: string or list of strings that are the suffixes of templates that are to be applied.
    name: subdirectory in which to apply the template, defaults to last subrun created, or '.' if no subrun have been created.
    """

    if not os.path.exists(inputpath):
        raise Exception("apply_templates: template does not exist")

    if mkdir:
        os.mkdir(outpath)

    # Make sure template_suffixies is a list so we can iterate over it
    if isinstance(template_suffixes, str):
        template_suffixes = [template_suffixes]

    # Loop over all files in the directory tree and run all templates that are found
    #main_path = os.getcwd()    
    #print "Looping over",inputpath
    
    for root, dirs, files in os.walk(inputpath):
        for filename in files:
            for suffix in template_suffixes:
                rp = os.path.relpath(root, inputpath)
                if rp == '.':
                    rp = ''
                else:
                    mkdir_p(os.path.join(outpath, rp))
                if(filename.endswith("."+suffix)):
                    newname = filename[:-len("."+suffix)]
                    #os.chdir(os.path.join("./",outpath,root))
                    #mkdir_p(os.path.dirname(newname))
                    #apply_template("./"+filename,"./"+newname,locals,envglobals=None,envlocals=None)        
                    #os.chdir(path)
                    apply_template(os.path.join(root, filename), os.path.join(outpath, rp, newname), envglobals=envglobals, envlocals=envlocals)      
                    shutil.copymode(os.path.join(root, filename), os.path.join(outpath, rp, newname))
                    #print "Instanceiate",os.path.join(root,filename),os.path.join(outpath,rp,newname)
                else:
                    #print "Copy",shutil.copyfile(os.path.join(root,filename),os.path.join(outpath,rp,filename)) 
                    shutil.copy(os.path.join(root, filename), os.path.join(outpath, rp, filename)) 

    #os.chdir(main_path)
