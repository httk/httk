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
import os, sys, tempfile, glob, shutil

import httk

from httk.core.basic import mkdir_p
from httk.core.template import apply_templates


def create_batch_task(dirpath, template='t:vasp/batch/vasp-relax-formenrg', args=None, project='noproject', assignment='unassigned',
                      instantiate_name='ht.instantiate.py', overwrite=False, overwrite_head_dir=True, remove_instantiate=True, name=None, priority=3):
    global instantiate_args, instantiate_to_path

    if args is None:
        args = {}

    if template.startswith('t:'):
        template = os.path.join(httk.httk_root, 'Execution', 'tasks-templates', template[2:])

    instantiate_args = args
    instantiate_to_path = template

    if overwrite_head_dir:
        mkdir_p(os.path.join(dirpath))
    else:
        os.mkdir(dirpath)

    taskspath = dirpath
    # taskspath = os.path.join(dirpath,project)
    # taskspath = os.path.join(dirpath,'ht.waiting',project)
    mkdir_p(taskspath)

    taskpath = tempfile.mkdtemp(prefix='ht.tmp.', dir=taskspath)
    basename = os.path.basename(taskpath)
    tmpstr = basename[7:]
    apply_templates(template, taskpath, envglobals=args, mkdir=False)

    old_path = os.getcwd()
    old_sys_argv = sys.argv

    # Saftey check
    if instantiate_name is None or instantiate_name == '' or not isinstance(instantiate_name, str) or not instantiate_name:
        raise Exception("taskmgr.create_batch_task: empty or weird instantiate_name:" + str(instantiate_name))

    try:
        os.chdir(taskpath)
        # try:
        print "INSTANTIATE_NAME", taskpath
        exec(compile(open(instantiate_name).read(), instantiate_name, 'exec'), args, {})
        # except:
        #    with open(instantiate_name) as f:
        #        code = compile(f.read(), instantiate_name, 'exec')
        #        exec(code,args,{})
        os.unlink(instantiate_name)

    # mkdir_p(os.path.join(dirpath,"ht.tmp.waiting",project))
    finally:
        os.chdir(old_path)
        sys.argv = old_sys_argv

    if name is None:
        if 'finalname' not in args:
            name = tmpstr
        else:
            name = args['finalname']

    if not overwrite:
        check = glob.glob(os.path.join(taskspath, 'ht.task.*.' + name + '.*'))
        if len(check) > 0:
            shutil.rmtree(os.path.join(taskspath, 'ht.tmp.' + tmpstr))
            raise Exception("task.taskmgr.create_batch_task: Task already exists:" + str(name))

    full_finalname = "ht.task." + assignment + "." + name + ".start.0.unclaimed." + str(priority) + ".waitstart"
    finalpath = os.path.join(taskspath, full_finalname)

    os.rename(taskpath, finalpath)

    return finalpath
